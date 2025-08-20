import json
from pathlib import Path

CONFIG_FILE = Path("ybs_config.json")

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}

def save_config(config: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(config))
