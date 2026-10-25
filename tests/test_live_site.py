"""Simulates a full run against the real waifulabs.com to catch selector changes.

Needs network and a Chromium download, so it is skipped on GitHub Actions.
"""

import os

import pytest

from site_navigator import (
    KEEP_BUTTON_SELECTOR,
    REFRESH_BUTTON_INDEX,
    UNDO_BUTTON_SELECTOR,
    WAIFU_GRID_SELECTOR,
    PageNavigator,
)

pytestmark = pytest.mark.skipif(os.environ.get("GITHUB_ACTIONS") == "true", reason="hits the live site")


async def test_full_run_on_live_site():
    navi = await PageNavigator.create_navi()
    assert navi is not None, "could not reach waifulabs.com"
    page = navi.page

    # Each stage: the selectors that must exist, then the action a user takes.
    middle = [".waifu-container", UNDO_BUTTON_SELECTOR, KEEP_BUTTON_SELECTOR]
    stages = [
        ([".waifu-grid"], lambda: navi.click_by_index(1)),
        (middle, navi.rand),
        (middle, navi.keep),
        (middle, lambda: navi.click_by_index(15)),
    ]

    try:
        await page.waitForSelector(WAIFU_GRID_SELECTOR, {"timeout": 30000})

        for stage, (selectors, action) in enumerate(stages):
            await navi.wait_for_not_load_screen()
            for selector in selectors:
                assert await page.querySelector(selector), f"stage {stage}: {selector}"
            assert len(await navi.find_all_girls()) > REFRESH_BUTTON_INDEX, f"stage {stage}"
            await action()

        await navi.wait_for_not_load_screen()
        # The preview image already exists from stage 1, so the empty grid is what
        # proves every action above actually advanced a stage.
        assert not await navi.find_all_girls(), "run did not reach the final stage"
        await navi.wait_for_final_image()
        final_image = await page.querySelector(".waifu-preview > img")
        assert final_image, ".waifu-preview > img"
        src = await page.evaluate("(element) => element.src", final_image)
        assert src.startswith("data:image/"), "final image src is no longer a base64 data URL"
    finally:
        await PageNavigator.browser.close()
        PageNavigator.browser = None
