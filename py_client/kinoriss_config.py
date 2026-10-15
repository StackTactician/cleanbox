"""
Kinoriss Config — Persistent configuration management.
"""

import json
from pathlib import Path

from .constants import DEFAULT_TOKEN, DEFAULT_DOWNLOAD_DIR

CONFIG_DIR = Path.home() / ".kinoriss"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "token": DEFAULT_TOKEN,
    "output_dir": DEFAULT_DOWNLOAD_DIR,
    "language": "en",
    "country": "NG",
    "preferred_quality": None,
}


def load_config():
    """Load config from ~/.kinoriss/config.json, returning defaults for missing keys."""
    config = dict(DEFAULTS)
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                config.update(saved)
    except (json.JSONDecodeError, OSError, ValueError):
        pass
    return config


def save_config(config):
    """Write config dict to disk."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except OSError:
        pass


def get_token():
    """Return token from config, falling back to DEFAULT_TOKEN."""
    cfg = load_config()
    return cfg.get("token") or DEFAULT_TOKEN
