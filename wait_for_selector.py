from time import sleep

async def wait_for_not_load_screen(page):
    while await page.querySelector(".loading-callout"):
        sleep(0.01)


async def find_all_girls(page):
    return await page.querySelectorAll(".waifu-grid > div")






