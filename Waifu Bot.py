#imports
from pyppeteer import launch
import appdirs
import os
import asyncio
import time
from random import random
import discord
from discord.ext import commands


dir_path = os.path.dirname(os.path.realpath(__file__))

os.environ['PYPPETEER_HOME'] = appdirs.user_data_dir("pyppeteer")

secret = ""

client = commands.Bot(command_prefix = "$", Intents = discord.Intents().all())
@client.command()


async def waifu(ctx, *, start):
    async def askposclick(page):
        msg = await client.wait_for("message")
        while not await check(msg, page):
            msg = await client.wait_for("message")
        msg = msg.content
        if not msg == "keep":
            x = int(msg[0]) - 1
            y = int(msg[3]) - 1
            pos = x + 4 * y
            time.sleep(1.5)
            await wait_for_all_girls(page)
            girls = await find_all_girls(page)
            await girls[pos].click()

        else:
            await ((await page.querySelectorAll(".keep-button"))[0]).click()



    async def check(msg, page):
        if not (msg.author == ctx.author and msg.channel == ctx.channel):
            return False
        
        msg = msg.content

        if msg == "$waifu start":
            return False

        if msg == "keep" and len(await page.querySelectorAll(".keep-button")) < 1:
            await ctx.channel.send("You haven't selected an initial waifu yet! Try something like 'x, y'.")
            return False
        if msg != "keep":
            try:
                if not (msg.find(", ") == 1 and len(msg) == 4):
                    await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'.")
                    return False
                
                if not (0 < int(msg[0]) < 5 and 0 < int(msg[3]) < 5):              #makes sure the user input is valid.
                    await ctx.channel.send("Numbers too big or small! Try something between 1 and 4 :)")
                    return False

            except ValueError:
                await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'. x and y must be numbers.")
                return False


        return True
            


    async def main():
        browser = await launch(                                             #opens browser
            headless=False,
            autoClose=False
        )
        page = await browser.newPage()
        
        await page.setViewport({'width': 1550, 'height': 1000})
        await page.goto('https://waifulabs.com/')
        await (await find_start_btn(page)).click()
        

        await wait_for_close_button(page)
        time.sleep(1)                                                       #executing these too quickly fails sometimes.
        await (await find_close_button(page)).click()

        await ctx.channel.send(f"Hello! I am WaifuBot! I make waifus using waifulabs.com. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid:")
        time.sleep(3)
        await (await page.querySelector(".container")).screenshot({'path': dir_path + '\Screenshots\grid1.png'})
        await ctx.channel.send(file=discord.File(dir_path + '\Screenshots\grid1.png'))
        await ctx.channel.send(f"Syntax for your answer must be 'x, y'. x represents the horizontal position of your waifu and y represents the vertical position.\nThe starting point is at the top left corner of the grid. You can also type 'keep' to continue with your current waifu.\nYour answer:")
        
        for i in range(0,3):
            await askposclick(page)
            time.sleep(3)
            await ctx.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
            await page.screenshot({'path': dir_path + '\Screenshots\grid2.png'}, clip = {"x": 160, "y": 250, "height": 690, "width": 1250})
            await ctx.channel.send(file=discord.File(dir_path + '\Screenshots\grid2.png'))
            
        await askposclick(page)

        time.sleep(2)
        await (await page.querySelector(".my-girl-image")).screenshot({'path': dir_path + '\Screenshots\end_result.png'})             #saves screenshot of result page

        await ctx.channel.send(file=discord.File(dir_path + '\Screenshots\end_result.png'))
        await ctx.channel.send("Here you go! :)")

        time.sleep(5)
        await browser.close()                                          #closes browser to free up resources.

    asyncio.get_event_loop().run_until_complete(await main())
    

async def find_all_girls(page):
    return await page.querySelectorAll(".girl")

async def find_start_btn(page):
    return await page.querySelector('.button.block.blue')

async def find_close_button(page):
    return await page.querySelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')

async def wait_for_close_button(page):
    while not await find_close_button(page):
        time.sleep(0.01)

async def wait_for_all_girls(page):
        while len(await find_all_girls(page)) < 16:
            time.sleep(0.01)
        

client.run(secret)