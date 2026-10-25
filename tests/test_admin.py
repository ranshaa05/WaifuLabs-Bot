from unittest.mock import MagicMock

import pytest

from cogs import config_manager
from cogs.admin_commands import AdminCommands
from cogs.admin_permissions import check_permission
from cogs.admin_validation import validate_admins
from tests.helpers import make_interaction

# --- check_permission ---


async def test_check_permission_true_for_admin_in_admin_server():
    interaction = make_interaction(user_id=1, guild_id=100)
    assert await check_permission(interaction) is True
    interaction.response.send_message.assert_not_called()


async def test_check_permission_rejects_dm():
    interaction = make_interaction(user_id=1, guild_id=None)
    assert await check_permission(interaction) is False
    assert "admin server" in interaction.response.send_message.call_args.args[0]


async def test_check_permission_rejects_non_admin_server():
    interaction = make_interaction(user_id=1, guild_id=999)
    assert await check_permission(interaction) is False


async def test_check_permission_rejects_non_admin_user():
    interaction = make_interaction(user_id=2, guild_id=100)
    assert await check_permission(interaction) is False
    assert "not an admin" in interaction.response.send_message.call_args.args[0]


# --- validate_admins ---


async def test_validate_admins_removes_unknown_users_and_guilds():
    config_manager.save_admin_ids([1, 2])
    config_manager.save_admin_server_ids([100, 200])
    client = MagicMock()
    client.get_user.side_effect = lambda user_id: object() if user_id == 1 else None
    client.get_guild.side_effect = lambda guild_id: object() if guild_id == 100 else None

    await validate_admins(client)

    assert config_manager.get_admin_ids() == [1]
    assert config_manager.get_admin_server_ids() == [100]


async def test_validate_admins_leaves_valid_config_untouched(config_file):
    before = config_file.read_text()
    client = MagicMock()

    await validate_admins(client)

    assert config_file.read_text() == before


# --- manage_admins ---


@pytest.fixture
def cog():
    return AdminCommands(MagicMock())


def make_member(user_id):
    member = MagicMock()
    member.id = user_id
    member.name = f"member{user_id}"
    return member


async def call_manage_admins(cog, action, member):
    interaction = make_interaction(user_id=1, guild_id=100)
    await AdminCommands.manage_admins.callback(cog, interaction, action, member, True)
    return interaction.response.send_message.call_args.args[0]


async def test_manage_admins_adds_user(cog):
    message = await call_manage_admins(cog, "add", make_member(5))
    assert "added to" in message
    assert config_manager.get_admin_ids() == [1, 5]


async def test_manage_admins_removes_user(cog):
    config_manager.save_admin_ids([1, 5])
    message = await call_manage_admins(cog, "remove", make_member(5))
    assert "removed from" in message
    assert config_manager.get_admin_ids() == [1]


async def test_manage_admins_refuses_to_remove_last_admin(cog):
    message = await call_manage_admins(cog, "remove", make_member(1))
    assert "last admin" in message
    assert config_manager.get_admin_ids() == [1]


async def test_manage_admins_rejects_duplicate_add(cog):
    message = await call_manage_admins(cog, "add", make_member(1))
    assert "already an admin" in message
    assert config_manager.get_admin_ids() == [1]


async def test_manage_admins_rejects_removing_non_admin(cog):
    config_manager.save_admin_ids([1, 5])
    message = await call_manage_admins(cog, "remove", make_member(9))
    assert "is not an admin" in message
    assert config_manager.get_admin_ids() == [1, 5]
