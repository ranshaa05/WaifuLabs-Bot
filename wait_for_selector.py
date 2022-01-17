from time import sleep

async def click_close_button(page):
    await page.waitForSelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')
    return await (await page.querySelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')).click()

async def wait_for_not_load_screen(page):
    while await page.querySelector(".loading-callout"):
        sleep(0.01)

    
async def wait_for_result(page):
    await wait_for_not_load_screen(page)
    await page.waitForSelector(".waifu-preview")

async def find_all_girls(page):
    return list(await page.querySelectorAll("div"))[43:148] #TODO: selecting all divs is a temporary solution.

async def wait_for_all_girls(page):     #TODO: this might be useless in new site
    await wait_for_not_load_screen(page)
    while ((len(await find_all_girls(page)) / 7) < 15) and await wait_for_result(page):
        sleep(0.01)



