import asyncio
import base64 as b64
import glob
import os
from io import BytesIO

from PIL import Image
import nextcord

from logger import setup_logging
from view import View

log = setup_logging().log


class ScreenshotHandler:
    """Handles the screenshotting and sending of the screenshot."""
    SCREENSHOT_PATH = os.path.join(os.path.dirname(__file__), "Screenshots")
    MAX_NUMBER_OF_FILES = (
        1000 + 1
    )  # +num is for any additional files and folders in the folder

    def __init__(self, navi, interaction, original_message, co_operator):
        self.navi = navi
        self.interaction = interaction
        self.co_operator = co_operator
        self.original_message = original_message
        self.view = None
        self.pil_image = None

    async def save_send_screenshot(self, session_id):
        """saves a screenshot of the current page and sends it to the user."""
        await self.navi.wait_for_not_load_screen()

        (
            selector,
            crop,
            self.view,
            b64_image
        ) = await self.get_screenshot_info_by_stage(View.stage[session_id], session_id)

        if b64_image:  # for final stage, where the image is a base64 string, not a screenshot of an element.
            image_bytes = b64.b64decode(b64_image)
            self.pil_image = Image.open(BytesIO(image_bytes))
        else:
            self.pil_image = await self.navi.screenshot(selector)

        if crop:
            width, height = self.pil_image.size
            self.pil_image = self.pil_image.crop((0, height - 630, width, height))

        # Convert the PIL image to bytes
        byte_arr = BytesIO()
        self.pil_image.save(byte_arr, format="PNG")
        byte_arr.seek(0)

        file = nextcord.File(byte_arr, filename="image.png")
        await self.original_message.edit(
            file=file,
            view=self.view if self.view else None,
        )

        # Close the PIL image
        self.pil_image = None
        byte_arr.close()

        self.original_message = await self.original_message.fetch()

        asyncio.create_task(self.remove_reaction())
        if self.view:
            await self.view.wait()
            asyncio.create_task(self.add_reaction())

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
            # if the label is a single emoji (3 chars), it can be added directly.
            # if it is a string of emojis, it must be split into chunks of 3 chars.
            elif len(self.view.current_label) > 3:
                for emoji in [
                    self.view.current_label[i : i + 3]
                    for i in range(0, len(self.view.current_label), 3)
                ]:
                    await self.original_message.add_reaction(emoji)
            else:
                await self.original_message.add_reaction(self.view.current_label)
            await self.original_message.add_reaction("⏳")

    async def get_screenshot_info_by_stage(self, stage, session_id):
        """Returns the selector, crop, and view based on the stage of the grid, as well as the base64 image if on the last stage."""
        if stage in range(1, 4):
            selector = ".waifu-container"
            crop = True
            view = View(self.navi, self.interaction, self.co_operator, session_id)
            b64_image = None

        elif stage == 0:
            selector = ".waifu-grid"
            crop = False
            view = View(self.navi, self.interaction, self.co_operator, session_id)
            b64_image = None

        else:
            # if on last stage.
            # this is a bit of a hack, but it works
            # the final image is not a screenshot, but a base64 image taken from the element's src attribute
            # this is done because of an issue with pyppeteer's screenshot func
            await self.navi.wait_for_final_image()

            final_image_element = await self.navi.page.querySelector(".waifu-preview > img")
            final_image_url = await self.navi.page.evaluate("(element) => element.src", final_image_element)
            final_image_base64 = final_image_url.split(",")[1]
            
            selector = None
            crop = False
            view = None
            b64_image = final_image_base64

        return selector, crop, view, b64_image
