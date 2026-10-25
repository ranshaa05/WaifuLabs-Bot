from unittest.mock import AsyncMock, MagicMock

import nextcord


def make_interaction(user_id=1, guild_id=100, roles=()):
    """Builds a mock nextcord.Interaction with an async response."""
    interaction = MagicMock()
    interaction.user.id = user_id
    interaction.user.name = f"user{user_id}"
    interaction.user.roles = list(roles)
    if guild_id is None:
        interaction.guild = None
    else:
        interaction.guild.id = guild_id
    interaction.response.send_message = AsyncMock()
    return interaction


def make_role():
    return MagicMock(spec=nextcord.Role)


def make_navi():
    """Builds a mock PageNavigator."""
    navi = MagicMock()
    for name in ("undo", "keep", "rand", "refresh", "exit", "click_by_index", "page_timeout"):
        setattr(navi, name, AsyncMock())
    return navi
