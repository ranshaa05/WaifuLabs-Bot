import pyppeteer as pp
from pyppeteer import launch
import appdirs
import os
import asyncio
import time

async def find_all_girls(page):
	return await page.querySelectorAll(".girl")

async def find_start_btn(page):
	return await page.querySelector(".button.block.blue")

os.environ['PYPPETEER_HOME'] = appdirs.user_data_dir("pyppeteer")

x = []
y = []

print("pick a row (1-4)")
x.append(int(input()) - 1)
print("pick a position (1-4)")
y.append(int(input()) - 1)
for i in range(3):
  print(f"---stage #{i+1}---\npick a row (1-4)")
  x.append(int(input()))
  print(f"---stage #{i+1}---\npick a position(1-4)")
  y.append(int(input()))

async def main():
    browser = await launch(
        headless=False,
        autoClose=False
    )
    page = await browser.newPage()
    await page.goto('https://waifulabs.com/')
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    page.click(await find_start_btn(page))
    time.sleep(5)
    positions = []
    for x_pos, y_pos in zip(x, y):
        positions.append(x+4*y)
    
    girls = await find_all_girls(page)
    for i in range(4):
        await page.click(girls[i])
        time.sleep(5)
	

asyncio.get_event_loop().run_until_complete(main())
