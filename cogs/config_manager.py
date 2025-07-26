import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
CONFIG_PATH = os.path.join(project_root, "config.json")


def load_config():
    """Loads the configuration from config.json."""
    with open(CONFIG_PATH, "r") as config_file:
        return json.load(config_file)


def save_config(config_data):
    """Saves the configuration to config.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)


def get_admin_ids():
    """Returns the list of admin IDs from the config."""
    config_data = load_config()
    return config_data.get("admin_ids", [])


def save_admin_ids(admin_list):
    """Saves the provided admin list to config.json."""
    config_data = load_config()
    config_data["admin_ids"] = admin_list
    save_config(config_data)


def save_admin_server_ids(server_list):
    """Saves the provided admin server list to config.json."""
    config_data = load_config()
    config_data["admin_server_ids"] = server_list
    save_config(config_data)