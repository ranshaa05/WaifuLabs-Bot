from pyppeteer import launch
import appdirs
import os
import asyncio
import time
from random import random
import discord
from discord.ext import commands

screenshot_path = os.path.dirname(os.path.realpath(__file__)) + "\\Screenshots"

os.environ['PYPPETEER_HOME'] = appdirs.user_data_dir("pyppeteer")

secret = "ODA5MDQ2NzY2MzEzOTMwNzYy" + ".YCPZhA.LYEmy2_D_w1xdWfwt3KjSddZYGc"

connected_users = []
msg_id = []

client = commands.Bot(command_prefix = "$", Intents = discord.Intents().all())

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="$waifu start"))   

@client.command()
async def waifu(ctx, *, start):
    msg = await ctx.channel.history().get(author=ctx.author)
    msg_binder = {}
    
    if msg.content != "$waifu start":
        await ctx.channel.send("Whoops! The correct command is '$waifu start'.")
        await list_last_msg_id(ctx, msg_id, msg_binder)
        time.sleep(5)
        await delete_messages(ctx, msg, msg_id, msg_binder)     #probably not the best way to delete this


    else:
        clicked_undo = False
        clicked_refresh = False
        if ctx.author.id in connected_users:
            await ctx.channel.send("Whoops! One user cannot start me twice. You can try again or type 'exit' to exit.")
            await list_last_msg_id(ctx, msg_id, msg_binder)
            return

        else:
            connected_users.append(ctx.author.id)
        async def askposclick(page, browser, clicked_undo, clicked_refresh):
            try:
                global msg
                msg = await client.wait_for("message", timeout=120)
                while not await check(msg, page, browser):
                    msg = await client.wait_for("message", timeout=120)
                msg = msg.content
                if msg != "keep" and msg != "refresh" and msg != "undo" and msg != "exit" and msg != "stop":
                    x = int(msg[0]) - 1
                    y = int(msg[3]) - 1
                    pos = x + 4 * y
                    if not page.isClosed():
                        girls = await find_all_girls(page)
                        await girls[pos].click()
                    else:
                        return
                
                elif msg == "keep":
                    await ((await page.querySelectorAll(".keep-button"))[0]).click()
                
                elif clicked_refresh == False and clicked_undo == False and msg == "undo":
                    await ((await page.querySelectorAll(".undo-button"))[0]).click()
                    clicked_undo = True
                    await delete_messages(ctx, msg, msg_id, msg_binder)
                    await ctx.channel.send("Undoing...")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    await wait_for_all_girls(page)
                    msg = await ctx.channel.history().get(author=client.user)
                    await msg.delete(delay=2)
                    await ctx.channel.send("Okay! Here's the previous grid:")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    await save_screenshot_send(page, ctx, msg_id, msg_binder)
                    await askposclick(page, browser, clicked_undo, clicked_refresh)
                    await delete_messages(ctx, msg, msg_id, msg_binder)
                    await ctx.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    await save_screenshot_send(page, ctx, msg_id, msg_binder)
                    clicked_undo = False
                    return (await askposclick(page, browser, clicked_undo, clicked_refresh))
                    
                elif clicked_undo == True and msg == "undo":
                        await ctx.channel.send("You can only undo once!")
                        await list_last_msg_id(ctx, msg_id, msg_binder)
                        return (await askposclick(page, browser, clicked_undo, clicked_refresh))
                elif clicked_refresh == True and msg == "undo":
                        await ctx.channel.send("You can't undo after a refresh!")
                        await list_last_msg_id(ctx, msg_id, msg_binder)
                        return (await askposclick(page, browser, clicked_undo, clicked_refresh))

                elif msg == "exit" or msg == "stop":
                    await ctx.channel.send("Exiting...")
                    await page.close()
                    await browser.close()
                    print("\033[1;37;40mEvent: \033[93mBrowser Closed for user '" + str(ctx.author.name) + "'\033[0;37;40m")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    time.sleep(2)
                    connected_users.remove(ctx.author.id)


                else:
                    await ((await page.querySelectorAll(".refresh-button"))[0]).click()
                    clicked_refresh = True
                    await delete_messages(ctx, msg, msg_id, msg_binder)
                    await ctx.channel.send("Refreshing the grid...")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    await wait_for_all_girls(page)
                    await save_screenshot_send(page, ctx, msg_id, msg_binder)
                    await ctx.channel.send("Here you go :slight_smile:")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    return (await askposclick(page, browser, clicked_undo, clicked_refresh))
                    

            except asyncio.TimeoutError:
                await ctx.channel.send("Timed out! Stopping...")
                await list_last_msg_id(ctx, msg_id, msg_binder)
                await page.close()
                await browser.close()
                connected_users.remove(ctx.author.id)
                time.sleep(2)
                print("\033[1;37;40mEvent: \033[93mBrowser Closed for user '" + str(ctx.author.name) + "', \033[1;31;40mTimed out.\033[0;37;40m")

            

        async def check(msg, page, browser):
            if not (msg.author == ctx.author and msg.channel == ctx.channel):
                return False
            
            msg = msg.content

            if msg == "$waifu start":
                return False

            if msg.startswith('$waifu'):
                return False

            
            if (msg == "undo" or msg == "keep") and len(await page.querySelectorAll(".keep-button")) < 1:
                await ctx.channel.send("You haven't selected an initial waifu yet! Try something like 'x, y'.")
                await list_last_msg_id(ctx, msg_id, msg_binder)
                return False
            
            if not msg.startswith('$waifu') and msg != "keep" and msg != "refresh" and msg != "exit" and msg != "stop" and msg != "undo":      #makes sure the user input is valid.
                try:
                    if not ((msg.find(", ") == 1 or msg.find(" ,")) == 1 and len(msg) == 4):
                        await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'.")
                        await list_last_msg_id(ctx, msg_id, msg_binder)
                        return False
                    
                    if not (0 < int(msg[0]) < 5 and 0 < int(msg[3]) < 5):
                        await ctx.channel.send("Numbers too big or small! Try something between 1 and 4 :slight_smile:")
                        await list_last_msg_id(ctx, msg_id, msg_binder)
                        return False

                except ValueError:
                    await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'. x and y must be numbers.")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    return False

            return True
                

        async def main():
            browser = await launch(
                headless=True,
                autoClose=False
            )
            page = await browser.newPage()
            
            await page.setViewport({'width': 1550, 'height': 1000})
            await ctx.channel.send(f"Hello! I am WaifuBot! I make waifus using https://www.waifulabs.com. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid:")
            await list_last_msg_id(ctx, msg_id, msg_binder)
            await page.goto('https://waifulabs.com/')
            print("\033[1;37;40mEvent: \033[1;32;40mBrowser started for user '" + str(ctx.author.name) + "'\033[0;37;40m")
            await (await find_start_btn(page)).click()

            await wait_for_close_button(page)
            time.sleep(1)                              #executing these too quickly fails sometimes.
            await (await find_close_button(page)).click()
            
            await wait_for_all_girls(page)
            await save_screenshot_send(page, ctx, msg_id, msg_binder)
            await ctx.channel.send(f"Syntax for your answer must be 'x, y'. x represents the horizontal position of your waifu and y represents the vertical position.\n**The starting point is at the top left corner of the grid**.\nYou can also type 'keep' to continue with your current waifu, 'refresh' to refresh the grid, or 'undo' to return to the previous grid.\nYour answer:")
            await list_last_msg_id(ctx, msg_id, msg_binder)

            for i in range(0,3):
                await askposclick(page, browser, clicked_undo, clicked_refresh)         #timeout & 'exit' return here
                await delete_messages(ctx, msg, msg_id, msg_binder)
                if not page.isClosed():
                    await wait_for_all_girls(page)
                    await ctx.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
                    await list_last_msg_id(ctx, msg_id, msg_binder)
                    await save_screenshot_send(page, ctx, msg_id, msg_binder)
                else:
                    return
               

            await askposclick(page, browser, clicked_undo, clicked_refresh)
            await delete_messages(ctx, msg, msg_id, msg_binder)
            await wait_for_result(page)
            await (await page.querySelector(".my-girl-loaded")).screenshot({'path': screenshot_path + '\\end_results\\end_result.png'})
            await browser.close()
            print("\033[1;37;40mEvent: \033[93mBrowser Closed for user '" + str(ctx.author.name) + "', \033[1;32;40mfinished.\033[0;37;40m")
            await ctx.channel.send(file=discord.File(screenshot_path + '\\end_results\\end_result.png'))
            await ctx.channel.send("Here's your waifu! Thanks for playing :slight_smile:")
            connected_users.remove(ctx.author.id)

        
        await main()



#all functions

async def find_all_girls(page):
    return await page.querySelectorAll(".girl")

async def find_result(page):
    return await page.querySelectorAll(".my-girl-loaded")
    
async def wait_for_result(page):
    await wait_for_not_load_screen(page)
    while len(await find_result(page)) < 1:
        time.sleep(0.01)

async def wait_for_all_girls(page):
    await wait_for_not_load_screen(page)
    while len(await find_all_girls(page)) < 16 and len(await find_result(page)) < 1:
        time.sleep(0.01)

async def find_start_btn(page):
    return await page.querySelector('.button.block.blue')

async def find_close_button(page):
    return await page.querySelector('.sc-bxivhb.eTpeTG.sc-bdVaJa.cYQqRL')

async def wait_for_close_button(page):
    while not await find_close_button(page):
        time.sleep(0.01)

async def wait_for_not_load_screen(page):
    while len(await page.querySelectorAll(".bp3-spinner-head")) > 0:
        time.sleep(0.01)

async def wait_for_final_image(page):
    while len(await page.querySelectorAll(".product-image")) < 0:
        time.sleep(0.01)

async def save_screenshot_send(page, ctx, msg_id, msg_binder):
    await wait_for_not_load_screen(page)
    filename = os.listdir(screenshot_path)
    last_grid_number = (filename[-1])[-5]           #get last grid number
    if int(last_grid_number) < 10:
        next_grid_number = str(int(last_grid_number) + 1)           #next grid number
        await (await page.querySelector(".container")).screenshot({'path': screenshot_path + '\\grid' + next_grid_number + '.png'})
        await ctx.channel.send(file=discord.File(screenshot_path + '\\grid' + next_grid_number + '.png'))
        await list_last_msg_id(ctx, msg_id, msg_binder)
        
    else:
        for i in range(10):
            os.remove(screenshot_path + '\\' + str(os.listdir(screenshot_path)[-1]))            #if *too* many users use the bot at once, this might cause an overwrite, as there's a maximum of 8 grids in the folder.

            if int(last_grid_number) == "0":
                return
        return (await save_screenshot_send(page, ctx, msg_id, msg_binder))


async def list_last_msg_id(ctx, msg_id, msg_binder):
    last_msg = await ctx.channel.history().get(author=client.user)
    msg_id.append(last_msg.id)
    return

async def delete_messages(ctx, msg, msg_id, msg_binder):
    last_msg = await ctx.channel.history().get(author=client.user)
    try:
        msg_binder[ctx.author.id] = last_msg.id
        await client.http.delete_message(ctx.channel.id, msg_binder[ctx.author.id])
        del msg_id[-1]
        msg_binder[ctx.author.id] = msg_id[-1]
        return await delete_messages(ctx, msg, msg_id, msg_binder)

    except IndexError:
        return


                          
client.run(secret)