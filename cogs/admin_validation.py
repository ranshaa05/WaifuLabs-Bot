from .config_manager import save_admin_ids, save_admin_server_ids, get_admin_ids, load_config
from logger import setup_logging

async def _check_config_not_empty(log, client, admin_list, server_list):
    if not admin_list:
        log.error("No admin IDs found. Please add at least one admin ID to config.json.")

    if not server_list:
        log.error("No valid server IDs found. Please add at least one server ID to config.json.")

    if not admin_list or not server_list:
        await client.close()

async def validate_admins(client):
    "Checks if the admin IDs and admin server IDs are valid."
    log = setup_logging().log
    original_admin_ids = get_admin_ids()
    valid_admin_ids, invalid_admin_ids = [], []
    for user_id in original_admin_ids:
        user = client.get_user(int(user_id))
        if user:
            valid_admin_ids.append(user_id)
        else:
            invalid_admin_ids.append(user_id)

    if invalid_admin_ids:
        log.warning(
            f"The following admin IDs were removed because they do not point to valid users: {', '.join(map(str, invalid_admin_ids))}"
        )
        save_admin_ids(valid_admin_ids)

    config_data = load_config()
    original_server_ids = config_data.get("admin_server_ids", [])
    valid_server_ids, invalid_server_ids = [], []
    for server_id in original_server_ids:
        guild = client.get_guild(int(server_id))
        if guild:
            valid_server_ids.append(server_id)
        else:
            invalid_server_ids.append(server_id)

    if invalid_server_ids:
        log.warning(
            f"The following Admin Server IDs were removed because they do not point to valid guilds: {', '.join(map(str, invalid_server_ids))}"
        )
        save_admin_server_ids(valid_server_ids)

    await _check_config_not_empty(log, client, valid_admin_ids, valid_server_ids)