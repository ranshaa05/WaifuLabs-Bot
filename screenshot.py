import asyncio
import base64 as b64
from io import BytesIO

from PIL import Image
import nextcord

from view import View


class ScreenshotHandler:
    """Handles the screenshotting and sending of the screenshot."""
    def __init__(self, navi, interaction, co_operator):
        self.navi = navi
        self.interaction = interaction
        self.co_operator = co_operator
        self.view = None

    async def save_send_screenshot(self, session_id, original_message):
        """saves a screenshot of the current page and sends it to the user."""
        await self.navi.wait_for_not_load_screen()

        (
            selector,
            crop,
            self.view,
            b64_string,
        ) = await self._get_screenshot_info_by_stage(View.stage[session_id], session_id)

        if not b64_string:  # For intermediate stages
            image_bytes = await self.navi.screenshot(selector)
        else:  # For the final stage, the image is a base64 string that needs decoding.
            image_bytes = b64.b64decode(b64_string)

        with Image.open(BytesIO(image_bytes)) as pil_image:
            if crop:
                width, height = pil_image.size
                pil_image = pil_image.crop((0, height - 630, width, height))


            with BytesIO() as byte_arr:
                pil_image.save(byte_arr, format="WEBP")
                byte_arr.seek(0)

                file = nextcord.File(byte_arr, filename="image.webp")
                await original_message.edit(
                    file=file,
                    view=self.view if self.view else None,
                )

        original_message = await original_message.fetch()

        asyncio.create_task(self.remove_reactions(original_message))
        if self.view:
            await self.view.wait()
            asyncio.create_task(self.add_reaction(original_message))

    def _is_message_reactable(self, message: nextcord.Message) -> bool:
        """
        Checks if a message can have reactions added to it.
        Reactions are only possible on non-ephemeral messages in guild channels.
        """
        # An InteractionMessage (from an ephemeral response) is not a full Message object and cannot have reactions.
        if not isinstance(message, nextcord.Message):
            return False
        
        return isinstance(message.channel, nextcord.abc.GuildChannel) and not message.flags.ephemeral

    async def remove_reactions(self, original_message):
        """Removes all reactions from the original message."""
        if self._is_message_reactable(original_message):
            await original_message.clear_reactions()

    async def add_reaction(self, original_message):
        """Adds a reaction to the original message based on the button pressed in the view."""
        if self._is_message_reactable(original_message):
            if self.view.current_label == "❓":
                return
            # if the label is a single emoji (3 chars), it can be added directly.
            # if it is a string of emojis, it must be split into chunks of 3 chars.
            elif len(self.view.current_label) > 3:
                for emoji in [
                    self.view.current_label[i : i + 3]
                    for i in range(0, len(self.view.current_label), 3)
                ]:
                    await original_message.add_reaction(emoji)
            else:
                await original_message.add_reaction(self.view.current_label)
            await original_message.add_reaction("⏳")

    async def _get_screenshot_info_by_stage(self, stage, session_id):
        """Returns the selector, crop, view, and base64 image based on the stage of the grid."""
        stage_configs = {
            0: {"selector": ".waifu-grid", "crop": False, "view": True},
            1: {"selector": ".waifu-container", "crop": True, "view": True},
            2: {"selector": ".waifu-container", "crop": True, "view": True},
            3: {"selector": ".waifu-container", "crop": True, "view": True},
        }

        if stage in stage_configs:
            config = stage_configs[stage]
            selector = config["selector"]
            crop = config["crop"]
            view = View(self.navi, self.interaction, self.co_operator, session_id) if config["view"] else None
            b64_string = None
        else:
            # this is a bit of a hack, but it works
            # the final image is not a screenshot, but a base64 image taken from the element's src attribute
            # this is done because of an issue with pyppeteer's screenshot func
            selector = None
            crop = False
            view = None
            await self.navi.wait_for_final_image()

            final_image_element = await self.navi.page.querySelector(".waifu-preview > img")
            final_image_url = await self.navi.page.evaluate("(element) => element.src", final_image_element)
            b64_string = final_image_url.split(",")[1]
    
        return selector, crop, view, b64_string
