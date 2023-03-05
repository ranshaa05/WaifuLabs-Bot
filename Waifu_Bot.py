import os
import logging
import coloredlogs
import nextcord
from nextcord.ext import commands
from PIL import Image #for image cropping

from delete_messages import *
from reaction import Reaction
from site_navigator import SiteNavigator

coloredlogs.install()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logging.getLogger("nextcord").setLevel(logging.WARNING)

TOKEN_FILE = "token.txt"
if not os.path.exists(TOKEN_FILE):
    logging.error(f"Error: {TOKEN_FILE} not found in program directory.")
    exit()

with open(TOKEN_FILE, "r") as file:
    TOKEN = file.read().strip()

CLIENT = commands.Bot(command_prefix="$", intents=nextcord.Intents().all(), case_insensitive=True)

@CLIENT.event
async def on_ready():
    logging.info("Bot Ready.")
    await CLIENT.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/waifu"))
    
SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "Screenshots")
connected_users = []

@CLIENT.slash_command(description="Build-a-waifu!")
async def waifu(interaction: nextcord.Interaction):
    if interaction.user.id in connected_users:
        await list_msg_id(await (await interaction.response.send_message("Whoops! One user cannot start me twice. You can continue or press ❌ to exit.")).fetch(), interaction)
        return
    else:
        connected_users.append(interaction.user.id)
        Reaction.stage[interaction.user.id] = 0
        await list_msg_id(await (await interaction.response.send_message("Hello! My name is WaifuBot! I make waifus using <https://www.waifulabs.com>. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid or use one of the following buttons:\n❌ to exit, ⬅ to go back, ➡ to keep your current waifu, 🤷‍♂️ to choose randomly or 🔄 to refresh.")).fetch(), interaction)
        navi = await SiteNavigator.create_navi()
        logging.info(f"Browser started for user '{interaction.user.name}'.")

        while Reaction.stage[interaction.user.id] < 4: #TODO: this is where i need to  tell the user they cant undo/keep waifu if they havent chosen one yet. figure this out.
            await save_send_screenshot(navi, navi.page, interaction)
            await delete_messages(interaction, CLIENT)
            if await navi.page_is_closed():
                break
            if Reaction.stage[interaction.user.id] < 4:
                await list_msg_id(await interaction.channel.send("Okay! lets continue. Here's another grid for you to choose from:"), interaction)

        if not await navi.page_is_closed():
            await delete_messages(interaction, CLIENT)
            await navi.wait_for_final_image()
            await (await navi.page.querySelector(".waifu-preview > img")).screenshot({'path': SCREENSHOT_PATH + '\\end_results\\end_result.png'})
            await navi.browser.close()
            logging.info(f"Browser closed for user '{interaction.user.name}', finished.")
            await interaction.channel.send(file=nextcord.File(SCREENSHOT_PATH + '\\end_results\\end_result.png'), content="Here's your waifu! Thanks for playing :slight_smile:")
            

        elif await navi.page_is_closed() and navi.timed_out:
            logging.info(f"Browser closed for user '{interaction.user.name}', timed out.")
            await delete_messages(interaction, CLIENT)
            await (await interaction.channel.send("Hey, anybody there? No? Okay, I'll shut down then :slight_frown:")).delete(delay=5)

        else:
            logging.info(f"Browser closed for user '{interaction.user.name}'")
        
        Reaction.stage.pop(interaction.user.id, None)
        connected_users.remove(interaction.user.id)



def create_dirs():
    if not os.path.exists(SCREENSHOT_PATH):
        logging.warning("screenshots folder does not exist, creating...")
        os.mkdir(SCREENSHOT_PATH)
        
    end_results_path = os.path.join(SCREENSHOT_PATH, 'end_results')
    if not os.path.exists(end_results_path):
        logging.warning("end_results folder does not exist, creating...")
        os.mkdir(end_results_path)



MAX_NUMBER_OF_FILES = 1000 + 1 #1 is for the additional files and folders in the folder
async def save_send_screenshot(navi, page, interaction):
    await navi.wait_for_not_load_screen()
    create_dirs()

    filenames_in_screenshot_path = os.listdir(SCREENSHOT_PATH)

    file_number = 0
    while os.path.isfile(os.path.join(SCREENSHOT_PATH, f"{file_number}.png")):    #checks and assigns the lowest file number available to next screenshot
        file_number += 1
    
    if len(filenames_in_screenshot_path) >= MAX_NUMBER_OF_FILES:
        await list_msg_id(await interaction.channel.send("*Server is busy! Your grid might take a while to be sent.*"), interaction)
        while len(filenames_in_screenshot_path) >= MAX_NUMBER_OF_FILES:
            filenames_in_screenshot_path = os.listdir(SCREENSHOT_PATH)
        return await save_send_screenshot(navi, page, interaction)


    if await page.querySelector(".sc-bdvvtL"): #check if grid is on stage 1 or not to determine whether or not it needs to be cropped
        selector = ".waifu-container"
        crop = True
    else:
        selector = ".waifu-grid"
        crop = False

    new_screenshot_path = os.path.join(SCREENSHOT_PATH, f"{file_number}.png")
    await (await page.querySelector(selector)).screenshot({'path': new_screenshot_path})

    if crop:
        image = Image.open(new_screenshot_path)
        width, height = image.size
        image.crop((0, height - 630, width, height)).save(new_screenshot_path)

    view = Reaction(navi, interaction)
    await list_msg_id(await interaction.channel.send(file=nextcord.File(SCREENSHOT_PATH + '\\' + str(file_number) + '.png'), view=view), interaction)
    os.remove(SCREENSHOT_PATH + '\\' + str(file_number) + '.png')
    await view.wait()
  

    ############ Stress test ############
    # #to debug with this, comment out the above line and uncomment the following lines
    # label_list = ["⬅", "➡", "🤷‍♂️", "🔄", "1" ,"2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"] #removing the numbers will perform a more thorough test.
    # import random
    # choice = random.choice(label_list)
    # logging.debug("Choice: " + choice + " || Stage: " + str(Reaction.stage[interaction.user.id]))
    # await view.click_by_label(choice, interaction.user.id)
    # if Reaction.stage[interaction.user.id] == 4:
    #     logging.debug("Finished")
    #     await interaction.channel.send("⌄⌄⌄⌄⌄This is a Bot-generated message.⌄⌄⌄⌄⌄")
        # TODO: find a way to re-run waifu()
    ######################################



if __name__ == "__main__":
    CLIENT.run(TOKEN)


