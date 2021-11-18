#! python3

from pyppeteer import launch
import os
import asyncio
from time import sleep
from re import search
import discord
from discord.ext import commands
from wait_for_selector import *
from delete_messages import *

screenshot_path = os.path.dirname(__file__) + "\\Screenshots"

secret = "OTAwMDQ2MDU2Nzk5MjE5NzYy.YW7n" + "NQ.hKw0jtjSXoKFI4sL1CP715mZuUE"

msg_user_binder = {}
connected_users = []




client = commands.Bot(command_prefix = "$", Intents = discord.Intents().all(), case_insensitive=True)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="$waifu start"))
    print("\033[1;32;40mBot Started.\033[0;37;40m")



@client.command()
async def waifu(ctx):
    msg = await ctx.channel.history().get(author=ctx.author)


    if msg.content.lower() != "$waifu start":
        wrong_command_message = await ctx.channel.send("Whoops! The correct command is '$waifu start'.")
        sleep(5)
        await wrong_command_message.delete()


    else:
        clicked_undo = False
        clicked_refresh = False
        if ctx.author.id in connected_users:
            await ctx.channel.send("Whoops! One user cannot start me twice. You can continue or type 'exit' to exit.")
            await list_last_msg_id(ctx,  msg_user_binder, client)
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
                if not search("^(keep|refresh|exit|stop|undo)$", msg.lower()):
                    x = int(msg[0]) - 1
                    y = int(msg[-1]) - 1      #1, 1 is top left
                    y = 3 - y                #1, 1 is bottom left
                    pos = x + 4 * y
                    if not page.isClosed():
                        girls = await find_all_girls(page)
                        await girls[pos].click()
                    else:
                        return
                
                elif msg.lower() == "keep":
                    await (await page.querySelector(".keep-button")).click()
                
                elif clicked_refresh == False and clicked_undo == False and msg.lower() == "undo":
                    await (await page.querySelector(".undo-button")).click()
                    clicked_undo = True
                    await delete_messages(ctx, msg_user_binder, client)
                    await ctx.channel.send("Undoing...")
                    await wait_for_all_girls(page)
                    msg = await ctx.channel.history().get(author=client.user)
                    await msg.delete(delay=2)
                    await ctx.channel.send("Okay! Here's the previous grid:")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    await save_screenshot_send(page, ctx)
                    await askposclick(page, browser, clicked_undo, clicked_refresh)
                    await delete_messages(ctx, msg_user_binder, client)
                    if page.isClosed() == False:
                        await ctx.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
                        await list_last_msg_id(ctx,  msg_user_binder, client)
                        await save_screenshot_send(page, ctx)
                        clicked_undo = False
                        return (await askposclick(page, browser, clicked_undo, clicked_refresh))
                    else:
                        return
                    
                    
                elif clicked_undo == True and clicked_refresh == False and msg.lower() == "undo":
                        await ctx.channel.send("You can only undo once!")
                        await list_last_msg_id(ctx,  msg_user_binder, client)
                        return (await askposclick(page, browser, clicked_undo, clicked_refresh))
                elif clicked_refresh == True and msg.lower() == "undo":
                        await ctx.channel.send("You can't undo after a refresh!")
                        await list_last_msg_id(ctx,  msg_user_binder, client)
                        return (await askposclick(page, browser, clicked_undo, clicked_refresh))

                elif msg.lower() == "exit" or msg.lower() == "stop":
                    await ctx.channel.send("Exiting...")
                    await page.close()
                    await browser.close()
                    print("\033[1;37;40mEvent: \033[93mBrowser Closed for user '" + str(ctx.author.name) + "'\033[0;37;40m")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    connected_users.remove(ctx.author.id)
                    sleep(2)

                else:
                    await (await page.querySelector(".refresh-button")).click()
                    clicked_refresh = True
                    await delete_messages(ctx, msg_user_binder, client)
                    await ctx.channel.send("Refreshing the grid...")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    await wait_for_all_girls(page)
                    await save_screenshot_send(page, ctx)
                    await ctx.channel.send("Here you go :slight_smile:")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    return (await askposclick(page, browser, clicked_undo, clicked_refresh))


            except asyncio.TimeoutError:
                await ctx.channel.send("Timed out! Stopping...")
                await page.close()
                await browser.close()
                print("\033[1;37;40mEvent: \033[93mBrowser Closed for user '" + str(ctx.author.name) + "', \033[1;31;40mTimed out.\033[0;37;40m")
                await list_last_msg_id(ctx,  msg_user_binder, client)
                connected_users.remove(ctx.author.id)
                sleep(2)
                


            
        async def check(msg, page, browser):
            if not (msg.author == ctx.author and msg.channel == ctx.channel):
                return False
            
            msg = msg.content

            #########################################################
            if msg == "kill" and ctx.author.id == 521743580193357863:
                await page.close()
                await browser.close()
                await ctx.channel.send("Shutting down")
                exit(0)
            #########################################################

            if msg.lower() == "$waifu start":
                return False

            if msg.lower().startswith('$waifu'):
                return False

            
            if search("^(keep|undo)$", msg.lower()) and not await page.querySelector(".keep-button"):
                await ctx.channel.send("You haven't selected an initial waifu yet! Try something like 'x, y'.")
                await list_last_msg_id(ctx,  msg_user_binder, client)
                return False
            
            
            if not search("^(keep|refresh|exit|stop|undo)$", msg.lower()):      #makes sure the input isn't a command.
                if not search("\d, \d|\d ,\d|\d,\d", msg) or (search("\d,\d", msg) and len(msg) >=4) or len(msg) >= 5 or search("\d\d", msg):      #makes sure the user input is in one of the required formats.
                    await ctx.channel.send("Whoops! Wrong syntax. The correct syntax is 'x, y'. x and y must be numbers.")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    return False

                if not (0 < int(msg[0]) < 5 and 0 < int(msg[-1]) < 5):
                    await ctx.channel.send("Numbers too big or small! Try something between 1 and 4 :slight_smile:")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    return False

            return True
                

        async def main():
            browser = await launch(headless=True, autoClose=True)
            page = await browser.newPage()

            
            await page.setViewport({'width': 1550, 'height': 1000})
            await ctx.channel.send(f"Hello! My name is WaifuBot! I make waifus using https://www.waifulabs.com. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid:")
            await list_last_msg_id(ctx,  msg_user_binder, client)
            await page.goto('https://waifulabs.com/')
            print("\033[1;37;40mEvent: \033[1;32;40mBrowser started for user '" + str(ctx.author.name) + "'\033[0;37;40m")
            await click_start_btn(page)

            sleep(0.3)                              #executing these too quickly fails sometimes.
            await click_close_button(page)
            
            await wait_for_all_girls(page)
            await save_screenshot_send(page, ctx)
            await ctx.channel.send(f"Syntax for your answer must be 'x, y'. x represents the horizontal position of your waifu and y represents the vertical position.\n**The starting point is at the bottom left corner of the grid**.\nYou can also type 'keep' to continue with your current waifu, 'refresh' to refresh the grid, or 'undo' to return to the previous grid.\nYour answer:")
            await list_last_msg_id(ctx,  msg_user_binder, client)

            for i in range(3):                   #timeout & 'exit' return here
                await askposclick(page, browser, clicked_undo, clicked_refresh)
                await delete_messages(ctx, msg_user_binder, client)
                if not page.isClosed():
                    await wait_for_all_girls(page)
                    await ctx.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
                    await list_last_msg_id(ctx,  msg_user_binder, client)
                    await save_screenshot_send(page, ctx)
                else:
                    return
               
            await askposclick(page, browser, clicked_undo, clicked_refresh)
            await delete_messages(ctx, msg_user_binder, client)
            await wait_for_result(page)
            await (await page.querySelector(".my-girl-loaded")).screenshot({'path': screenshot_path + '\\end_results\\end_result.png'})
            await browser.close()
            print("\033[1;37;40mEvent: \033[93mBrowser Closed for user '" + str(ctx.author.name) + "', \033[1;32;40mfinished.\033[0;37;40m")
            await ctx.channel.send(file=discord.File(screenshot_path + '\\end_results\\end_result.png'))
            await ctx.channel.send("Here's your waifu! Thanks for playing :slight_smile:")
            connected_users.remove(ctx.author.id)

        await main()

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        return
    raise error

#all functions

def create_dirs():
    if "Screenshots" not in os.listdir(os.path.dirname(__file__)):
        print("\033[1;37;40mEvent: \033[1;31;40mscreenshots folder does not exist, creating...\033[0;37;40m")
        os.mkdir(os.path.dirname(os.path.realpath(__file__)) + "\\Screenshots")
        
    if "end_results" not in os.listdir(screenshot_path):
        print("\033[1;37;40mEvent: \033[1;31;40mend_results folder does not exist, creating...\033[0;37;40m")
        os.mkdir(screenshot_path + "\\end_results")
        f = open(screenshot_path +"\\end_results\\.gitignore", "w")
        f.write("*\n!.gitignore")
        f.close()

        

max_number_of_files = 1000 + 3
async def save_screenshot_send(page, ctx):
    await wait_for_not_load_screen(page)
    create_dirs()

    filenames_in_screenshot_path = os.listdir(screenshot_path)
    file_number = -1
    for i in range(max_number_of_files - 1):
        if os.path.isfile(screenshot_path + '\\' + str(i) + ".png"):    #checks and assigns the lowest file number available to next screenshot
            file_number += 1
        else:
            file_number += 1
            break
    
    if len(filenames_in_screenshot_path) < max_number_of_files:
        await (await page.querySelector(".container")).screenshot({'path': screenshot_path + '\\' + str(file_number) + '.png'})
        await ctx.channel.send(file=discord.File(screenshot_path + '\\' + str(file_number) + '.png'))
        await list_last_msg_id(ctx,  msg_user_binder, client)
        os.remove(screenshot_path + '\\' + str(file_number) + '.png')
    else:
        await ctx.channel.send("*Server is busy! Your grid might take a while to be sent.*")
        await list_last_msg_id(ctx,  msg_user_binder, client)
        while len(filenames_in_screenshot_path) >= max_number_of_files:
            sleep(0.01)
            filenames_in_screenshot_path = os.listdir(screenshot_path)
        return await save_screenshot_send(page, ctx)


client.run(secret)