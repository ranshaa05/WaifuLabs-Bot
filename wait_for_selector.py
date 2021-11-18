from time import sleep

async def click_start_btn(page):
    return await (await page.querySelector('.button.block.blue')).click()

async def click_close_button(page):
    await page.waitForSelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')
    return await (await page.querySelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')).click()

async def wait_for_not_load_screen(page):
    while await page.querySelector(".bp3-spinner-head"):
        sleep(0.01)

    
async def wait_for_result(page):
    await wait_for_not_load_screen(page)
    await page.waitForSelector(".my-girl-loaded")

async def find_all_girls(page):
    return await page.querySelectorAll(".girl")

async def wait_for_all_girls(page):
    await wait_for_not_load_screen(page)
    while len(await find_all_girls(page)) < 16 and await wait_for_result(page):
        sleep(0.01)


