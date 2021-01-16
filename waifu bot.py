#imports
from pyppeteer import launch
import appdirs
import os
import asyncio
import time
from random import random

async def find_all_girls(page):
    return await page.querySelectorAll(".girl")


async def find_start_btn(page):
    return await page.querySelector('.button.block.blue')


async def find_close_button(page):
    return await page.querySelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')

async def wait_for_close_button(page):
    while not await find_close_button(page):
        print(not await find_close_button(page))

async def wait_for_all_girls(page):
        while len(await find_all_girls(page)) < 16:
            pass
        
os.environ['PYPPETEER_HOME'] = appdirs.user_data_dir("pyppeteer")

x = []
y = []

#print("pick a row (1-4)")
#x.append(int(input()) - 1)
x.append(3)
#print("pick a position (1-4)")
#y.append(int(input()) - 1)
y.append(3)
for i in range(3):
#    print(f"---stage #{i + 1}---\npick a row (1-4)")
#    x.append(int(input()) - 1)
    x.append(3)

#    print(f"---stage #{i + 1}---\npick a position(1-4)")
#    y.append(int(input()) - 1)
    y.append(3)
print(str(x) + str(y))
async def main():
    browser = await launch(
        headless=False,
        autoClose=False
    )
    page = await browser.newPage()
    
    await page.setViewport({'width': 1550, 'height': 1000})
    await page.goto('https://waifulabs.com/')
    await (await find_start_btn(page)).click()

    await wait_for_close_button(page)
    
    
    await (await find_close_button(page)).click()
  
    positions = []
    for x_pos, y_pos in zip(x, y):
        positions.append(x_pos + 4 * y_pos)
    
    for pos in positions:
        print(pos)
        time.sleep(1.5)
        await wait_for_all_girls(page)
        girls = await find_all_girls(page)
        await girls[pos].click()
        
    time.sleep(2)
    await page.screenshot({'path': 'example.png'})             #saves screenshot of result page

    
        
asyncio.get_event_loop().run_until_complete(main())
