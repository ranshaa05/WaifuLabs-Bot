from types import SimpleNamespace
from unittest.mock import MagicMock

import nextcord

from permissions import REQUIRED_PERMISSIONS, check_permissions
from tests.helpers import make_interaction


def perms(**overrides):
    values = dict.fromkeys(REQUIRED_PERMISSIONS, True)
    values.update(overrides)
    return SimpleNamespace(**values)


def guild_interaction(role_perms, channel_perms):
    interaction = make_interaction()
    interaction.channel = MagicMock(spec=nextcord.TextChannel)
    interaction.channel.permissions_for.return_value = channel_perms
    interaction.guild.me.top_role.permissions = role_perms
    return interaction


async def test_dm_channel_always_allowed():
    interaction = make_interaction()
    interaction.channel = MagicMock(spec=nextcord.DMChannel)
    assert await check_permissions(interaction) is True


async def test_all_permissions_present():
    interaction = guild_interaction(perms(), perms())
    assert await check_permissions(interaction) is True
    interaction.response.send_message.assert_not_called()


async def test_missing_permissions_are_reported_per_scope():
    interaction = guild_interaction(perms(add_reactions=False), perms(manage_messages=False))

    assert await check_permissions(interaction) is False

    embed = interaction.response.send_message.call_args.kwargs["embed"]
    fields = {field.name: field.value for field in embed.fields}
    assert fields == {
        "❌ Missing in role:": "Add Reactions",
        "❌ Missing in channel:": "Manage Messages",
    }
