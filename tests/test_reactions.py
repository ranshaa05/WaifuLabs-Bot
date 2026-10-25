from unittest.mock import AsyncMock, MagicMock

import nextcord
import pytest

from screenshot import ScreenshotHandler
from tests.helpers import make_interaction, make_navi


@pytest.fixture
def handler():
    return ScreenshotHandler(make_navi(), make_interaction(), None)


def make_message(guild=True, ephemeral=False):
    message = MagicMock(spec=nextcord.Message)
    message.channel = MagicMock(spec=nextcord.TextChannel if guild else nextcord.DMChannel)
    message.flags.ephemeral = ephemeral
    message.add_reaction = AsyncMock()
    message.clear_reactions = AsyncMock()
    return message


def reactions(message):
    return [call.args[0] for call in message.add_reaction.await_args_list]


# --- _is_message_reactable ---


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        (make_message(), True),
        (make_message(guild=False), False),
        (make_message(ephemeral=True), False),
        (MagicMock(), False),  # e.g. an InteractionMessage-like object
    ],
)
def test_is_message_reactable(handler, message, expected):
    assert handler._is_message_reactable(message) is expected


# --- remove_reactions ---


async def test_remove_reactions_clears_reactable_message(handler):
    message = make_message()

    await handler.remove_reactions(message)

    message.clear_reactions.assert_awaited_once()


async def test_remove_reactions_skips_unreactable_message(handler):
    message = make_message(ephemeral=True)

    await handler.remove_reactions(message)

    message.clear_reactions.assert_not_called()


# --- add_reaction ---


async def test_add_reaction_single_emoji(handler):
    handler.view = MagicMock(current_label="🎲")
    message = make_message()

    await handler.add_reaction(message)

    assert reactions(message) == ["🎲", "⏳"]


async def test_add_reaction_splits_multi_digit_label(handler):
    handler.view = MagicMock(current_label="1️⃣2️⃣")
    message = make_message()

    await handler.add_reaction(message)

    assert reactions(message) == ["1️⃣", "2️⃣", "⏳"]


async def test_add_reaction_skips_placeholder(handler):
    handler.view = MagicMock(current_label="❓")
    message = make_message()

    await handler.add_reaction(message)

    message.add_reaction.assert_not_called()


async def test_add_reaction_skips_unreactable_message(handler):
    handler.view = MagicMock(current_label="🎲")
    message = make_message(ephemeral=True)

    await handler.add_reaction(message)

    message.add_reaction.assert_not_called()
