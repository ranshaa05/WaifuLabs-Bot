import nextcord


class View(nextcord.ui.View):
    stage = {}
    _number_emoji_list = [
        "1️⃣",
        "2️⃣",
        "3️⃣",
        "4️⃣",
        "5️⃣",
        "6️⃣",
        "7️⃣",
        "8️⃣",
        "9️⃣",
        "🔟",
        "1️⃣🇮",
        "1️⃣2️⃣",
        "1️⃣3️⃣",
        "1️⃣4️⃣",
        "1️⃣5️⃣",
    ]

    def __init__(self, navi, interaction, co_operator, session_id):
        super().__init__(timeout=120)
        self.navi = navi
        self.interaction = interaction
        self.co_operator = co_operator
        self.session_id = session_id
        self.current_label = "❓"  # placeholder

        button_groups = [
            {"labels": [str(i) for i in range(1, 5)], "style": nextcord.ButtonStyle.blurple},
            {"labels": ["⬅"], "style": nextcord.ButtonStyle.green, "disabled_at_stage_0": True},
            {"labels": [str(i) for i in range(5, 9)], "style": nextcord.ButtonStyle.blurple},
            {"labels": ["➡"], "style": nextcord.ButtonStyle.green, "disabled_at_stage_0": True},
            {"labels": [str(i) for i in range(9, 13)], "style": nextcord.ButtonStyle.blurple},
            {"labels": ["🎲"], "style": nextcord.ButtonStyle.green},
            {"labels": [str(i) for i in range(13, 16)], "style": nextcord.ButtonStyle.blurple},
            {"labels": ["🔄"], "style": nextcord.ButtonStyle.grey},
            {"labels": ["❌"], "style": nextcord.ButtonStyle.red},
        ]

        for group in button_groups:
            style = group["style"]
            disabled_at_stage_0 = group.get("disabled_at_stage_0", False)
            for label in group["labels"]:
                button = nextcord.ui.Button(
                    custom_id=label,
                    label=label,
                    style=style,
                    disabled=(self.stage[session_id] == 0 and disabled_at_stage_0),
                )
                button.callback = self._button_callback
                self.add_item(button)

    async def interaction_check(self, interaction: nextcord.Interaction):
        """
        Checks if the user interacting with the view is authorized.
        """
        is_author = interaction.user.id == self.interaction.user.id
        is_co_op_user = self.co_operator and interaction.user == self.co_operator
        is_co_op_role = (
            self.co_operator
            and isinstance(self.co_operator, nextcord.Role)
            and self.co_operator in interaction.user.roles
        )

        authorized = is_author or is_co_op_user or is_co_op_role
        if not authorized:
            await interaction.response.send_message(
                "You don't have permission to use these buttons.", ephemeral=True, delete_after=5
            )

        return authorized

    async def _button_callback(self, interaction: nextcord.Interaction):
        """Handles all button clicks."""
        label = interaction.data["custom_id"]
        await self._button_logic(label)

        if label.isnumeric():
            self.current_label = self._number_emoji_list[int(label) - 1]
        else:
            self.current_label = label

        self.stop()

    async def _button_logic(self, label: str):
        """Runs the appropriate functions based on the button label."""
        actions = {
            "⬅": (self.navi.undo, -1),
            "➡": (self.navi.keep, 1),
            "🎲": (self.navi.rand, 1),
            "🔄": (self.navi.refresh, 0),
            "❌": (self.navi.exit, 0),
        }

        if label.isnumeric():
            await self.navi.click_by_index(int(label))
            View.stage[self.session_id] += 1
        elif label in actions:
            action, stage_change = actions[label]
            await action()
            View.stage[self.session_id] += stage_change

    async def on_timeout(self):
        await self.navi.page_timeout()
