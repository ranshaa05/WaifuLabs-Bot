import json
from typing import Optional

import nextcord
from nextcord.ext import commands
import traceback

from cogs.admin_commands import AdminCommands
from logger import setup_logging
from screenshot import Screenshot
from site_navigator import PageNavigator
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

REQUIRED_PERMISSIONS = ["view_channel", "manage_messages", "add_reactions"]


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
    navi = await PageNavigator.create_navi()
    log.info(f"Page started for user '{interaction.user.name}'.")

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
        await navi.page.close()
        log.info(f"Page closed for user '{interaction.user.name}', finished.")

    elif navi.page.isClosed() and navi.timed_out:
        log.info(f"Page closed for user '{interaction.user.name}', timed out.")
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
    "Checks if the bot has the required permissions and notifies the user if not."

    if isinstance(interaction.channel, nextcord.abc.GuildChannel):
        role_missing_permissions = []
        bot_role = interaction.guild.me.top_role
        for permission in REQUIRED_PERMISSIONS:
            if not getattr(bot_role.permissions, permission):
                permission = permission.replace("_", " ").title()
                role_missing_permissions.append(permission)

        channel_missing_permissions = []
        for permission in REQUIRED_PERMISSIONS:
            if not getattr(
                interaction.channel.permissions_for(interaction.guild.me), permission
            ):
                permission = permission.replace("_", " ").title()
                channel_missing_permissions.append(permission)

        if role_missing_permissions or channel_missing_permissions:
            embed = nextcord.Embed(
                title="⚠️ __Missing Permissions__",
                description="Hey! I'm missing these permissions:",
                color=0xFF0000,
            )
            if role_missing_permissions:
                embed.add_field(
                    name="❌ Missing in role:",
                    value="\n".join(role_missing_permissions),
                    inline=True,
                )
            if channel_missing_permissions:
                embed.add_field(
                    name="❌ Missing in channel:",
                    value="\n".join(channel_missing_permissions),
                    inline=True,
                )
            embed.set_footer(
                text="Please grant me these permissions so i can work properly!🙏"
            )

            await interaction.response.send_message(embed=embed)
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

    error_message = str(error).split(":")[1]
    if not error_message in admin_commands.application_errors:
        admin_commands.application_errors[error_message] = 1
    else:
        admin_commands.application_errors[error_message] += 1


# TODO: run the bot for an extended period of time and see if any errors raise without being caught by on_application_command_error. if they do, add an identical on_error event to catch them.


if __name__ == "__main__":
    CLIENT.run(TOKEN)
