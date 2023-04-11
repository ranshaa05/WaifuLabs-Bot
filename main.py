import os
import nextcord
from nextcord.ext import commands

from view import View
from site_navigator import SiteNavigator
from logger import setup_logging
from screenshot import Screenshot

log = setup_logging().log

TOKEN_FILE = "token.txt"
if not os.path.exists(TOKEN_FILE):
    log.error(f"Error: {TOKEN_FILE} not found in program directory.")
    exit()

with open(TOKEN_FILE, "r") as file:
    TOKEN = file.read().strip()

CLIENT = commands.Bot(command_prefix="$", intents=nextcord.Intents().all())

@CLIENT.event
async def on_ready():
    log.info("Bot Ready.")
    await CLIENT.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/waifu"))
    
connected_users = []

@CLIENT.slash_command(description="Build-a-waifu!")
async def waifu(interaction: nextcord.Interaction):
    "Starts the bot."
    if not await check_permissions(interaction):
        return
    if interaction.user.id in connected_users:
        await interaction.response.send_message("Whoops! One user cannot start me twice. You can continue or press ❌ to exit.", ephemeral=True, delete_after=5)
        return

    connected_users.append(interaction.user.id)
    original_message = await interaction.response.send_message("Hi there! I'm WaifuBot, and I can create waifus using <https://www.waifulabs.com>. Let's get started!\nYou'll be presented with 4 grids of waifus, each based on your previous choice. Tell me which waifu you like or use the buttons below:\n❌ to exit, ⬅ to undo, ➡ to continue your current waifu, 🎲 to choose randomly, or 🔄 to refresh the grid.")
    navi = await SiteNavigator.create_navi()
    log.info(f"Browser started for user '{interaction.user.name}'.")

    View.stage[interaction.user.id] = 0
    while View.stage[interaction.user.id] < 4: #TODO: this is where i need to  tell the user they cant undo/keep waifu if they havent chosen one yet. figure this out.
        if navi.page.isClosed():
            await original_message.edit("Exiting...", delete_after=5, attachments=[], view=None)
            break
        else:
            await Screenshot(navi, interaction, original_message).save_send_screenshot()
        if View.stage[interaction.user.id] < 4 and not navi.page.isClosed():
            await original_message.edit("Okay! lets continue. Here's another grid for you to choose from:", view=None)

    if not navi.page.isClosed():
        await Screenshot(navi, interaction, original_message).save_send_screenshot()
        await original_message.edit(content="Here's your waifu! Thanks for playing :slight_smile:")
        await navi.browser.close()
        log.info(f"Browser closed for user '{interaction.user.name}', finished.")
        
    elif navi.page.isClosed() and navi.timed_out:
        log.info(f"Browser closed for user '{interaction.user.name}', timed out.")
        await original_message.edit("Hey, anybody there? No? Okay, I'll shut down then :slight_frown:", delete_after=5, attachments=[], view=None)

    else:
        log.info(f"Browser closed for user '{interaction.user.name}'")
        
        View.stage.pop(interaction.user.id, None)
        connected_users.remove(interaction.user.id)


async def check_permissions(interaction):
    required_permissions = ["manage_messages", "send_messages", "add_reactions", "attach_files", "embed_links"]
    missing_permissions = []
    for permission in required_permissions:
        if not getattr(interaction.channel.permissions_for(interaction.guild.me), permission):
            missing_permissions.append(permission)

    if missing_permissions:
        message = "The following permissions are missing: {}".format(", ".join(missing_permissions))
        await interaction.response.send_message(message)
        return False
    return True
 

if __name__ == "__main__":
    CLIENT.run(TOKEN)

