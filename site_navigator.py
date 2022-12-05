from pyppeteer import launch
from random import randint
from time import sleep


class SiteNavigator():
    def __init__(self):
        self.browser = None
        self.page = None
        self.timed_out = False

    @staticmethod
    async def create_navi():
        navi = SiteNavigator()
        navi.browser = await launch(headless=True, autoClose=True)
        navi.page = await navi.browser.newPage()
        await navi.page.setViewport({'width': 1200, 'height': 630})
        await navi.page.goto('https://waifulabs.com/generate')
        return navi

    async def click_by_index(self, index):
        girls = await self.find_all_girls()
        await girls[index -1].click()

    async def exit(self):
        await self.page.close()
        await self.browser.close()

    async def undo(self):
        if await self.page.querySelectorAll(".sc-bdvvtL"):
            await (await self.page.querySelectorAll(".sc-bdvvtL"))[0].click()
    
    async def keep(self):
        if await self.page.querySelectorAll(".sc-bdvvtL"):
            await (await self.page.querySelectorAll(".sc-bdvvtL"))[1].click()
    
    async def rand(self):
        label = randint(1, 15)
        girls = await self.find_all_girls()
        await girls[label].click()

    async def refresh(self):
        await (await self.find_all_girls())[15].click()

    async def wait_for_not_load_screen(self):
        while await self.page.querySelector(".loading-callout"):
            sleep(0.01)

    async def wait_for_final_image(self): #TODO: doesn't work
        while await self.page.querySelector(".waifu-preview-loading"):
            sleep(0.01)

    async def find_all_girls(self):
        return await self.page.querySelectorAll(".waifu-grid > div")



    async def browser_timeout(self):
        await self.page.close()
        await self.browser.close()
        await self.page_is_closed()
        self.timed_out = True

    async def page_is_closed(self):
        return self.page.isClosed()
    



