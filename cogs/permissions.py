from .config_manager import get_admin_ids

async def check_permission(interaction):
    "Sends a message saying the user doesn't have permission to use the command."
    if not interaction.user.id in get_admin_ids():
        await interaction.response.send_message(
            "You do not have permission to use this command since you are not an admin of this bot.",
            ephemeral=True,
        )
        return False
    else:
        return True