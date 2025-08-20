import sqlite3
from threading import Lock
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

# Type alias for step entries: (step name, timestamp)
Step = Tuple[str, datetime]


def connect_db(path: str | Path):
    """Connect to the SQLite database at *path*.

    A small schema is created if the file is new.  The function returns the
    connection object along with a threading lock that callers can use to
    serialise writes from multiple threads.
    """
    conn = sqlite3.connect(str(path), check_same_thread=False)
    cur = conn.cursor()
    # Table storing each step an order passes through.  The combination of
    # order number and step name is unique so that re-processing the same
    # information does not raise an error.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS steps (
            order_number TEXT NOT NULL,
            customer TEXT NOT NULL,
            step TEXT NOT NULL,
            ts TEXT NOT NULL,
            UNIQUE(order_number, step)
        )
        """
    )
    # Minimal table used by the application to record when the print file for
    # an order is first required.  The primary key avoids duplicate entries.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS print_file (
            order_number TEXT PRIMARY KEY,
            started_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn, Lock()


def log_order(conn: sqlite3.Connection, lock: Lock, order_number: str, customer: str, steps: Iterable[Step]) -> bool:
    """Insert *steps* for *order_number* into the database.

    Returns ``True`` if at least one new step was recorded, ``False`` if all
    steps were already present.  The function is safe to call repeatedly with
    the same data; duplicate entries are ignored rather than raising an
    ``IntegrityError``.
    """
    new_step = False
    with lock:
        for step_name, ts in steps:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO steps(order_number, customer, step, ts)
                VALUES (?, ?, ?, ?)
                """,
                (order_number, customer, step_name, ts.isoformat()),
            )
            if cur.rowcount:
                new_step = True
        conn.commit()
    return new_step


def record_print_file_start(conn: sqlite3.Connection, lock: Lock, order_number: str) -> None:
    """Record that work on ``order_number``'s print file has started."""
    with lock:
        conn.execute(
            """
            INSERT OR REPLACE INTO print_file(order_number, started_at)
            VALUES (?, ?)
            """,
            (order_number, datetime.utcnow().isoformat()),
        )
        conn.commit()
