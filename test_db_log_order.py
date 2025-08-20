from datetime import datetime

from data import db


def test_log_order_returns_bool(tmp_path):
    db_path = tmp_path / "orders.db"
    conn, lock = db.connect_db(db_path)

    steps = [("Print File", datetime.now())]

    # First insert should return True indicating a new order
    assert db.log_order(conn, lock, "100", "ACME", steps) is True

    # Second insert of the same order should return False
    assert db.log_order(conn, lock, "100", "ACME", steps) is False
