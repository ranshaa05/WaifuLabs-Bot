import pyppeteer as pp
from pyppeteer import launch
import appdirs
import os
import asyncio
import time
import win32api
x, y = win32api.GetCursorPos()

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
    await page.setViewport({'width': 800, 'height': 900})
    await page.goto('https://waifulabs.com/')
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    await page.mouse.click(700, 700)
    await page.mouse.click(460, 250)
    time.sleep(4)
    x_poses = [140+180*pos for pos in x]
    y_poses = [180+170*pos for pos in y]
    for i in range(4):
        await page.mouse.click(x_poses[i],y_poses[i])
        time.sleep(5)
    


	
async def FindAllGirls(page):
	list = page.querySelectorAll(".girl")
	return list
async def FindStartBtn(page)
	return page.querySelector(".button.block.blue")



    if "start" == input():
        while True:
            print(win32api.GetCursorPos())
            time.sleep(2)
    else:
        print("Stopped.")

        

asyncio.get_event_loop().run_until_complete(main())

