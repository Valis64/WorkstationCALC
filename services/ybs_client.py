import requests

def login(session: requests.Session, credentials: dict) -> dict:
    return {"success": True}

def fetch_orders(session: requests.Session, url: str) -> dict:
    return {"orders_html": "", "queue_html": ""}
