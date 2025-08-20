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


def test_login_called_on_every_refresh():
    app = OrderScraperApp.__new__(OrderScraperApp)
    app.orders_url = "http://example.com/orders"
    app.credentials = {"username": "u", "password": "p"}
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
    app.prompt_login = MagicMock()

    with patch(
        "ui.order_app.ybs_client.fetch_orders",
        return_value={"orders_html": "<table></table>", "queue_html": "<table></table>"},
    ) as mock_fetch, patch(
        "ui.order_app.ybs_client.login", return_value={"success": True}
    ) as mock_login, patch(
        "ui.order_app.parse_orders", return_value=[]
    ) as mock_parse_orders, patch(
        "ui.order_app.parse_queue", return_value=[]
    ) as mock_parse_queue:
        app.refresh_orders()
        app.refresh_orders()

        assert mock_login.call_count == 2
        for call in mock_login.call_args_list:
            assert call.args[1] == app.credentials
        assert mock_fetch.call_count == 2
        assert mock_parse_orders.call_count == 2
        assert mock_parse_queue.call_count == 2
        app.prompt_login.assert_not_called()


def test_prompt_login_called_when_auto_login_fails():
    app = OrderScraperApp.__new__(OrderScraperApp)
    app.orders_url = "http://example.com/orders"
    app.credentials = {"username": "u", "password": "p"}
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
    app.prompt_login = MagicMock()

    with patch("ui.order_app.ybs_client.fetch_orders") as mock_fetch, patch(
        "ui.order_app.ybs_client.login", return_value={"success": False}
    ) as mock_login, patch("ui.order_app.parse_orders"), patch(
        "ui.order_app.parse_queue"
    ):
        app.refresh_orders()

        mock_login.assert_called_once()
        mock_fetch.assert_not_called()
        app.prompt_login.assert_called_once()
