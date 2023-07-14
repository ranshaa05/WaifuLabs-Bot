import json
from typing import Optional

import nextcord
from nextcord.ext import commands
import traceback

from cogs.admin_commands import AdminCommands
from logger import setup_logging
from screenshot import Screenshot
from site_navigator import SiteNavigator
from view import View

### Logging setup ###
log = setup_logging().log

### Bot setup ###
with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

TOKEN = config_data["bot_token"]


CLIENT = commands.Bot(intents=nextcord.Intents().all())

admin_commands = AdminCommands(CLIENT)
CLIENT.add_cog(admin_commands)

REQUIRED_PERMISSIONS = [
    "manage_messages",
    "send_messages",
    "add_reactions",
    "attach_files",
    "embed_links",
]


@CLIENT.event
async def on_ready():
    log.info("Bot Ready.")
    CLIENT.start_time = nextcord.utils.utcnow()
    await CLIENT.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/waifu")
    )
    admin_commands.validate_admins()


connected_users = []


@CLIENT.slash_command(description="Build-a-waifu!")
async def waifu(
    interaction: nextcord.Interaction,
    private: Optional[bool] = nextcord.SlashOption(
        description="Makes it so only you can see your waifus.",
        default=False,
        required=False,
    ),
):
    "Starts the bot."
    if not await check_permissions(interaction):
        return
    if interaction.user.id in connected_users:
        await interaction.response.send_message(
            "Whoops! One user cannot start me twice. You can continue or press ❌ to exit.",
            ephemeral=True,
            delete_after=10,
        )
        return

    connected_users.append(interaction.user.id)
    original_message = await interaction.response.send_message(
        "Hi there! I'm WaifuBot!\nI create waifus using <https://www.waifulabs.com>. Let's get started!\nYou'll be presented with 4 grids of waifus, each based on your previous choice. Click the waifu you like best or use these buttons:\n❌ to exit, ⬅ to undo, ➡ to skip forward, 🎲 to choose randomly, or 🔄 to refresh the grid.\n_(1/4)_",
        ephemeral=private,
    )
    navi = await SiteNavigator.create_navi()
    log.info(f"Browser started for user '{interaction.user.name}'.")

    View.stage[interaction.user.id] = 0
    while View.stage[interaction.user.id] < 4:
        if navi.page.isClosed():
            await original_message.edit(
                "Exiting...", delete_after=5, attachments=[], view=None
            )
            break
        else:
            await Screenshot(navi, interaction, original_message).save_send_screenshot()
        if View.stage[interaction.user.id] < 4 and not navi.page.isClosed():
            await original_message.edit(
                f"Okay! lets continue. Here's another grid for you to choose from:\n(_{View.stage[interaction.user.id] + 1}/4)_",
                view=None,
            )

    if not navi.page.isClosed():
        await Screenshot(navi, interaction, original_message).save_send_screenshot()
        await original_message.edit(
            content="Here's your waifu! Thanks for playing :slight_smile:"
        )
        await navi.browser.close()
        log.info(f"Browser closed for user '{interaction.user.name}', finished.")

    elif navi.page.isClosed() and navi.timed_out:
        log.info(f"Browser closed for user '{interaction.user.name}', timed out.")
        await original_message.edit(
            "Hey, anybody there? No? Okay, I'll shut down then :slight_frown:",
            delete_after=10,
            attachments=[],
            view=None,
        )

    else:
        log.info(f"Browser closed for user '{interaction.user.name}'")

    View.stage.pop(interaction.user.id, None)
    connected_users.remove(interaction.user.id)


@CLIENT.slash_command(description="Submit a bug report.")
async def feedback(interaction: nextcord.Interaction):
    "Link to the issues page."
    await interaction.response.send_message(
        """If you've encountered a bug or have a suggestion for Waifu Bot, please head over to the issues page on Github: <https://github.com/ranshaa05/WaifuLabs-Bot/issues>.
There, you can report bugs, suggest features, or ask for help with any issues you're having.
Thanks for helping us make Waifu Bot better! :slight_smile:""",
        ephemeral=True,
    )


async def check_permissions(interaction):
    "Checks if the bot has the required permissions."

    if isinstance(interaction.channel, nextcord.abc.GuildChannel):
        missing_permissions = []
        for permission in REQUIRED_PERMISSIONS:
            if not getattr(
                interaction.channel.permissions_for(interaction.guild.me), permission
            ):
                permission = permission.replace("_", " ").title()
                missing_permissions.append(permission)

        if missing_permissions:
            message = "Hey! I'm missing these permissions:\n{}".format(
                "\n".join(missing_permissions)
                + ".\nPlease give me these so I can work properly :slight_smile:"
            )
            await interaction.response.send_message(message, ephemeral=True)
            return False
        return True
    else:
        return True


@CLIENT.event
async def on_application_command_error(
    interaction: nextcord.Interaction, error: nextcord.DiscordException
):
    log.error(f"####### an error occured #######\n{error}")
    traceback.print_exception(type(error), error, error.__traceback__)

    err_name = type(error).__name__
    if not err_name in admin_commands.application_errors:
        admin_commands.application_errors[err_name] = 1
    else:
        admin_commands.application_errors[err_name] += 1


# TODO: run the bot for an extended period of time and see if any errors raise without being caught by on_application_command_error. if they do, add an identical on_error event to catch them.


if __name__ == "__main__":
    CLIENT.run(TOKEN)
