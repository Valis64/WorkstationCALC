import threading
from unittest.mock import MagicMock, patch

from ui.order_app import OrderScraperApp


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


def test_print_file_logged_after_job_leaves_queue():
    app = OrderScraperApp.__new__(OrderScraperApp)
    app.session = MagicMock()
    app.orders_url = "http://example.com/orders"
    app.db = MagicMock()
    app.db_lock = threading.Lock()
    app.set_status = MagicMock()
    app.append_db_log = MagicMock()
    app._call_async = lambda func: func()
    app.schedule_order_scrape = MagicMock()
    app.countdown_var = DummyVar("")
    app.refresh_countdown_job = None
    app.last_queue = set()
    app.seen_queue_jobs = set()
    app.root = object()
    app.credentials = {"username": "u", "password": "p"}

    with patch("ui.order_app.ybs_client.fetch_orders") as mock_fetch, \
         patch("ui.order_app.ybs_client.login", return_value={"success": True}), \
         patch("ui.order_app.parse_orders", return_value=[]), \
         patch("ui.order_app.parse_queue") as mock_queue, \
         patch("ui.order_app.db.record_print_file_start") as mock_record:
        mock_fetch.return_value = {"orders_html": "", "queue_html": ""}
        mock_queue.side_effect = [[], ["JOB1"], []]

        app.refresh_orders()
        mock_record.assert_not_called()

        app.refresh_orders()
        mock_record.assert_not_called()

        app.refresh_orders()
        mock_record.assert_called_once_with(app.db, app.db_lock, "JOB1")
        assert app.last_queue == set()
        assert app.seen_queue_jobs == set()
