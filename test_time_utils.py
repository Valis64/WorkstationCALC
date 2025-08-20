import unittest
from datetime import datetime, time, timedelta

from time_utils import business_hours_delta, business_hours_breakdown, calculate_hours, hours_breakdown
import time_utils


class TimeUtilsTests(unittest.TestCase):
    def test_business_hours_skip_weekend(self):
        start = datetime(2024, 1, 5, 16, 0)  # Friday 4pm
        end = datetime(2024, 1, 8, 10, 0)  # Monday 10am
        delta = business_hours_delta(start, end)
        self.assertEqual(delta.total_seconds() / 3600, 9.0)  # 9 hours within business hours

        segments = business_hours_breakdown(start, end)
        expected = [
            (datetime(2024, 1, 5, 16, 0), datetime(2024, 1, 5, 22, 0)),
            (datetime(2024, 1, 8, 7, 0), datetime(2024, 1, 8, 10, 0)),
        ]
        self.assertEqual(segments, expected)

    def test_hours_breakdown(self):
        """Should split total time into business and after-hours portions."""
        start = datetime(2024, 1, 5, 16, 0)
        end = datetime(2024, 1, 8, 10, 0)
        business, after_hours = hours_breakdown(start, end)
        self.assertEqual(business, timedelta(hours=9))
        self.assertEqual(after_hours, timedelta(hours=57))

    def test_hours_breakdown_crosses_midnight(self):
        """Late evening to next morning should split business and after-hours."""
        start = datetime(2024, 1, 8, 21, 0)  # Monday 9pm
        end = datetime(2024, 1, 9, 8, 0)  # Tuesday 8am
        business, after_hours = hours_breakdown(start, end)
        self.assertEqual(business, timedelta(hours=2))
        self.assertEqual(after_hours, timedelta(hours=9))

    def test_hours_breakdown_full_weekend(self):
        """Entire weekend should count as after hours only."""
        start = datetime(2024, 1, 6, 0, 0)  # Saturday
        end = datetime(2024, 1, 8, 0, 0)  # Monday midnight
        business, after_hours = hours_breakdown(start, end)
        self.assertEqual(business, timedelta(0))
        self.assertEqual(after_hours, timedelta(hours=48))

    def test_business_hours_same_day_partial_window(self):
        """Hours on a single day honor partial start/end times."""
        start = datetime(2024, 1, 8, 9, 15)
        end = datetime(2024, 1, 8, 11, 45)
        delta = business_hours_delta(start, end)
        self.assertAlmostEqual(delta.total_seconds() / 3600, 2.5)

    def test_business_hours_multi_day_weekdays(self):
        """Spans across weekdays should accumulate each day within hours."""
        start = datetime(2024, 1, 8, 15, 0)  # Monday
        end = datetime(2024, 1, 9, 10, 0)  # Tuesday
        delta = business_hours_delta(start, end)
        self.assertAlmostEqual(delta.total_seconds() / 3600, 10.0)

    def test_custom_business_hours(self):
        """Setting custom hours should influence calculations."""
        try:
            time_utils.set_business_hours(time(9, 0), time(17, 0))
            start = datetime(2024, 1, 5, 8, 30)
            end = datetime(2024, 1, 5, 9, 30)
            delta = business_hours_delta(start, end)
            self.assertEqual(delta, timedelta(minutes=30))
        finally:
            time_utils.set_business_hours(time(7, 0), time(22, 0))

    def test_calculate_hours_iso_strings(self):
        """ISO strings with seconds should parse and use business hours."""
        start = "2024-01-05T16:00:00"
        end = "2024-01-08T10:00:00"
        hours = calculate_hours(start, end)
        self.assertAlmostEqual(hours, 9.0)

    def test_calculate_hours_outside_business_hours_with_seconds(self):
        """Times outside configured hours across days return 0."""
        start = "2025-08-15 22:01:00"  # Friday after hours
        end = "2025-08-16 06:59:00"  # Saturday before hours
        self.assertEqual(calculate_hours(start, end), 0.0)

    def test_calculate_hours_end_before_start(self):
        """Reversed start/end should log an error and return 0."""
        with self.assertLogs("time_utils", level="ERROR"):
            self.assertEqual(
                calculate_hours("2025-01-01 10:00:00", "2025-01-01 09:00:00"),
                0.0,
            )

    def test_calculate_hours_respects_business_hours(self):
        """Changing business hours should affect calculated duration."""
        try:
            time_utils.set_business_hours(time(9, 0), time(17, 0))
            self.assertEqual(
                calculate_hours("2024-01-05 08:00:00", "2024-01-05 10:00:00"),
                1.0,
            )
        finally:
            time_utils.set_business_hours(time(7, 0), time(22, 0))

    def test_calculate_hours_exact_business_bounds(self):
        """Start and end at the exact business boundaries count the full day."""
        self.assertEqual(
            calculate_hours("2024-01-08 07:00", "2024-01-08 22:00"),
            15.0,
        )

    def test_calculate_hours_errors(self):
        """Invalid inputs or reversed times should log and return 0."""
        with self.assertLogs("time_utils", level="ERROR"):
            self.assertEqual(calculate_hours("bad", "2024-01-01T10:00"), 0.0)
        with self.assertLogs("time_utils", level="ERROR"):
            self.assertEqual(
                calculate_hours(
                    datetime(2024, 1, 2, 10, 0), datetime(2024, 1, 2, 9, 0)
                ),
                0.0,
            )

    def test_calculate_hours_mismatched_timezones(self):
        """Different non-null time zones should log an error and return 0."""
        start = "2024-01-01T10:00:00+00:00"
        end = "2024-01-01T11:00:00+01:00"
        with self.assertLogs("time_utils", level="ERROR"):
            self.assertEqual(calculate_hours(start, end), 0.0)

    def test_calculate_hours_provided_example(self):
        """Given example should match expected rounded hours."""
        self.assertAlmostEqual(
            calculate_hours("2025-08-14 15:47", "2025-08-15 16:08"),
            15.35,
        )


if __name__ == "__main__":
    unittest.main()
