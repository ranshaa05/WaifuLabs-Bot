import json
import os
from typing import Optional

import nextcord
from nextcord.ext import commands
from uuid import uuid4

from cogs.admin_commands import AdminCommands
from logger import setup_logging
from screenshot import ScreenshotHandler
from site_navigator import PageNavigator
from view import View
from permissions import check_permissions

### Logging setup ###
log = setup_logging().log

### Bot setup ###
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")
with open(config_path, "r") as config_file:
    config_data = json.load(config_file)

TOKEN = config_data["bot_token"]

CLIENT = commands.Bot(intents=nextcord.Intents().all())

CLIENT.add_cog(AdminCommands(CLIENT))



@CLIENT.event
async def on_ready():
    log.info("Bot Ready.")
    CLIENT.start_time = nextcord.utils.utcnow()
    await CLIENT.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/waifu")
    )


connected_users = []


@CLIENT.slash_command(description="Build-a-waifu!")
async def waifu(
    interaction: nextcord.Interaction,
    co_operator: nextcord.Mentionable = nextcord.SlashOption(
        name="co-op",
        description="Allows other users to help you build your character.",
        default=None,
        required=False,
    ),
    privacy: Optional[bool] = nextcord.SlashOption(
        name="private",
        description="Makes it so only you can see your characters.",
        default=False,
        required=False,
    ),
):
    """Starts the bot."""
    if co_operator and privacy:
        await interaction.response.send_message(
            "Whoops! You cannot use co-op mode and private mode at the same time.",
            ephemeral=True,
            delete_after=5,
        )
        return

    #check weather bot should start or not 
    if not await check_permissions(interaction):
        return
    if interaction.user.id in connected_users:
        await interaction.response.send_message(
            "Whoops! One user cannot start me twice at the same time."
            "You can continue making your character or press ❌ to exit.",
            ephemeral=True,
            delete_after=10,
        )
        return

    connected_users.append(interaction.user.id)

    session_id = uuid4()
    if co_operator:
        collaborator_type = 'Role' if isinstance(co_operator, nextcord.Role) else 'User'
        collaborator_info = f'Co-operator: {co_operator}. Co-operator type: ({collaborator_type})'
    else:
        collaborator_info = ''

    original_message = await interaction.response.send_message(
        (
            "Hi there! I'm WaifuBot!\n"
            "I create characters using [waifulabs.com](https://www.waifulabs.com). Let's get started!"
            "\n* You'll be presented with 4 grids of characters, each based on your previous choice. "
            "\n* Click the number corresponding to the character you like best in each grid or use these buttons:"
            "\n❌ to exit, ⬅ to undo, ➡ to skip a stage, 🎲 to choose randomly, or 🔄 to refresh the grid."
            "\n_(Progress: 1/4)_"
        ),
        ephemeral=privacy,
    )
    navi = await PageNavigator.create_navi()
    if navi is None:
        await original_message.edit(
            "Whoops! I'm having trouble connecting to the server right now.\n"
            "Please try again later.\n"
            "For now, you can use the official site instead: [waifulabs.com](https://www.waifulabs.com)",
            delete_after=60
        )
        connected_users.remove(interaction.user.id)
        return

    log.info(f"Page started for user '{interaction.user.name}'. {collaborator_info}")

    screenshot_handler = ScreenshotHandler(navi, interaction, co_operator)

    View.stage.setdefault(session_id, 0)
    view_instance = View(navi, interaction, co_operator, session_id)
    while view_instance.stage[session_id] < 4 and not navi.page.isClosed():
        await screenshot_handler.save_send_screenshot(session_id, original_message)
        try:
            if view_instance.stage[session_id] <= 3:
                    await original_message.edit(
                        (
                            "Okay! lets continue. Here's another grid for you to choose from:\n"
                            f"(_Progress: {view_instance.stage[session_id] + 1}/4)_"
                        ),
                        view=None,
                    )

            # final image
            else:
                await original_message.edit(
                content="Here's your character! Thanks for playing :slight_smile:"
            )
                await screenshot_handler.save_send_screenshot(session_id, original_message)
            
        except nextcord.errors.NotFound:    # in case the message gets deleted, and timeout occurs.
            break

    # Cleanup
    if not navi.page.isClosed():
        await navi.page.close()
        log.info(
            f"Page closed for user '{interaction.user.name}', finished. {collaborator_info}"
        )

    elif navi.timed_out:
        log.info(
            f"Page closed for user '{interaction.user.name}', timed out. {collaborator_info}")
        try:
            await original_message.edit(
                "Hey, anybody there? No? Okay, I'll shut down then :slight_frown:",
                delete_after=10,
                attachments=[],
                view=None,
            )
        except nextcord.errors.HTTPException:
            pass
    else:
        try:
            await original_message.edit(
                "Exiting...", delete_after=5, attachments=[], view=None
            )
        except nextcord.errors.HTTPException:
            pass
        log.info(
            f"Page closed for user '{interaction.user.name}'. {collaborator_info}")

    connected_users.remove(interaction.user.id)


@CLIENT.slash_command(description="Submit a bug report.")
async def feedback(interaction: nextcord.Interaction):
    """Link to the issues page."""
    await interaction.response.send_message(
        ("If you've encountered a bug or have a suggestion for Waifu Bot, "
         "please head over to the issues page on [Github](<https://github.com/ranshaa05/WaifuLabs-Bot/issues).\n"
         "There, you can report bugs, suggest features, or ask for help with "
         "any issues you're having.\n"
         "Thanks for helping us make Waifu Bot better! :slight_smile:"),
        ephemeral=True
        )


if __name__ == "__main__":
    CLIENT.run(TOKEN)
