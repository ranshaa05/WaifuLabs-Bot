import nextcord


REQUIRED_PERMISSIONS = ["view_channel", "manage_messages", "add_reactions"]


async def check_permissions(interaction):
    """Checks if the bot has the required permissions and notifies the user if not."""

    if isinstance(interaction.channel, nextcord.abc.GuildChannel):
        bot_role = interaction.guild.me.top_role
        bot_channel_permissions = interaction.channel.permissions_for(interaction.guild.me)

        missing_permissions = {"role": [], "channel": []}

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
            embed.set_footer(text="Please grant me these permissions so i can work properly!🙏")

            await interaction.response.send_message(embed=embed)
            return False
    return True
