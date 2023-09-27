import os
import glob
from PIL import Image
import base64 as b64
from io import BytesIO
import nextcord


from view import View
from logger import setup_logging

log = setup_logging().log


class Screenshot:
    SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "Screenshots")
    MAX_NUMBER_OF_FILES = (
        1000 + 1
    )  # +num is for any additional files and folders in the folder

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
        while os.path.isfile(
            os.path.join(Screenshot.SCREENSHOT_PATH, f"{file_number}.png")
        ):
            # checks and assigns the lowest file number available to next screenshot
            file_number += 1

        new_screenshot_path = os.path.join(
            Screenshot.SCREENSHOT_PATH, f"{file_number}.png"
        )

        (
            selector,
            crop,
            self.view,
            new_screenshot_path,
            b64_image,
        ) = await self.get_screenshot_info_by_stage(new_screenshot_path)

        if (
            b64_image
        ):  # this is for the final stage, where the image is a base64 string and not a screenshot of an element.
            image_bytes = b64.b64decode(b64_image)
            pil_image = Image.open(BytesIO(image_bytes))
            pil_image.save(new_screenshot_path)

        else:
            await self.navi.screenshot(selector, new_screenshot_path)

            if crop:
                image = Image.open(new_screenshot_path)
                width, height = image.size
                image.crop((0, height - 630, width, height)).save(new_screenshot_path)

        await self.original_message.edit(
            file=nextcord.File(new_screenshot_path),
            view=self.view if self.view else None,
        )
        os.unlink(new_screenshot_path)

        self.original_message = await self.original_message.fetch()

        await self.remove_reaction()
        if self.view:
            await self.view.wait()
            await self.add_reaction()

    def create_dirs(self):
        """Creates the screenshot folders if they do not exist."""
        if not os.path.exists(Screenshot.SCREENSHOT_PATH):
            log.warning("screenshots folder does not exist, creating...")
            os.mkdir(Screenshot.SCREENSHOT_PATH)

        final_results_path = os.path.join(Screenshot.SCREENSHOT_PATH, "final_results")
        if not os.path.exists(final_results_path):
            log.warning("final_results folder does not exist, creating...")
            os.mkdir(final_results_path)

    async def remove_reaction(self):
        """Removes all reactions from the original message."""
        if (
            isinstance(self.original_message.channel, nextcord.abc.GuildChannel)
            and not self.original_message.flags.ephemeral
        ):  # check if message is reactable in the first place
            await self.original_message.clear_reactions()

    async def add_reaction(self):
        """Adds a reaction to the original message based on the button pressed in the view."""
        if (
            isinstance(self.original_message.channel, nextcord.abc.GuildChannel)
            and not self.original_message.flags.ephemeral
        ):  # check if message is reactable
            if self.view.current_label == "❓":
                return
            # if the label is a single emoji (3 chars), it can be added directly. if it is a string of emojis, it must be split into 3 character chunks.
            elif len(self.view.current_label) > 3:
                for emoji in [
                    self.view.current_label[i : i + 3]
                    for i in range(0, len(self.view.current_label), 3)
                ]:
                    await self.original_message.add_reaction(emoji)
            else:
                await self.original_message.add_reaction(self.view.current_label)
            await self.original_message.add_reaction("⏳")

    async def busy_wait(self):
        """Waits for the screenshot folder to have less than MAX_NUMBER_OF_FILES files in it."""
        files_in_screenshot_path = len(glob.glob(rf"{Screenshot.SCREENSHOT_PATH}\*"))
        if files_in_screenshot_path >= self.MAX_NUMBER_OF_FILES:
            await self.original_message.edit(
                "*Server is busy! Your grid might take a while to be sent.*"
            )
            while files_in_screenshot_path >= self.MAX_NUMBER_OF_FILES:
                files_in_screenshot_path = len(
                    glob.glob(rf"{Screenshot.SCREENSHOT_PATH}\*")
                )

    async def get_screenshot_info_by_stage(self, new_screenshot_path):
        """Returns the selector, crop, view, and new_screenshot_path based on the stage of the grid, as well as the base64 image if on the last stage."""
        selector, crop, view, b64_image = (
            None,
            False,
            None,
            None,
        )  # these are the default values.

        if View.stage[self.interaction.user.id] in range(1, 4):
            selector = ".waifu-container"
            crop = True
            view = View(self.navi, self.interaction)

        elif View.stage[self.interaction.user.id] == 0:
            selector = ".waifu-grid"
            view = View(self.navi, self.interaction)

        else:
            # if on last stage.
            # this is a bit of a hack, but it works. the final image is not a screenshot, but is rather a base64 encoded image taken from the element's src attribute.
            # this is done because of an issue with pyppeteer's screenshot function.
            new_screenshot_path = os.path.join(
                self.SCREENSHOT_PATH, "final_results", "final_result.png"
            )
            await self.navi.wait_for_final_image()

            final_image_element = await self.navi.page.querySelector(
                ".waifu-preview > img"
            )
            final_image_url = await self.navi.page.evaluate(
                "(element) => element.src", final_image_element
            )
            final_image_base64 = final_image_url.split(",")[1]
            b64_image = final_image_base64

        return selector, crop, view, new_screenshot_path, b64_image
