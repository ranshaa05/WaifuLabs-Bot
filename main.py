import nextcord
from nextcord.ext import commands

import json
from typing import Optional

from view import View
from site_navigator import SiteNavigator
from logger import setup_logging
from screenshot import Screenshot


### Logging setup ###
log = setup_logging().log

### Bot setup ###
with open("config.json") as config_file:
    config_data = json.load(config_file)

TOKEN = config_data["bot_token"]

ADMIN_IDS = config_data["admin_ids"]
ADMIN_SERVER_IDS = config_data["admin_server_ids"]

CLIENT = commands.Bot(intents=nextcord.Intents().all())

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
    await CLIENT.change_presence(
        activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="/waifu")
    )
    await check_admin_ids()


async def check_admin_ids():
    """Checks if the admin IDs and admin server IDs are valid."""
    if not ADMIN_IDS:
        log.error("No admin IDs were provided in config.json. 'show_servers' command will not work.")
    elif not ADMIN_SERVER_IDS:
        log.error("No admin server IDs were provided in config.json. 'show_servers' command will not work.")
    else:
        for user_id in ADMIN_IDS:
            user = nextcord.utils.get(CLIENT.users, id=user_id)
            if user is None:
                log.error(
                    f"Admin ID '{user_id}' is not a valid user ID. Please check your config.json file. 'show_servers' command will not work for that user."
                )

        for server_id in ADMIN_SERVER_IDS:
            guild = nextcord.utils.get(CLIENT.guilds, id=server_id)
            if guild is None:
                log.error(
                    f"Admin Server ID '{server_id}' is not a valid server ID. Please check your config.json file. 'show_servers' command will not work in that server."
                )


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
            delete_after=5,
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
            delete_after=5,
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


@CLIENT.slash_command(
    name="show_servers",
    description="Shows the list of servers the bot is in.",
    guild_ids=ADMIN_SERVER_IDS,
)
async def show_servers(
    interaction: nextcord.Interaction,
    private: Optional[bool] = nextcord.SlashOption(
        description="Makes it so only you can see the list.",
        default=True,
        required=False,
    ),
):
    "Shows the list of servers the bot is in."
    if interaction.user.id in ADMIN_IDS:
        servers = CLIENT.guilds
        server_list = "\n".join(
            [f"{i+1}. {server.name} ({server.id})" for i, server in enumerate(servers)]
        )
        total_servers = len(servers)
        embed = nextcord.Embed(
            title="Server List",
            description=f"Total Servers: {total_servers}\n{server_list}",
        )
        await interaction.response.send_message(embed=embed, ephemeral=private)
    else:
        await interaction.response.send_message(
            "You don't have permission to use this command. You must be an admin of this bot to use it.",
            ephemeral=True,
        )


if __name__ == "__main__":
    CLIENT.run(TOKEN)
