from uuid import uuid4

import pytest

from site_navigator import MAX_GRID_CHOICES
from tests.helpers import make_interaction, make_navi, make_role
from view import View


@pytest.fixture
def session_id():
    session_id = uuid4()
    View.stage[session_id] = 0
    yield session_id
    View.stage.pop(session_id, None)


def make_view(session_id, co_operator=None, navi=None):
    return View(navi or make_navi(), make_interaction(user_id=1), co_operator, session_id)


def button(view, label):
    return next(item for item in view.children if item.custom_id == label)


async def test_view_has_all_buttons(session_id):
    view = make_view(session_id)
    labels = [item.custom_id for item in view.children]
    numbers = [str(i) for i in range(1, MAX_GRID_CHOICES + 1)]
    controls = ["⬅", "➡", "🎲", "🔄", "❌"]

    assert labels[:4] == numbers[:4]  # first row starts with the grid choices
    assert sorted(labels) == sorted(numbers + controls)  # every button exactly once


async def test_undo_and_skip_disabled_only_at_stage_zero(session_id):
    view = make_view(session_id)
    assert button(view, "⬅").disabled
    assert button(view, "➡").disabled
    assert not button(view, "🎲").disabled

    View.stage[session_id] = 1
    view = make_view(session_id)
    assert not button(view, "⬅").disabled
    assert not button(view, "➡").disabled


def test_number_emoji_list_has_unique_reaction_chunks():
    # Discord can't react with the same emoji twice, so multi-digit labels must not repeat a chunk.
    assert len(View._number_emoji_list) == MAX_GRID_CHOICES
    for label in View._number_emoji_list:
        chunks = [label[i : i + 3] for i in range(0, len(label), 3)] if len(label) > 3 else [label]
        assert len(chunks) == len(set(chunks)), label


@pytest.mark.parametrize(
    ("label", "action", "stage_change"),
    [
        ("⬅", "undo", -1),
        ("➡", "keep", 1),
        ("🎲", "rand", 1),
        ("🔄", "refresh", 0),
        ("❌", "exit", 0),
    ],
)
async def test_control_buttons_call_navi_and_update_stage(session_id, label, action, stage_change):
    View.stage[session_id] = 2
    navi = make_navi()
    view = make_view(session_id, navi=navi)

    await view._button_logic(label)

    getattr(navi, action).assert_awaited_once()
    assert View.stage[session_id] == 2 + stage_change


async def test_number_button_clicks_grid_and_advances(session_id):
    navi = make_navi()
    view = make_view(session_id, navi=navi)

    await view._button_logic("7")

    navi.click_by_index.assert_awaited_once_with(7)
    assert View.stage[session_id] == 1


async def test_button_callback_sets_emoji_label_and_stops(session_id):
    view = make_view(session_id)
    interaction = make_interaction()
    interaction.data = {"custom_id": "10"}

    await view._button_callback(interaction)

    assert view.current_label == "🔟"
    assert view.is_finished()


async def test_interaction_check_allows_author(session_id):
    view = make_view(session_id)
    assert await view.interaction_check(make_interaction(user_id=1))


async def test_interaction_check_rejects_stranger(session_id):
    view = make_view(session_id)
    stranger = make_interaction(user_id=2)

    assert not await view.interaction_check(stranger)
    stranger.response.send_message.assert_awaited_once()


async def test_interaction_check_allows_co_op_user(session_id):
    stranger = make_interaction(user_id=2)
    view = make_view(session_id, co_operator=stranger.user)
    assert await view.interaction_check(stranger)


async def test_interaction_check_allows_co_op_role_member(session_id):
    role = make_role()
    view = make_view(session_id, co_operator=role)
    assert await view.interaction_check(make_interaction(user_id=2, roles=[role]))
    assert not await view.interaction_check(make_interaction(user_id=3, roles=[]))


async def test_timeout_notifies_navigator(session_id):
    navi = make_navi()
    view = make_view(session_id, navi=navi)

    await view.on_timeout()

    navi.page_timeout.assert_awaited_once()
