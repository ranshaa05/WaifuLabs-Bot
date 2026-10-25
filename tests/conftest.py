import json
import tempfile
from pathlib import Path

import pytest

from cogs import config_manager

DEFAULT_CONFIG = {"bot_token": "test-token", "admin_ids": [1], "admin_server_ids": [100]}

# cogs.admin_commands reads the config at import time, so point it away from the
# real config.json before any test module imports it.
_import_config = Path(tempfile.mkdtemp()) / "config.json"
_import_config.write_text(json.dumps(DEFAULT_CONFIG))
config_manager.CONFIG_PATH = str(_import_config)


@pytest.fixture(autouse=True)
def config_file(tmp_path, monkeypatch):
    """Gives every test its own throwaway config.json."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(DEFAULT_CONFIG))
    monkeypatch.setattr(config_manager, "CONFIG_PATH", str(path))
    return path
