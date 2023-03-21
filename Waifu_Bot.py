import os
import logging
import coloredlogs
import nextcord
from nextcord.ext import commands
from PIL import Image #for image cropping

from reaction import Reaction
from site_navigator import SiteNavigator

coloredlogs.install()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
log = logging.getLogger(__name__)
logging.getLogger("nextcord").setLevel(logging.WARNING)

TOKEN_FILE = "token.txt"
if not os.path.exists(TOKEN_FILE):
    log.error(f"Error: {TOKEN_FILE} not found in program directory.")
    exit()

with open(TOKEN_FILE, "r") as file:
    TOKEN = file.read().strip()

CLIENT = commands.Bot(command_prefix="$", intents=nextcord.Intents().all(), case_insensitive=True)

@CLIENT.event
async def on_ready():
    log.info("Bot Ready.")
    await CLIENT.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/waifu"))
    
SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "Screenshots")
connected_users = []

@CLIENT.slash_command(description="Build-a-waifu!")
async def waifu(interaction: nextcord.Interaction):
    if interaction.user.id in connected_users:
        await interaction.response.send_message("Whoops! One user cannot start me twice. You can continue or press ❌ to exit.", ephemeral=True, delete_after=5)
        return
    else:
        connected_users.append(interaction.user.id)
        Reaction.stage[interaction.user.id] = 0
        original_message = await interaction.response.send_message("Hello! My name is WaifuBot! I make waifus using <https://www.waifulabs.com>. let's start making your waifu!\nYou will be shown 4 grids of waifus, each one based on your previous choice.\nStart by telling me the position of your waifu on the following grid or use one of the following buttons:\n❌ to exit, ⬅ to go back, ➡ to keep your current waifu, 🤷‍♂️ to choose randomly or 🔄 to refresh.")
        navi = await SiteNavigator.create_navi()
        log.info(f"Browser started for user '{interaction.user.name}'.")

        while Reaction.stage[interaction.user.id] < 4: #TODO: this is where i need to  tell the user they cant undo/keep waifu if they havent chosen one yet. figure this out.
            await save_send_screenshot(navi, navi.page, interaction, original_message)
            if await navi.page_is_closed():
                await original_message.edit("Exiting...", delete_after=5, view=None) #TODO: remove the file attachment from the message, when nextcord supports it
                break
            if Reaction.stage[interaction.user.id] < 4:
                await original_message.edit("Okay! lets continue. Here's another grid for you to choose from:")

        if not await navi.page_is_closed():
            await navi.wait_for_final_image()
            await (await navi.page.querySelector(".waifu-preview > img")).screenshot({'path': SCREENSHOT_PATH + '\\end_results\\end_result.png'})
            await navi.browser.close()
            log.info(f"Browser closed for user '{interaction.user.name}', finished.")
            await original_message.edit(file=nextcord.File(SCREENSHOT_PATH + '\\end_results\\end_result.png'), content="Here's your waifu! Thanks for playing :slight_smile:" , view=None)
            

        elif await navi.page_is_closed() and navi.timed_out:
            log.info(f"Browser closed for user '{interaction.user.name}', timed out.")
            await original_message.edit("Hey, anybody there? No? Okay, I'll shut down then :slight_frown:", delete_after=5, view=None)

        else:
            log.info(f"Browser closed for user '{interaction.user.name}'")
        
        Reaction.stage.pop(interaction.user.id, None)
        connected_users.remove(interaction.user.id)



def create_dirs():
    if not os.path.exists(SCREENSHOT_PATH):
        log.warning("screenshots folder does not exist, creating...")
        os.mkdir(SCREENSHOT_PATH)
        
    end_results_path = os.path.join(SCREENSHOT_PATH, 'end_results')
    if not os.path.exists(end_results_path):
        log.warning("end_results folder does not exist, creating...")
        os.mkdir(end_results_path)



MAX_NUMBER_OF_FILES = 1000 + 1 #1 is for the additional files and folders in the folder
async def save_send_screenshot(navi, page, interaction, original_message):
    await navi.wait_for_not_load_screen()
    create_dirs()
    files_in_screenshot_path = len(os.listdir(SCREENSHOT_PATH))
    if files_in_screenshot_path >= MAX_NUMBER_OF_FILES:
        await original_message.edit("*Server is busy! Your grid might take a while to be sent.*")
        while files_in_screenshot_path >= MAX_NUMBER_OF_FILES:
            files_in_screenshot_path = len(os.listdir(SCREENSHOT_PATH))
        return await save_send_screenshot(navi, page, interaction, original_message)
    
    file_number = 0
    while os.path.isfile(os.path.join(SCREENSHOT_PATH, f"{file_number}.png")):    #checks and assigns the lowest file number available to next screenshot
        file_number += 1

    if await page.querySelector(".sc-bdvvtL"): #check if grid is on stage 1 or not to determine whether or not it needs to be cropped
        selector = ".waifu-container"
        crop = True
    else:
        selector = ".waifu-grid"
        crop = False

    new_screenshot_path = os.path.join(SCREENSHOT_PATH, f"{file_number}.png")
    await (await page.querySelector(selector)).screenshot({'path': new_screenshot_path}) #NOTE: the object positioning can take too long, resulting in a slightly cropped image from the right. This is likely an issue with pyppeteer, not the code itself.

    if crop:
        image = Image.open(new_screenshot_path)
        width, height = image.size
        image.crop((0, height - 630, width, height)).save(new_screenshot_path)

    view = Reaction(navi, interaction)
    await original_message.edit(file=nextcord.File(SCREENSHOT_PATH + '\\' + str(file_number) + '.png'), view=view)
    os.remove(SCREENSHOT_PATH + '\\' + str(file_number) + '.png')
    await view.wait()
  

    ########### Stress test ############
    #to debug with this, comment out the view.await() and uncomment the following lines.
    #this will simulate button presses until the waifu is finished.
    # label_list = ["⬅", "➡", "🤷‍♂️", "🔄", "1" ,"2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"] #removing the numbers will perform a more thorough test.
    # import random
    # choice = random.choice(label_list)
    # logging.info("Choice: " + choice + " || Stage: " + str(Reaction.stage[interaction.user.id]))
    # await view.click_by_label(choice, interaction.user.id)
    # if Reaction.stage[interaction.user.id] == 4:
    #     logging.info("Finished")
    #     await interaction.channel.send("^^^^This is a Bot-generated message.^^^^")
        #TODO: find a way to re-run waifu()
    #####################################



if __name__ == "__main__":
    CLIENT.run(TOKEN)


