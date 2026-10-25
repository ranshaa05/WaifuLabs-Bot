import json

from cogs import config_manager


def test_load_config_reads_file(config_file):
    assert config_manager.load_config()["bot_token"] == "test-token"


def test_getters_default_to_empty_list(config_file):
    config_file.write_text(json.dumps({"bot_token": "x"}))
    assert config_manager.get_admin_ids() == []
    assert config_manager.get_admin_server_ids() == []


def test_save_admin_ids_preserves_other_keys(config_file):
    config_manager.save_admin_ids([1, 2, 3])

    saved = json.loads(config_file.read_text())
    assert saved["admin_ids"] == [1, 2, 3]
    assert saved["bot_token"] == "test-token"
    assert saved["admin_server_ids"] == [100]


def test_save_admin_server_ids_preserves_other_keys(config_file):
    config_manager.save_admin_server_ids([200])

    saved = json.loads(config_file.read_text())
    assert saved["admin_server_ids"] == [200]
    assert saved["admin_ids"] == [1]
