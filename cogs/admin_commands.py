from typing import Optional

import nextcord
from nextcord.ext import commands

from logger import setup_logging
from .config_manager import load_config, save_admin_ids, get_admin_ids
from .admin_validation import validate_admins
from .permissions import check_permission # Import the global check_permission

config_data = load_config()

class AdminCommands(commands.Cog):
    admin_server_ids = config_data["admin_server_ids"]
    application_errors = {}
    runtime_errors = {}
    #client = (
    #    commands.Bot()
    #)  # Placeholder to make  the linter happy. this is used for the decorators

    def __init__(self, client):
        self.log = setup_logging().log
        AdminCommands.client = client
        self._ready = False

    @commands.Cog.listener()
    async def on_ready(self):
        """When the bot is ready, validate the admin and server IDs."""
        if not self._ready:
            await validate_admins(AdminCommands.client)
            self._ready = True

    @nextcord.slash_command(
        name="error_count",
        guild_ids=admin_server_ids,
    )
    async def error_count(
        self,
        interaction: nextcord.Interaction,
        privacy: Optional[bool] = nextcord.SlashOption(
            name="private",
            description="Whether to make the response private.",
            default=True,
            required=False,
        ),
    ):
        "Counts each type of error the bot encountered since last restart individually"
        if await check_permission(interaction): # Use the global check_permission
            application_errors = AdminCommands.application_errors
            runtime_errors = AdminCommands.runtime_errors

            app_dict_str = ""
            run_dict_str = ""

            # formatting the dicts into strings
            if application_errors:
                for key, value in application_errors.items():
                    app_dict_str += f"{key}: {value}\n"
            if runtime_errors:
                for key, value in runtime_errors.items():
                    run_dict_str += f"{key}: {value}\n"

            if app_dict_str or run_dict_str:
                embed = nextcord.Embed(
                    title="Error count",
                    description=f"""
                    **__Application errors:__**
                    {app_dict_str if app_dict_str else 'No application errors have occurred'}

                    **__Runtime errors:__**
                    {run_dict_str if run_dict_str else 'No runtime errors have occurred'}
                    """,
                    color=nextcord.Color.red(),
                )
                await interaction.response.send_message(embed=embed, ephemeral=privacy)
            else:
                await interaction.response.send_message(
                    "No errors have occurred yet.", ephemeral=True
                )

    @nextcord.slash_command(
        name="manage_admins",
        guild_ids=admin_server_ids,
    )
    async def manage_admins(
        self,
        interaction: nextcord.Interaction,
        add_or_remove: str = nextcord.SlashOption(
            description="Whether to add or remove a user from the admin list.",
            choices=["add", "remove"],
            required=True,
        ),
        user: nextcord.Member = nextcord.SlashOption(
            description="The user to perform the action on.",
            required=True,
        ),
        privacy: Optional[bool] = nextcord.SlashOption(
            name="private",
            description="Whether to make the response private.",
            default=True,
            required=False,
        ),
    ):
        "Adds or removes a user from the admin list."
        if await check_permission(interaction): # Use the global check_permission
            admin_ids = get_admin_ids()
            if (
                add_or_remove == "remove"
                and len(admin_ids) == 1 and user.id in admin_ids
            ):
                await interaction.response.send_message(
                    "You cannot remove the last admin.", ephemeral=privacy
                )
                self.log.info(
                    f"{interaction.user.name}: Tried to remove themselves from the admin list, but they are the last admin, so they were denied."
                )
                return
            elif (
                add_or_remove == "add"
                and user.id in admin_ids
            ):
                await interaction.response.send_message(
                    f"'{user.name}' is already an admin.", ephemeral=privacy
                )
                self.log.info(
                    f"{interaction.user.name}: Tried to add user '{user.name}' to the admin list, but they are already an admin."
                )
                return
            elif (
                add_or_remove == "remove"
                and user.id not in admin_ids
            ):
                await interaction.response.send_message(
                    f"'{user.name}' is not an admin.", ephemeral=privacy
                )
                self.log.info(
                    f"{interaction.user.name}: Tried to remove user '{user.name}' from the admin list, but they are not an admin."
                )
                return

            elif add_or_remove == "add":
                admin_ids.append(user.id)
                save_admin_ids(admin_ids)

            elif add_or_remove == "remove":
                admin_ids.remove(user.id)
                save_admin_ids(admin_ids)

            await interaction.response.send_message(
                f"User '{user.name}' was {'added to' if add_or_remove == 'add' else 'removed from'} the admin list.",
                ephemeral=privacy,
            )
            self.log.info(
                f"{interaction.user.name}: User '{user.name}' was {'added to' if add_or_remove == 'add' else 'removed from'} the admin list."
            )

    @nextcord.slash_command(
        name="show_servers",
        guild_ids=admin_server_ids,
    )
    async def show_servers(
        self,
        interaction: nextcord.Interaction,
        privacy: Optional[bool] = nextcord.SlashOption(
            name="private",
            description="Whether to make the list private.",
            default=True,
            required=False,
        ),
    ):
        "Shows the list of servers the bot is in."
        if await check_permission(interaction): # Use the global check_permission
            servers = self.client.guilds
            server_list = "\n".join(
                [
                    f"{i+1}. {server.name} ({server.id})"
                    for i, server in enumerate(servers)
                ]
            )
            total_servers = len(servers)
            embed = nextcord.Embed(
                title="Server List",
                description=f"**__Total Servers: {total_servers}__**\n{server_list}",
                color=0x00FF00,
            )
            await interaction.response.send_message(embed=embed, ephemeral=privacy)

    @nextcord.slash_command(
        name="uptime",
        guild_ids=admin_server_ids,
    )
    async def uptime(
        self,
        interaction: nextcord.Interaction,
        privacy: Optional[bool] = nextcord.SlashOption(
            name="private",
            description="Whether to make the response private.",
            default=True,
            required=False,
        ),
    ):
        "Shows how long the bot has been running for since the last restart."
        if await check_permission(interaction): # Use the global check_permission
            uptime = nextcord.utils.utcnow() - self.client.start_time
            await interaction.response.send_message(
                "Uptime: " + str(uptime).split(".")[0], ephemeral=privacy
            )

    @nextcord.slash_command(
        name="api_latency",
        guild_ids=admin_server_ids,
    )
    async def api_latency(
        self,
        interaction: nextcord.Interaction,
        privacy: Optional[bool] = nextcord.SlashOption(
            name="private",
            description="Whether to make the response private.",
            default=True,
            required=False,
        ),
    ):
        "Shows the bot's API latency."
        if await check_permission(interaction): # Use the global check_permission
            await interaction.response.send_message(
                f"API Latency: {round(self.client.latency * 1000)}ms", ephemeral=privacy
            )


def setup(client):
    client.add_cog(AdminCommands(client))
