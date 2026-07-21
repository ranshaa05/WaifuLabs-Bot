from .config_manager import get_admin_ids, get_admin_server_ids


async def check_permission(interaction):
    "Sends a message saying the user doesn't have permission to use the command."
    admin_server_ids = get_admin_server_ids()

    if not interaction.guild or interaction.guild.id not in admin_server_ids:
        await interaction.response.send_message(
            "This command may only be used in a configured admin server.",
            ephemeral=True,
        )
        return False

    if interaction.user.id not in get_admin_ids():
        await interaction.response.send_message(
            "You do not have permission to use this command since you are not an admin of this bot.",
            ephemeral=True,
        )
        return False

    return True
