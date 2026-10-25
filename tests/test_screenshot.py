from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from screenshot import ScreenshotHandler
from tests.helpers import make_interaction, make_navi
from view import View


@pytest.fixture
def handler():
    navi = make_navi()
    navi.wait_for_final_image = AsyncMock()
    navi.page.querySelector = AsyncMock()
    navi.page.evaluate = AsyncMock(return_value="data:image/png;base64,QUJD")
    return ScreenshotHandler(navi, make_interaction(), None)


# --- _get_screenshot_info_by_stage ---


async def test_stage_zero_screenshots_full_grid(handler):
    session_id = uuid4()
    View.stage[session_id] = 0
    try:
        selector, crop, view, b64_string = await handler._get_screenshot_info_by_stage(0, session_id)
    finally:
        View.stage.pop(session_id)

    assert (selector, crop, b64_string) == (".waifu-grid", False, None)
    assert isinstance(view, View)


@pytest.mark.parametrize("stage", [1, 2, 3])
async def test_middle_stages_crop_container(handler, stage):
    session_id = uuid4()
    View.stage[session_id] = stage
    try:
        selector, crop, view, b64_string = await handler._get_screenshot_info_by_stage(stage, session_id)
    finally:
        View.stage.pop(session_id)

    assert (selector, crop, b64_string) == (".waifu-container", True, None)
    assert isinstance(view, View)


async def test_final_stage_returns_base64_without_view(handler):
    selector, crop, view, b64_string = await handler._get_screenshot_info_by_stage(4, uuid4())

    assert (selector, crop, view, b64_string) == (None, False, None, "QUJD")
    handler.navi.wait_for_final_image.assert_awaited_once()
