import os
import glob
from PIL import Image #for image cropping
import nextcord

from view import View
from logger import setup_logging

class Screenshot():
    log = setup_logging().log
    SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "Screenshots")
    MAX_NUMBER_OF_FILES = 1000 + 1 #1 is for the additional files and folders in the folder
    def __init__(self, navi, interaction, original_message):
        self.navi = navi
        self.interaction = interaction
        self.original_message = original_message
        self.view = None

    async def save_send_screenshot(self):
        """saves a screenshot of the current page and sends it to the user."""
        self.create_dirs()
        await self.busy_wait()
        await self.navi.wait_for_not_load_screen()
        
        file_number = 0
        while os.path.isfile(os.path.join(Screenshot.SCREENSHOT_PATH, f"{file_number}.png")):    #checks and assigns the lowest file number available to next screenshot
            file_number += 1

        new_screenshot_path = os.path.join(Screenshot.SCREENSHOT_PATH, f"{file_number}.png")

        selector, crop, self.view, new_screenshot_path = await self.get_screenshot_info_by_stage(new_screenshot_path)

        await (await self.navi.page.querySelector(selector)).screenshot({'path': new_screenshot_path}) #NOTE: the object positioning can take too long, resulting in a slightly cropped image from the right. This is likely an issue with pyppeteer, not the code itself.

        if crop:
            image = Image.open(new_screenshot_path)
            width, height = image.size
            image.crop((0, height - 630, width, height)).save(new_screenshot_path)
            
        await self.original_message.edit(file=nextcord.File(new_screenshot_path), view=self.view if self.view else None)
        os.unlink(new_screenshot_path)
        
        await self.remove_reaction()
        if self.view:
            await self.view.wait()
            await self.add_reaction()



        ########### Stress test ############
        # #to debug with this, comment out the view.await() above and uncomment the following lines.
        # # #this will simulate button presses until the waifu is finished.
        # label_list = ["⬅", "➡", "🎲", "🔄", "1" ,"2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"] #removing the numbers will perform a more thorough test.
        # import random
        # choice = random.choice(label_list)
        # Screenshot.log.info("Choice: " + choice + " || Stage: " + str(View.stage[self.interaction.user.id]))
        # if not View.stage[self.interaction.user.id] == 4:
        #     await self.view.click_by_label(choice, self.interaction.user.id)
        # else: 
        #     Screenshot.log.info("Finished")
        #     await self.interaction.channel.send("^^^^This is a Bot-generated message.^^^^")
            # #TODO: find a way to re-run waifu()
        #####################################


    def create_dirs(self):
        """Creates the screenshot folders if they do not exist."""
        if not os.path.exists(Screenshot.SCREENSHOT_PATH):
            self.log.warning("screenshots folder does not exist, creating...")
            os.mkdir(Screenshot.SCREENSHOT_PATH)
            
        end_results_path = os.path.join(Screenshot.SCREENSHOT_PATH, 'end_results')
        if not os.path.exists(end_results_path):
            self.log.warning("end_results folder does not exist, creating...")
            os.mkdir(end_results_path)

    async def remove_reaction(self):
        """Removes all reactions from the original message."""
        if isinstance(self.original_message.channel, nextcord.abc.GuildChannel):
            await (await self.original_message.fetch()).clear_reactions()


    async def add_reaction(self):
            """Adds a reaction to the original message based on the button pressed in the view."""
            if isinstance(self.original_message.channel, nextcord.abc.GuildChannel):
                if self.view.current_label == "❓":
                    return
                #if the label is a single emoji (3 chars), it can be added directly. if it is a string of emojis, it must be split into 3 character chunks.
                elif len(self.view.current_label) > 3:
                    for emoji in [self.view.current_label[i:i+3] for i in range(0, len(self.view.current_label), 3)]:
                        await (await self.original_message.fetch()).add_reaction(emoji)
                else:
                    await (await self.original_message.fetch()).add_reaction(self.view.current_label)

    
    async def busy_wait(self):
        """Waits for the screenshot folder to have less than MAX_NUMBER_OF_FILES files in it."""
        files_in_screenshot_path = len(glob.glob(f"{Screenshot.SCREENSHOT_PATH}\*"))
        if files_in_screenshot_path >= self.MAX_NUMBER_OF_FILES:
            await self.original_message.edit("*Server is busy! Your grid might take a while to be sent.*")
            while files_in_screenshot_path >= self.MAX_NUMBER_OF_FILES:
                files_in_screenshot_path = len(glob.glob(f"{Screenshot.SCREENSHOT_PATH}\*"))

    async def get_screenshot_info_by_stage(self, new_screenshot_path): #TODO: perhaps have these passed to save_send_screenshot in the first place?
        """Returns the selector, crop, view, and new_screenshot_path based on the stage of the grid"""
        new_screenshot_path = new_screenshot_path
        if View.stage[self.interaction.user.id] in range(1,4):
            selector = ".waifu-container"
            crop = True
            view = View(self.navi, self.interaction)

        elif View.stage[self.interaction.user.id] == 0: #check if grid is on stage 0 or not to determine whether or not it needs to be cropped
            selector = ".waifu-grid"
            crop = False
            view = View(self.navi, self.interaction)

        else: #if on last stage
            new_screenshot_path = os.path.join(Screenshot.SCREENSHOT_PATH, 'end_results', 'end_result.png')
            await self.navi.wait_for_final_image()
            selector = ".waifu-preview > img"
            crop = False
            view = None
        
        return selector, crop, view, new_screenshot_path