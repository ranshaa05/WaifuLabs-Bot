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

secret = "ODA5MDQ2NzY2MzEzOTMwNzYy.YCPZhA.PItlTYokiM82pW6gJKSr1oz-yAY"

client = commands.Bot(command_prefix = "$", Intents = discord.Intents().all())
@client.command()


async def waifu(ctx, *, start):
    await ctx.channel.send(f"Hello! I am WaifuBot! I make waifus using waifulabs.com. let's start making your waifu!\nStart by telling me the position of your waifu on the following grid:")
       
    await ctx.channel.send(f"Syntax for your answer must be 'x, y'. x represents the horizontal position of your waifu and y represents the vertical position.\nThe starting point is at the top left cornet of the grid.\nYour answer:")


    async def check(msg):
        retvalue = True
        if not (msg.author == ctx.author and msg.channel == ctx.channel):
            retvalue = False
        
        msg = msg.content

        try:
            if not 0 < int(msg[0]) < 5 and 0 < int(msg[3]) < 5 and msg.find(", ") == 1 and len(msg) == 5:              #makes sure the user input is valid. to do: for some reason it accepts inputs higher or lower than 4 and longer or shorter than 5 chars, but does not accept non-integers
                await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'.")
                return False

        except IndexError:
            await ctx.channel.send("Whoops! Numbers too big! Try something between 1 and 4 :)")                        # no idea if we even need this

        except ValueError:
            await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'. x and y must be numbers.")
            return False
        
        return retvalue
            


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
        
        await (await find_close_button(page)).click()

        
        for i in range(0,4):
            msg = await client.wait_for("message")
            while not await check(msg):
                msg = await client.wait_for("message")
            msg = msg.content
            x = int(msg[0]) - 1
            y = int(msg[3]) - 1
            pos = x + 4 * y

            time.sleep(1.5)
            await wait_for_all_girls(page)
            girls = await find_all_girls(page)
            await girls[pos].click()
            
        time.sleep(2)
        await (await page.querySelector(".my-girl-image")).screenshot({'path': dir_path + '\end_result.png'})             #saves screenshot of result page

        await ctx.channel.send(file=discord.File(dir_path + '\end_result.png'))
        await ctx.channel.send("Here you go! :)")

        
            
    asyncio.get_event_loop().run_until_complete(await main())
    

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
        

client.run(secret)
