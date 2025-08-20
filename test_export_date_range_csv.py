import csv
from datetime import datetime, time
from unittest.mock import patch

import time_utils
from ui.order_app import OrderScraperApp


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_export_date_range_csv_recomputes_hours(tmp_path):
    # Ensure default business hours
    time_utils.set_business_hours(time(7, 0), time(22, 0))

    app = OrderScraperApp.__new__(OrderScraperApp)
    app.date_range_rows = [
        {
            "order": "1001",
            "company": "Acme",
            "hours": 0.0,
            "status": "Done",
            "workstations": [
                {
                    "workstation": "Cut",
                    "start": "2024-01-08 06:30",
                    "end": "2024-01-08 07:30",
                    "hours": 0.0,
                }
            ],
        }
    ]
    app.export_path_var = DummyVar(str(tmp_path))
    app.range_start_var = DummyVar("")
    app.range_end_var = DummyVar("")
    app.get_date_range = lambda *args, **kwargs: (
        datetime(2024, 1, 8),
        datetime(2024, 1, 9),
    )

    with patch("ui.order_app.messagebox.showerror"), patch(
        "ui.order_app.messagebox.showinfo"
    ):
        app.export_date_range_csv()

    csv_path = tmp_path / "date_range_20240108_20240109.csv"
    with csv_path.open() as f:
        rows = list(csv.reader(f))

    # Workstation row should have recomputed hours
    assert rows[2][2] == "Cut"
    assert rows[2][5] == "0.50"
