import asyncio
from unittest.mock import AsyncMock

import pytest

import main
from tests.helpers import make_interaction


@pytest.fixture
def site_gate(monkeypatch):
    """Sessions block at the "connecting to the site" step until this event is set."""
    monkeypatch.setattr(main, "connected_users", [])
    return asyncio.Event()


@pytest.fixture
def create_navi(monkeypatch, site_gate):
    """Mocks the site connection. Once the gate opens it returns None (site offline),
    so the session exits right away without a browser."""

    async def wait_for_gate():
        await site_gate.wait()
        return None

    mock = AsyncMock(side_effect=wait_for_gate)
    monkeypatch.setattr(main.PageNavigator, "create_navi", mock)
    return mock


def start_interaction(user_id):
    interaction = make_interaction(user_id=user_id)
    interaction.response.send_message = AsyncMock(return_value=AsyncMock())
    return interaction


async def run_waifu(interaction):
    await main.waifu.callback(interaction, None, False)


def sent_text(interaction):
    return interaction.response.send_message.call_args.args[0]


async def test_user_cannot_start_bot_while_running(create_navi, site_gate):
    first = start_interaction(user_id=1)
    session = asyncio.create_task(run_waifu(first))
    await asyncio.sleep(0)  # let the first session register and block on the site
    assert main.connected_users == [1]

    second = start_interaction(user_id=1)
    # A rejected start returns immediately; without the guard it would block on the site.
    await asyncio.wait_for(run_waifu(second), timeout=1)

    assert "cannot start me twice" in sent_text(second)
    assert second.response.send_message.call_args.kwargs["ephemeral"] is True
    create_navi.assert_awaited_once()  # only the first session reached the site

    site_gate.set()
    await session


async def test_user_can_start_again_after_session_ends(create_navi, site_gate):
    site_gate.set()
    await run_waifu(start_interaction(user_id=1))
    assert main.connected_users == []

    again = start_interaction(user_id=1)
    await run_waifu(again)

    assert "cannot start me twice" not in sent_text(again)
    assert create_navi.await_count == 2


async def test_other_users_can_start_while_one_is_running(create_navi, site_gate):
    session = asyncio.create_task(run_waifu(start_interaction(user_id=1)))
    await asyncio.sleep(0)

    other = start_interaction(user_id=2)
    other_session = asyncio.create_task(run_waifu(other))
    await asyncio.sleep(0)

    assert "cannot start me twice" not in sent_text(other)
    assert sorted(main.connected_users) == [1, 2]
    assert create_navi.await_count == 2

    site_gate.set()
    await asyncio.gather(session, other_session)
    assert main.connected_users == []
