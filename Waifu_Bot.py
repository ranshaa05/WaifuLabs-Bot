#! python3

import os
from time import sleep
import nextcord
from nextcord.ext import commands
from PIL import Image #for image cropping
from delete_messages import *
from reaction import Reaction
from site_navigator import SiteNavigator


screenshot_path = os.path.dirname(__file__) + "\\Screenshots"

secret = "OTAwMDQ2MDU2Nzk5MjE5NzYy.YW7n" + "NQ.hKw0jtjSXoKFI4sL1CP715mZuUE"

user_msg_binder = {}
connected_users = []
msg_id = []


client = commands.Bot(command_prefix = "$", intents = nextcord.Intents().all(), case_insensitive=True)


@client.event
async def on_ready():
    print("\033[1;32;40mBot Ready.\033[0;37;40m")
    await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="$waifu start"))
    

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, nextcord.ext.commands.errors.CommandNotFound):
        return
    raise error


@client.command()
async def waifu(ctx):
    if ctx.message.content.lower() != "$waifu start":
        wrong_command_message = await ctx.channel.send("Whoops! The correct command is '$waifu start'.")
        sleep(5)
        await wrong_command_message.delete()


    else:
        if ctx.author.id in connected_users:
            await ctx.channel.send("Whoops! One user cannot start me twice. You can continue or press ❌ to exit.")
            await list_last_msg_id(ctx, user_msg_binder, client)
            return
        else:
            connected_users.append(ctx.author.id)


        async def main():
            navi = await SiteNavigator.create_navi()
            await ctx.channel.send("Hello! My name is WaifuBot! I make waifus using <https://www.waifulabs.com>. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid or use one of the following buttons:\n❌ to exit, ⬅ to go back, ➡ to keep your current waifu, 🤷‍♂️ to choose randomly or 🔄 to refresh.")
            await list_last_msg_id(ctx, user_msg_binder, client)
            print("\033[1;37;40mEvent: \033[1;32;40mBrowser started for user '" + str(ctx.author.name) + "'\033[0;37;40m")
            await save_screenshot_send(navi, navi.page, ctx)
            
            
            
            while Reaction.stage < 4:
                print("stage: " + str(Reaction.stage))
                await delete_messages(ctx, user_msg_binder, client)
                if await navi.page_is_closed():
                    break
                if Reaction.stage != 4:
                    await ctx.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
                    await list_last_msg_id(ctx, user_msg_binder, client)
                    await save_screenshot_send(navi, navi.page, ctx)
        

            if not await navi.page_is_closed():
                await delete_messages(ctx, user_msg_binder, client)
                await navi.wait_for_final_image()
                await (await navi.page.querySelector(".waifu-preview > img")).screenshot({'path': screenshot_path + '\\end_results\\end_result.png'})
                await navi.browser.close()
                print("\033[1;37;40mEvent: \033[93mBrowser closed for user '" + str(ctx.author.name) + "', \033[1;32;40mfinished.\033[0;37;40m")
                await ctx.channel.send(file=nextcord.File(screenshot_path + '\\end_results\\end_result.png'), content="Here's your waifu! Thanks for playing :slight_smile:")
                Reaction.stage = 0 #TODO: when stage is user specific, delete this.
                connected_users.remove(ctx.author.id)

            elif await navi.page_is_closed() and navi.timed_out:
                print("\033[1;37;40mEvent: \033[1;31;40mBrowser closed for user '" + str(ctx.author.name) + "', \033[1;32;40mtimed out.\033[0;37;40m")
                await delete_messages(ctx, user_msg_binder, client)
                timeout_message = await ctx.channel.send("Hey, anybody there? No? Okay, I'll shut down then :slight_frown:")
                sleep(5)
                await timeout_message.delete()
                Reaction.stage = 0 #TODO: when stage is  user specific, delete this.
                connected_users.remove(ctx.author.id)
            
            else:
                print("\033[1;37;40mEvent: \033[1;31;40mBrowser closed for user '" + str(ctx.author.name) + "'.\033[0;37;40m")
                Reaction.stage = 0 #TODO: when stage is  user specific, delete this.
                connected_users.remove(ctx.author.id)

        await main()



def create_dirs():
    if not os.path.exists(screenshot_path):
        print("\033[1;37;40mEvent: \033[1;31;40mscreenshots folder does not exist, creating...\033[0;37;40m")
        os.mkdir(os.path.dirname(os.path.realpath(__file__)) + "\\Screenshots")
        
    if not os.path.exists(screenshot_path + '\\end_results'):
        print("\033[1;37;40mEvent: \033[1;31;40mend_results folder does not exist, creating...\033[0;37;40m")
        os.mkdir(screenshot_path + "\\end_results")
        f = open(screenshot_path +"\\end_results\\.gitignore", "w")
        f.write("*\n!.gitignore")
        f.close()

        

max_number_of_files = 1000 + 2 #2 is for the additional files and folders in the folder
async def save_screenshot_send(navi, page, ctx):
    await navi.wait_for_not_load_screen()
    create_dirs()

    filenames_in_screenshot_path = os.listdir(screenshot_path)
    file_number = -1
    for i in range(max_number_of_files - 1):
        if os.path.isfile(screenshot_path + '\\' + str(i) + ".png"):    #checks and assigns the lowest file number available to next screenshot
            file_number += 1
        else:
            file_number += 1
            break
    
    if len(filenames_in_screenshot_path) >= max_number_of_files:
        await ctx.channel.send("*Server is busy! Your grid might take a while to be sent.*")
        await list_last_msg_id(ctx, user_msg_binder, client)
        while len(filenames_in_screenshot_path) >= max_number_of_files:
            sleep(0.01)
            filenames_in_screenshot_path = os.listdir(screenshot_path)
        return await save_screenshot_send(navi, page, ctx)


    file_number = 0
    while os.path.isfile(screenshot_path + '\\' + str(file_number) + ".png"):    #checks and assigns the lowest file number available to next screenshot
        file_number += 1

    if await page.querySelector(".sc-bdvvtL"):          #checks if grid is on stage one or not to determine if it needs cropping or not.
        await (await page.querySelector(".waifu-container")).screenshot({'path': screenshot_path + '\\' + str(file_number) + '.png'})
        crop = True
    else:
        await (await page.querySelector(".waifu-grid")).screenshot({'path': screenshot_path + '\\' + str(file_number) + '.png'})
        crop = False

    if crop:
        image = Image.open(screenshot_path + '\\' + str(file_number) + '.png')
        width, height = image.size
        image.crop((0, height - 630, width, height)).save(screenshot_path + '\\' + str(file_number) + '.png')

    view = Reaction(navi, ctx)
    await ctx.channel.send(file=nextcord.File(screenshot_path + '\\' + str(file_number) + '.png'), view=view)
    await list_last_msg_id(ctx, user_msg_binder, client)
    os.remove(screenshot_path + '\\' + str(file_number) + '.png')
    await view.wait()


    # await navi._fast_forward_to_final_() #to debug with this, comment out the above line and uncomment this line
    # Reaction.stage += 1




client.run(secret)
