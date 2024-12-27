import nextcord


class View(nextcord.ui.View):
    stage = {}

    def __init__(self, navi, interaction, co_operator, session_id):
        super().__init__(timeout=120)
        self.buttons = []
        self.navi = navi
        self.interaction = interaction
        self.current_label = "❓"  # placeholder
        self.label_list = []
        self.color_list = []
        emoji_label_list = ["⬅", "➡", "🎲", "🔄", "❌"]
        number_emoji_list = [
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

        # determine color for each button
        for i, emoji in enumerate(emoji_label_list[:3]):
            self.color_list += [nextcord.ButtonStyle.blurple] * 4 + [nextcord.ButtonStyle.green]
            self.label_list += [str(i) for i in range((i * 4) + 1, (i * 4) + 5)] + [emoji]

        self.color_list += [nextcord.ButtonStyle.blurple] * 3 + [nextcord.ButtonStyle.grey, nextcord.ButtonStyle.red]
        self.label_list += [str(i) for i in range(13, 16)] + emoji_label_list[-2:]

        for label, style in zip(self.label_list, self.color_list):  # make the buttons
            button = nextcord.ui.Button(
                custom_id=label,
                label=label,
                style=style,
                disabled=True
                if self.stage[session_id] == 0
                and (label == "⬅" or label == "➡")
                else False,
            )

            async def button_function(interaction):
                label = interaction.data[
                    "custom_id"
                ]  # sets label to the label of the button that was pressed.
                await self.button_logic(label, interaction.user, co_operator, session_id)
                if label.isnumeric():
                    label = number_emoji_list[
                        int(label) - 1
                    ]  # converts the label into an emoji if it is a number.
                self.current_label = label  # used to add the emoji to the message to show the what the user selected.

            button.callback = button_function
            self.add_item(button)

    async def button_logic(self, label, interactor, co_operator, session_id):
        """run the appropriate functions based on the label of the button that was pressed."""
        if (
            interactor.id == self.interaction.user.id
            or interactor == co_operator
            or co_operator in interactor.roles
        ):
            if label.isnumeric():
                await self.navi.click_by_index(int(label))
                View.stage[session_id] += 1
            elif label == "❌":
                await self.navi.exit()
            elif label == "🎲":
                await self.navi.rand()
                View.stage[session_id] += 1
            elif label == "🔄":
                await self.navi.refresh()
            if label == "⬅":
                    await self.navi.undo()
                    View.stage[session_id] -= 1
            elif label == "➡":
                    await self.navi.keep()
                    View.stage[session_id] += 1

            self.stop()

    async def on_timeout(self):
        await self.navi.page_timeout()
