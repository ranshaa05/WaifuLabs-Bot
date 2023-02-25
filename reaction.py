import nextcord


class Reaction(nextcord.ui.View):
    stage = {}
    def __init__(self, navi, interavtion):
        super().__init__(timeout=120)
        self.buttons = []
        self.navi = navi
        self.interavtion = interavtion
        label_list = []
        color_list = []
        emoji_label_list = ["⬅", "➡", "🤷‍♂️", "🔄", "❌"]
        for i, emoji in enumerate(emoji_label_list[:3]):    #make list of all button labels and their respective colors
            color_list.extend([nextcord.ButtonStyle.blurple] * 4)
            label_list.extend([str(i) for i in range((i * 4) + 1, (i * 4) + 5)])
            color_list.append(nextcord.ButtonStyle.green)
            label_list.append(emoji)
        color_list.extend([nextcord.ButtonStyle.blurple] * 3) #last line of buttons
        label_list.extend([str(i) for i in range(13, 16)])
        color_list.append(nextcord.ButtonStyle.grey)
        color_list.append(nextcord.ButtonStyle.red)
        label_list.extend(emoji_label_list[-2:])


        for label, style in zip(label_list, color_list):    #make buttons
            button = nextcord.ui.Button(custom_id=label, label=label, style=style)
            async def button_function(interaction):
                label = interaction.data["custom_id"] #sets label to the label of the button that was pressed
                await self.click_by_label(label, interaction.user.id)

            button.callback = button_function
            self.add_item(button)



    async def click_by_label(self, label, interactor):
        if interactor == self.interavtion.user.id: #checks if the interactor is the one who activated the bot
            if label.isdecimal():
                await self.navi.click_by_index(int(label))
                Reaction.stage[interactor] += 1
            elif label == "❌":
                await self.navi.exit()
            elif label == "🤷‍♂️":
                await self.navi.rand()
                Reaction.stage[interactor] += 1
            elif label == "🔄":   #refresh
                await self.navi.refresh()

            if label == "⬅":
                await self.navi.undo()
                if Reaction.stage[interactor] > 0:
                    Reaction.stage[interactor] -= 1 #TODO: find a way to tell the user that they can't undo/keep any further
            elif label == "➡":
                await self.navi.keep()
                if Reaction.stage[interactor] > 0:
                    Reaction.stage[interactor] += 1
            self.stop()


    async def on_timeout(self):
        await self.navi.browser_timeout()