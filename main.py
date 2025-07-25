import json
import os
import traceback
from typing import Optional

import nextcord
from nextcord.ext import commands
from uuid import uuid4

from cogs.admin_commands import AdminCommands
from logger import setup_logging
from screenshot import ScreenshotHandler
from site_navigator import PageNavigator
from view import View

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
        description="Allows other users to help you build your waifu.",
        default=None,
        required=False,
    ),
    privacy: Optional[bool] = nextcord.SlashOption(
        name="private",
        description="Makes it so only you can see your waifus.",
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

    if not await check_permissions(interaction):
        return
    if interaction.user.id in connected_users:
        await interaction.response.send_message(
            "Whoops! One user cannot start me twice at the same time."
            "You can continue making your waifu or press ❌ to exit.",
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
            "I create waifus using [waifulabs.com](https://www.waifulabs.com). Let's get started!"
            "\n* You'll be presented with 4 grids of waifus, each based on your previous choice. "
            "\n* Click the number corresponding to the waifu you like best in each grid or use these buttons:"
            "\n❌ to exit, ⬅ to undo, ➡ to skip a stage, 🎲 to choose randomly, or 🔄 to refresh the grid."
            "\n_(Progress: 1/4)_"
        ),
        ephemeral=privacy,
    )
    navi = await PageNavigator.create_navi()
    log.info(f"Page started for user '{interaction.user.name}'. {collaborator_info}")

    handler = ScreenshotHandler(navi, interaction, co_operator)
    View.stage[session_id] = 0
    while View.stage[session_id] < 4 and not navi.page.isClosed():
        await handler.save_send_screenshot(session_id, original_message)
        if View.stage[session_id] <= 3:
            try:    #in case the message was deleted
                await original_message.edit(
                    (
                        "Okay! lets continue. Here's another grid for you to choose from:\n"
                        f"(_Progress: {View.stage[session_id] + 1}/4)_"
                    ),
                    view=None,
                )
            except nextcord.errors.NotFound:
                break

    #final images
    if not navi.page.isClosed():
        await handler.save_send_screenshot(session_id, original_message)
        await original_message.edit(
            content="Here's your waifu! Thanks for playing :slight_smile:"
        )
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

    View.stage.pop(session_id, None)
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


REQUIRED_PERMISSIONS = ["view_channel", "manage_messages", "add_reactions"]

async def check_permissions(interaction):
    """Checks if the bot has the required permissions and notifies the user if not."""

    if isinstance(interaction.channel, nextcord.abc.GuildChannel):
        bot_role = interaction.guild.me.top_role
        bot_channel_permissions = interaction.channel.permissions_for(interaction.guild.me)

        missing_permissions = {
            "role": [],
            "channel": []
        }

        for permission in REQUIRED_PERMISSIONS:
            if not getattr(bot_role.permissions, permission):
                missing_permissions["role"].append(permission.replace("_", " ").title())
            if not getattr(bot_channel_permissions, permission):
                missing_permissions["channel"].append(permission.replace("_", " ").title())

        if missing_permissions["role"] or missing_permissions["channel"]:
            embed = nextcord.Embed(
                title="⚠️ __Missing Permissions__",
                description="Hey! I'm missing these permissions:",
                color=0xFF0000,
            )
            for permission_type, permissions in missing_permissions.items():
                if permissions:
                    embed.add_field(
                        name=f"❌ Missing in {permission_type}:",
                        value="\n".join(permissions),
                        inline=True,
                    )
            embed.set_footer(
                text="Please grant me these permissions so i can work properly!🙏"
            )

            await interaction.response.send_message(embed=embed)
            return False
    return True



@CLIENT.event
async def on_application_command_error(interaction: nextcord.Interaction, error: nextcord.DiscordException):
    """Handles errors that occur in application commands."""

    log.error(f"####### an error occured #######\n{error}")
    traceback.print_exception(type(error), error, error.__traceback__)

    error_message = str(error).split(":")[1]
    if error_message not in admin_commands.application_errors:
        admin_commands.application_errors[error_message] = 1
    else:
        admin_commands.application_errors[error_message] += 1


if __name__ == "__main__":
    CLIENT.run(TOKEN)
