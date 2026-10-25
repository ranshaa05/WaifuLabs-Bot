from unittest.mock import AsyncMock, MagicMock

import pytest

import site_navigator
from site_navigator import MAX_GRID_CHOICES, REFRESH_BUTTON_INDEX, PageNavigator


@pytest.fixture
def navi():
    navi = PageNavigator()
    navi.page = MagicMock()
    navi.page.isClosed.return_value = False
    navi.page.close = AsyncMock()
    navi.page.click = AsyncMock()
    navi.grid = [MagicMock(click=AsyncMock()) for _ in range(REFRESH_BUTTON_INDEX + 1)]
    navi.page.querySelectorAll = AsyncMock(return_value=navi.grid)
    return navi


async def test_click_by_index_is_one_based(navi):
    await navi.click_by_index(1)
    navi.grid[0].click.assert_awaited_once()


async def test_refresh_clicks_refresh_button(navi):
    await navi.refresh()
    navi.grid[REFRESH_BUTTON_INDEX].click.assert_awaited_once()


async def test_rand_clicks_a_grid_cell_in_range(navi, monkeypatch):
    monkeypatch.setattr(site_navigator, "randint", lambda a, b: b)
    await navi.rand()
    navi.page.click.assert_awaited_once_with(f".waifu-grid > div:nth-child({MAX_GRID_CHOICES})")


async def test_exit_closes_open_page(navi):
    await navi.exit()
    navi.page.close.assert_awaited_once()


async def test_exit_skips_already_closed_page(navi):
    navi.page.isClosed.return_value = True
    await navi.exit()
    navi.page.close.assert_not_called()


async def test_page_timeout_marks_timed_out_and_closes(navi):
    await navi.page_timeout()
    assert navi.timed_out
    navi.page.close.assert_awaited_once()
