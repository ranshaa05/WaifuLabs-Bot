import nextcord
from site_navigator import SiteNavigator


class Reaction(nextcord.ui.View):
    stage = 0

    def __init__(self, navi):
        super().__init__(timeout=120)
        self.buttons = []
        self.navi = navi
        label_list = []
        color_list = []
        emoji_label_list = ["⬅", "➡", "🤷‍♂️", "🔄", "❌"]
        for i, emoji in enumerate(emoji_label_list[:3]):    #make list of all button labels and their respective colors
            color_list.extend([nextcord.ButtonStyle.blurple] * 4)
            label_list.extend([str(i) for i in range((i * 4) + 1, (i * 4) + 5)])
            color_list.append(nextcord.ButtonStyle.green)
            label_list.append(emoji)
        color_list.extend([nextcord.ButtonStyle.blurple] * 3)   #last line of buttons
        label_list.extend([str(i) for i in range(13, 16)])
        color_list.append(nextcord.ButtonStyle.grey)
        color_list.append(nextcord.ButtonStyle.red)
        label_list.extend(emoji_label_list[-2:])


        for label, style in zip(label_list, color_list):    #make buttons
            button = nextcord.ui.Button(custom_id=label, label=label, style=style)
            async def button_function(interaction):
                label = interaction.data["custom_id"] #sets label to the label of the button that was pressed
                await self.click_by_label(label)

            button.callback = button_function
            self.add_item(button)

    async def on_timeout(self):
        print("Timeout")
        await self.navi.browser_timeout()



    async def click_by_label(self, label):  # label is the string that is shown on the button
        if label.isdecimal():
            await self.navi.click_by_index(int(label))
            Reaction.stage = Reaction.stage + 1
            self.stop()

        elif label == "❌":
            await self.navi.exit()
            self.stop()
        elif label == "⬅":
            await self.navi.undo()
            if Reaction.stage > 0:
                Reaction.stage = Reaction.stage - 1 #find a way to tell the user that they can't undo/keep anymore
            self.stop()
        elif label == "➡":
            await self.navi.keep()
            if Reaction.stage > 0:
                Reaction.stage = Reaction.stage + 1
            self.stop()
        elif label == "🤷‍♂️":
            await self.navi.rand()
            Reaction.stage = Reaction.stage + 1
            self.stop()
        elif label == "🔄":   #refresh
            await self.navi.refresh()
            self.stop()
        else:
            raise ValueError(f"Label `{label}` was not found")
