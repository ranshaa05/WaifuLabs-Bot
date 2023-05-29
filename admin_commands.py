import json
from typing import Optional

import nextcord
from nextcord.ext import commands

from logger import setup_logging

with open("config.json", "r") as config_file:
    config_data = json.load(config_file)


class AdminCommands(commands.Cog):
    ADMIN_IDS = config_data["admin_ids"]
    ADMIN_SERVER_IDS = config_data["admin_server_ids"]
    client = (
        commands.Bot()
    )  # Placeholder to make  the linter happy. this is used for the decorators

    def __init__(self, client):
        self.log = setup_logging().log
        AdminCommands.client = client

    def validate_admins(self):
        "Checks if the admin IDs and admin server IDs are valid."
        for user_id in AdminCommands.ADMIN_IDS:
            user = self.client.get_user(user_id)
            if user is None:
                self.log.error(
                    f"Admin ID '{user_id}' is not a valid user ID. Please check your config.json file. 'show_servers' command will not work for that user."
                )

        for server_id in AdminCommands.ADMIN_SERVER_IDS:
            guild = nextcord.utils.get(self.client.guilds, id=server_id)
            if guild is None:
                self.log.error(
                    f"Admin Server ID '{server_id}' is not a valid server ID. Please check your config.json file. 'show_servers' command will not work in that server."
                )

    @client.slash_command(
        name="manage_admins",
        description="Adds or removes a user from the admin list.",
        guild_ids=ADMIN_SERVER_IDS,
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
        private: Optional[bool] = nextcord.SlashOption(
            description="Whether to make the response private.",
            default=True,
            required=False,
        ),
    ):
        "Adds or removes a user from the admin list."
        if interaction.user.id in AdminCommands.ADMIN_IDS:
            if (
                add_or_remove == "remove"
                and user.id in AdminCommands.ADMIN_IDS  # <--- This line is the problem
                and len(AdminCommands.ADMIN_IDS) == 1
            ):
                await interaction.response.send_message(
                    "You cannot remove the last admin.", ephemeral=private
                )
                self.log.info(
                    f"{interaction.user.name}: Tried to remove the last admin, but was denied."
                )
                return
            elif user.id in AdminCommands.ADMIN_IDS and add_or_remove == "add":
                await interaction.response.send_message(
                    f"'{user.name}' is already an admin.", ephemeral=private
                )
                self.log.info(
                    f"{interaction.user.name}: Tried to add user '{user.name}' to the admin list, but they are already an admin."
                )
                return
            elif user.id not in AdminCommands.ADMIN_IDS and add_or_remove == "remove":
                await interaction.response.send_message(
                    f"'{user.name}' is not an admin.", ephemeral=private
                )
                self.log.info(
                    f"{interaction.user.name}: Tried to remove user '{user.name}' from the admin list, but they are not an admin."
                )
                return
            elif add_or_remove == "add":
                AdminCommands.ADMIN_IDS.append(user.id)
                json.dump(config_data, open("config.json", "w"), indent=4)

            elif add_or_remove == "remove":
                AdminCommands.ADMIN_IDS.remove(user.id)
                json.dump(config_data, open("config.json", "w"), indent=4)

            await interaction.response.send_message(
                f"User '{user.name}' was {'added to' if add_or_remove == 'add' else 'removed from'} the admin list.",
                ephemeral=private,
            )
            self.log.info(
                f"{interaction.user.name}: User '{user.name}' was {'added to' if add_or_remove == 'add' else 'removed from'} the admin list."
            )

        else:
            await interaction.response.send_message(
                "You do not have permission to perform this action. You must be an admin of this bot to use it.",
                ephemeral=private,
            )

    @client.slash_command(
        name="show_servers",
        description="Shows the list of servers the bot is in.",
        guild_ids=ADMIN_SERVER_IDS,
    )
    async def show_servers(
        self,
        interaction: nextcord.Interaction,
        private: Optional[bool] = nextcord.SlashOption(
            description="Whether to make the list private.",
            default=True,
            required=False,
        ),
    ):
        "Shows the list of servers the bot is in."
        if interaction.user.id in AdminCommands.ADMIN_IDS:
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
                description=f"Total Servers: {total_servers}\n{server_list}",
                color=0x00FF00,
            )
            await interaction.response.send_message(embed=embed, ephemeral=private)
        else:
            await interaction.response.send_message(
                "You don't have permission to use this command. You must be an admin of this bot to use it.",
                ephemeral=True,
            )
