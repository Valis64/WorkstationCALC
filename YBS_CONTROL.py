"""Application entry point with automatic dependency setup.

This module now performs a lightweight bootstrap before importing GUI
dependencies.  When executed it will ensure all packages listed in
``requirements.txt`` are installed.  Missing packages are built into wheels
and installed from a local ``wheelhouse`` directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _ensure_requirements() -> None:
    """Install packages from ``requirements.txt`` if any are missing.

    A ``wheelhouse`` directory is created to cache built wheels.  Packages are
    installed from these wheels so subsequent runs can operate offline.
    """

    req_file = Path(__file__).with_name("requirements.txt")
    if not req_file.exists():
        return

    try:
        import pkg_resources  # type: ignore
    except Exception:  # pragma: no cover - bootstrap only
        subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools", "wheel"])
        import pkg_resources  # type: ignore

    installed = {pkg.key for pkg in pkg_resources.working_set}
    required = [
        line.strip()
        for line in req_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    missing = [pkg for pkg in required if pkg.split("==")[0].lower() not in installed]
    if not missing:
        return

    wheel_dir = Path(__file__).with_name("wheelhouse")
    wheel_dir.mkdir(exist_ok=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "wheel"])
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "-r",
        str(req_file),
        "-w",
        str(wheel_dir),
    ])
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(wheel_dir),
        "-r",
        str(req_file),
    ])


_ensure_requirements()

import customtkinter as ctk

from ui import theme

theme.configure()

from ui.order_app import OrderScraperApp
from login_dialog import LoginDialog
from config.settings import load_config
from services import ybs_client
import requests


def main():
    root = ctk.CTk()
    config = load_config()
    credentials: dict[str, str] | None = None
    session = requests.Session()
    authenticated = False
    username = config.get("username")
    password = config.get("password")
    if username and password:
        credentials = {"username": username, "password": password}
        try:
            resp = ybs_client.login(session, credentials)
            authenticated = resp.get("success", False)
        except requests.RequestException:
            authenticated = False
    if not authenticated:
        dialog = LoginDialog(root)
        dialog.grab_set()
        root.wait_window(dialog)
        if not dialog.authenticated:
            return
        session = dialog.session
        credentials = dialog.credentials
    OrderScraperApp(root, session=session, credentials=credentials)
    root.mainloop()


if __name__ == "__main__":
    main()
