"""
Configuration management for API
"""
import json
import os
from .dependencies import traders

API_CONFIG_FILE = "api_config.json"


def save_api_config():
    """Save API settings to JSON file"""
    config = {}
    for exchange, data in traders.items():
        config[exchange] = {
            "enabled": data["enabled"],
            "is_started": data["is_started"],
            "name": data["name"],
        }

    try:
        with open(API_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        print(f"API configuration saved to {API_CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving API configuration: {e}")


def load_api_config():
    """Load API settings from JSON file"""
    if not os.path.exists(API_CONFIG_FILE):
        print(f"No configuration file found at {API_CONFIG_FILE}, using defaults")
        return

    try:
        with open(API_CONFIG_FILE, "r") as f:
            config = json.load(f)

        for exchange, settings in config.items():
            if exchange in traders:
                traders[exchange]["enabled"] = settings.get(
                    "enabled", traders[exchange]["enabled"]
                )
                traders[exchange]["is_started"] = settings.get(
                    "is_started", traders[exchange]["is_started"]
                )
                traders[exchange]["name"] = settings.get(
                    "name", traders[exchange]["name"]
                )

        print(f"API configuration loaded from {API_CONFIG_FILE}")
    except Exception as e:
        print(f"Error loading API configuration: {e}")
