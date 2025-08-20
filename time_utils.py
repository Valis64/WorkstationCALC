"""Utilities for working with business hours.

The module previously exposed ``BUSINESS_START`` and ``BUSINESS_END`` as
mutable module-level globals.  Directly changing those values from other
modules made it easy to accidentally mutate them without a consistent API.

To centralize configuration, business hours are now stored in a small
``BusinessHoursConfig`` object.  Callers should use the provided setter and
getter helpers to adjust or read the configured hours.
"""

from datetime import datetime, timedelta, time
from dataclasses import dataclass
import logging


@dataclass
class BusinessHoursConfig:
    """Runtime configuration for business hours.

    ``start`` and ``end`` default to 07:00 and 22:00 respectively but can be
    updated via :func:`set_business_hours`.
    """

    start: time = time(7, 0)
    end: time = time(22, 0)


_CONFIG = BusinessHoursConfig()

logger = logging.getLogger(__name__)


def get_business_start() -> time:
    """Return the configured start of the business day."""

    return _CONFIG.start


def get_business_end() -> time:
    """Return the configured end of the business day."""

    return _CONFIG.end


def set_business_hours(start: time, end: time) -> None:
    """Set the business day start and end times.

    Parameters
    ----------
    start:
        The time at which the business day begins.
    end:
        The time at which the business day ends.  ``end`` must be strictly
        later than ``start``.
    """

    if start >= end:
        raise ValueError("business start must be before business end")
    _CONFIG.start = start
    _CONFIG.end = end


def _next_business_start(dt: datetime) -> datetime:
    """Return the next datetime aligned with the configured start of day.

    Steps:
    1. Add one calendar day to ``dt``.
    2. Replace the time portion with the configured business start.
    3. Return the normalized datetime.

    The helper itself does not skip weekends; callers should continue
    invoking it until a weekday is reached.
    """
    next_day = dt + timedelta(days=1)
    start = get_business_start()
    return next_day.replace(
        hour=start.hour, minute=start.minute, second=0, microsecond=0
    )


def business_hours_breakdown(start: datetime, end: datetime):
    """Return a list of business-hour segments between ``start`` and ``end``.

    Steps:
    1. Iterate from ``start`` until ``end``.
    2. Skip Saturdays and Sundays by jumping to the next business start.
    3. For each weekday, compute the configured ``day_start`` and ``day_end``
       (defaults 07:00–22:00).
    4. Snap the current time to ``day_start`` if it falls earlier.
    5. If the current time is past ``day_end``, move to the next day.
    6. Record a segment from the current time to the earlier of ``day_end`` or ``end``.
    7. Advance to the next day's start and repeat.

    Example:
        >>> from datetime import datetime
        >>> business_hours_breakdown(
        ...     datetime(2024, 1, 5, 16, 0), datetime(2024, 1, 8, 10, 0)
        ... )
        [(datetime(2024, 1, 5, 16, 0), datetime(2024, 1, 5, 22, 0)),
         (datetime(2024, 1, 8, 7, 0), datetime(2024, 1, 8, 10, 0))]

    Weekends are skipped entirely, days are segmented by business start and
    end, and the return value lists each contiguous span that contributes
    to business time.
    """

    segments = []
    current = start
    while current < end:
        # Skip weekends entirely
        if current.weekday() >= 5:
            current = _next_business_start(current)
            continue

        start_time = get_business_start()
        end_time = get_business_end()
        day_start = current.replace(
            hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0
        )
        day_end = current.replace(
            hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0
        )

        if current < day_start:
            current = day_start
        if current >= day_end:
            current = _next_business_start(current)
            continue

        segment_end = min(day_end, end)
        segments.append((current, segment_end))
        current = _next_business_start(current)

    return segments


def business_hours_delta(start: datetime, end: datetime) -> timedelta:
    """Return the total business time between ``start`` and ``end``.

    Steps:
    1. If ``start`` is not before ``end``, return ``timedelta(0)``.
    2. Use :func:`business_hours_breakdown` to obtain all weekday segments.
    3. Sum the duration of each segment to compute the total.

    Only hours between the configured business start/end on weekdays
    contribute to the total because weekend periods are skipped by the
    breakdown.
    """

    if start >= end:
        return timedelta(0)
    total = timedelta()
    for seg_start, seg_end in business_hours_breakdown(start, end):
        total += seg_end - seg_start
    return total


def hours_breakdown(start: datetime, end: datetime) -> tuple[timedelta, timedelta]:
    """Return business and after-hours durations between ``start`` and ``end``.

    The weekend and holiday behavior matches the :func:`business_hours_delta`
    and :func:`business_hours_breakdown` helpers.
    """

    if start >= end:
        return timedelta(0), timedelta(0)

    total = end - start
    business = business_hours_delta(start, end)
    after_hours = total - business
    return business, after_hours


def calculate_hours(start: datetime | str | None, end: datetime | str | None) -> float:
    """Return business hours between ``start`` and ``end``.

    Parameters
    ----------
    start, end:
        ``datetime`` objects or ISO-8601 formatted strings (seconds optional).
        Legacy ``"%Y-%m-%d %H:%M"`` strings remain supported.  If ``start`` or
        ``end`` is missing, the function simply returns ``0.0``. If parsing
        fails, the time zones differ, or ``end`` precedes ``start``, the function
        logs an error and returns ``0.0``.

    Returns
    -------
    float
        Total business hours between ``start`` and ``end``, rounded to two
        decimal places.
    """

    if not start or not end:
        return 0.0

    def _to_datetime(value: datetime | str) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%d %H:%M")
        raise TypeError("value must be datetime or ISO-8601 string")

    try:
        start_dt = _to_datetime(start)
        end_dt = _to_datetime(end)
        if (
            start_dt.tzinfo is not None
            and end_dt.tzinfo is not None
            and start_dt.tzinfo != end_dt.tzinfo
        ):
            logger.error("start and end time zones differ")
            return 0.0
        if end_dt < start_dt:
            raise ValueError("end before start")
        delta = business_hours_delta(start_dt, end_dt)
        hours = delta.total_seconds() / 3600.0
        return round(hours + 1e-9, 2)
    except Exception:
        logger.exception("Error calculating hours")
        return 0.0
