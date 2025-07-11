import asyncio
from pyppeteer import launch
from random import randint

UNDO_BUTTON_SELECTOR = ".sc-bdvvtL:nth-child(1)"
KEEP_BUTTON_SELECTOR = ".sc-bdvvtL:nth-child(2)"
WAIFU_GRID_SELECTOR = ".waifu-grid > div"
LOADING_SELECTOR = ".loading-callout"
FINAL_IMAGE_LOADING_SELECTOR = ".waifu-preview-loading"
MAX_GRID_CHOICES = 15
REFRESH_BUTTON_INDEX = 15  # The 16th element is the refresh button


class PageNavigator:
    browser = None

    def __init__(self):
        self.page = None
        self.timed_out = False

    @staticmethod
    async def _initialize_browser():
        """Initializes the pyppeteer browser instance if it hasn't been already."""
        if PageNavigator.browser is None or not PageNavigator.browser.isConnected():
            PageNavigator.browser = await launch(headless=True, autoClose=True)

    @staticmethod
    async def create_navi():
        await PageNavigator._initialize_browser()
        navi = PageNavigator()
        navi.page = await PageNavigator.browser.newPage()
        await navi.page.setViewport({"width": 1200, "height": 630})
        await navi.page.goto("https://waifulabs.com/generate")
        return navi

    async def click_by_index(self, index):
        girls = await self.find_all_girls()
        await girls[index - 1].click()

    async def exit(self):
        if self.page and not self.page.isClosed():
            await self.page.close()

    async def undo(self):
        await self.page.click(UNDO_BUTTON_SELECTOR)

    async def keep(self):
        await self.page.click(KEEP_BUTTON_SELECTOR)

    async def rand(self):
        random_index = randint(1, MAX_GRID_CHOICES)
        await self.page.click(f"{WAIFU_GRID_SELECTOR}:nth-child({random_index})")

    async def refresh(self):
        await (await self.find_all_girls())[REFRESH_BUTTON_INDEX].click()

    async def wait_for_not_load_screen(self):
        while await self.page.querySelector(LOADING_SELECTOR):
            await asyncio.sleep(0.01)

    async def wait_for_final_image(self):
        while await self.page.querySelector(FINAL_IMAGE_LOADING_SELECTOR):
            await asyncio.sleep(0.01)

    async def screenshot(self, selector):
        element = await self.page.querySelector(selector)
        screenshot_bytes = await element.screenshot()
        return screenshot_bytes

    async def find_all_girls(self):
        return await self.page.querySelectorAll(WAIFU_GRID_SELECTOR)

    async def page_timeout(self):
        # this is to differentiate between a timeout and a user exiting.
        self.timed_out = True
        await self.exit()
