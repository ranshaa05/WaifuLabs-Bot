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

secret = ""

client = commands.Bot(command_prefix = "$", intents = nextcord.Intents().all(), case_insensitive=True)


@client.event
async def on_ready():
    print("\033[1;32;40mBot Ready.\033[0;37;40m")
    await client.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="$waifu start"))
    
connected_users = []

@client.slash_command(description="Build-a-waifu!")
async def waifu(interaction: nextcord.Interaction):
    if interaction.user.id in connected_users:
        await interaction.channel.send("Whoops! One user cannot start me twice. You can continue or press ❌ to exit.")
        await list_last_msg_id(interaction, client)
        return
    else:
        connected_users.append(interaction.user.id)
        Reaction.stage[interaction.user.id] = 0


        navi = await SiteNavigator.create_navi()
        await interaction.response.send_message("Hello! My name is WaifuBot! I make waifus using <https://www.waifulabs.com>. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid or use one of the following buttons:\n❌ to exit, ⬅ to go back, ➡ to keep your current waifu, 🤷‍♂️ to choose randomly or 🔄 to refresh.")
        await list_last_msg_id(interaction, client)
        print("\033[1;37;40mEvent: \033[1;32;40mBrowser started for user '" + str(interaction.user.name) + "'\033[0;37;40m")
        await save_send_screenshot(navi, navi.page, interaction)
        
        while Reaction.stage[interaction.user.id] < 4:
            await delete_messages(interaction, client)
            if await navi.page_is_closed():
                break
            await interaction.channel.send("Okay! lets continue. Here's another grid for you to choose from:")
            await list_last_msg_id(interaction, client)
            await save_send_screenshot(navi, navi.page, interaction)


        if not await navi.page_is_closed():
            await delete_messages(interaction, client)
            await navi.wait_for_final_image()
            await (await navi.page.querySelector(".waifu-preview > img")).screenshot({'path': screenshot_path + '\\end_results\\end_result.png'})
            await navi.browser.close()
            print("\033[1;37;40mEvent: \033[93mBrowser closed for user '" + str(interaction.user.name) + "', \033[1;32;40mfinished.\033[0;37;40m")
            await interaction.channel.send(file=nextcord.File(screenshot_path + '\\end_results\\end_result.png'), content="Here's your waifu! Thanks for playing :slight_smile:")
            

        elif await navi.page_is_closed() and navi.timed_out:
            print("\033[1;37;40mEvent: \033[1;31;40mBrowser closed for user '" + str(interaction.user.name) + "', \033[1;32;40mtimed out.\033[0;37;40m")
            await delete_messages(interaction, client)
            timeout_message = await interaction.channel.send("Hey, anybody there? No? Okay, I'll shut down then :slight_frown:")
            sleep(5)
            await timeout_message.delete()

        else:
            print("\033[1;37;40mEvent: \033[1;31;40mBrowser closed for user '" + str(interaction.user.name) + "'.\033[0;37;40m")
        
        Reaction.stage.pop(interaction.user.id, None)
        connected_users.remove(interaction.user.id)




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

        

max_number_of_files = 1000 + 1 #1 is for the additional files and folders in the folder
async def save_send_screenshot(navi, page, interaction):
    await navi.wait_for_not_load_screen()
    create_dirs()

    filenames_in_screenshot_path = os.listdir(screenshot_path)

    file_number = 0
    while os.path.isfile(screenshot_path + '\\' + str(file_number) + ".png"):    #checks and assigns the lowest file number available to next screenshot
        file_number += 1
    
    if len(filenames_in_screenshot_path) >= max_number_of_files:
        await interaction.channel.send("*Server is busy! Your grid might take a while to be sent.*")
        await list_last_msg_id(interaction, client)
        while len(filenames_in_screenshot_path) >= max_number_of_files:
            sleep(0.01)
            filenames_in_screenshot_path = os.listdir(screenshot_path)
        return await save_send_screenshot(navi, page, interaction)


    if await page.querySelector(".sc-bdvvtL"):  #checks if grid is on stage one or not to determine if it needs cropping or not.
        await (await page.querySelector(".waifu-container")).screenshot({'path': screenshot_path + '\\' + str(file_number) + '.png'})
        crop = True
    else:
        await (await page.querySelector(".waifu-grid")).screenshot({'path': screenshot_path + '\\' + str(file_number) + '.png'})
        crop = False

    if crop:
        image = Image.open(screenshot_path + '\\' + str(file_number) + '.png')
        width, height = image.size
        image.crop((0, height - 630, width, height)).save(screenshot_path + '\\' + str(file_number) + '.png')

    view = Reaction(navi, interaction)
    await interaction.channel.send(file=nextcord.File(screenshot_path + '\\' + str(file_number) + '.png'), view=view)
    await list_last_msg_id(interaction, client)
    os.remove(screenshot_path + '\\' + str(file_number) + '.png')
    await view.wait()
  

    ############ Stress test ############
    # #to debug with this, comment out the above line and uncomment the following lines
    # label_list = ["⬅", "➡", "🤷‍♂️", "🔄", "1" ,"2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"] #removing the numbers will perform a more thorough test.
    # import random
    # choice = random.choice(label_list)
    # print("Choice: " + choice + " || Stage: " + str(Reaction.stage[interaction.user.id]))
    # await view.click_by_label(choice, interaction.user.id)
    # if Reaction.stage[interaction.user.id] == 4:
    #     print("Finished")
    #     await interaction.channel.send("⌄⌄⌄⌄⌄This is a Bot-generated message.⌄⌄⌄⌄⌄")
        # TODO: find a way to re-run waifu()
    ######################################







client.run(secret)
