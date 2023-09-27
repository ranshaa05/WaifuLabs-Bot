import functools
import asyncio
from pyppeteer import launch
from random import randint
from time import sleep


def _page_stack(coroutine):
    """a decorator that takes returns to the page of the previous user"""

    @functools.wraps(coroutine)
    async def wrapper(self, *args, **kwargs):
        previous_page = PageNavigator.active_page
        await self.page.bringToFront()
        return_value = await coroutine(self, *args, **kwargs)
        if previous_page:
            await previous_page.bringToFront()
        PageNavigator.active_page = previous_page
        return return_value

    return wrapper


class PageNavigator:
    browser = asyncio.get_event_loop().run_until_complete(
        launch(headless=True, autoClose=True)
    )
    active_page = None

    def __init__(self):
        self.page = None
        self.timed_out = False

    @staticmethod
    async def create_navi():
        navi = PageNavigator()
        navi.page = await PageNavigator.browser.newPage()
        await navi.page.setViewport({"width": 1200, "height": 630})
        await navi.page.goto("https://waifulabs.com/generate")
        return navi

    @_page_stack
    async def click_by_index(self, index):
        girls = await self.find_all_girls()
        await girls[index - 1].click()

    @_page_stack
    async def exit(self):
        await self.page.close()

    @_page_stack
    async def undo(self):
        await self.page.click(".sc-bdvvtL:nth-child(1)")

    @_page_stack
    async def keep(self):
        await self.page.click(".sc-bdvvtL:nth-child(2)")

    @_page_stack
    async def rand(self):
        random_index = randint(1, 15)
        await self.page.click(f".waifu-grid > div:nth-child({random_index})")

    @_page_stack
    async def refresh(self):
        await (await self.find_all_girls())[15].click()

    @_page_stack
    async def wait_for_not_load_screen(self):
        while await self.page.querySelector(".loading-callout"):
            sleep(0.01)

    @_page_stack
    async def wait_for_final_image(self):
        while await self.page.querySelector(".waifu-preview-loading"):
            sleep(0.01)

    @_page_stack
    async def screenshot(self, selector, new_screenshot_path):
        await (await self.page.querySelector(selector)).screenshot(
            {"path": new_screenshot_path}
        )

    async def find_all_girls(self):
        return await self.page.querySelectorAll(".waifu-grid > div")

    async def page_timeout(self):
        # this is to differentiate between a timeout and a user exiting.
        self.timed_out = True
        await self.exit()
