import nextcord

class View(nextcord.ui.View):
    stage = {} #NOTE: this should probably be moved to main.
    def __init__(self, navi, interaction):
        super().__init__(timeout=120)
        self.buttons = []
        self.navi = navi
        self.interaction = interaction #slash command's interaction.
        self.current_label = "❓" #placeholder for first clear_reaction.
        label_list = []
        color_list = []
        emoji_label_list = ["⬅", "➡", "🎲", "🔄", "❌"]
        number_emoji_list = [f"{i}\uFE0F\u20E3" if i < 10 else f"{i//10}\uFE0F\u20E3{i%10}\uFE0F\u20E3" for i in range(1, 100)]
 #list of number emojis.

        for i, emoji in enumerate(emoji_label_list[:3]): #make list of all button labels and their respective colors.
            color_list.extend([nextcord.ButtonStyle.blurple] * 4)
            label_list.extend([str(i) for i in range((i * 4) + 1, (i * 4) + 5)])
            color_list.append(nextcord.ButtonStyle.green)
            label_list.append(emoji)
        color_list.extend([nextcord.ButtonStyle.blurple] * 3) #last line of buttons.
        label_list.extend([str(i) for i in range(13, 16)])
        color_list.append(nextcord.ButtonStyle.grey)
        color_list.append(nextcord.ButtonStyle.red)
        label_list.extend(emoji_label_list[-2:])


        for label, style in zip(label_list, color_list): #make the buttons.
            button = nextcord.ui.Button(custom_id=label, label=label, style=style)
            async def button_function(interaction):
                label = interaction.data["custom_id"] #sets label to the label of the button that was pressed.
                await self.click_by_label(label, interaction.user.id) #uses the button press interaction.
                if label.isnumeric(): 
                    label = number_emoji_list[int(label) - 1] #converts the label to an emoji if it is a number.
                self.current_label = label #used to add the emoji to the message to show the what the user selected.

            button.callback = button_function
            self.add_item(button)


    async def click_by_label(self, label, interactor):
        if interactor == self.interaction.user.id: #checks if the user who pressed the button is the one who activated the bot
            if label.isnumeric():
                await self.navi.click_by_index(int(label))
                View.stage[interactor] += 1
            elif label == "❌":
                await self.navi.exit()
            elif label == "🎲":
                await self.navi.rand()
                View.stage[interactor] += 1
            elif label == "🔄":
                await self.navi.refresh()
            if label == "⬅":
                if View.stage[interactor] > 0:
                    View.stage[interactor] -= 1 #TODO: find a way to tell the user that they can't undo/keep any further
                    await self.navi.undo()
            elif label == "➡":
                if View.stage[interactor] > 0:
                    await self.navi.keep()
                    View.stage[interactor] += 1
            self.stop()


    async def on_timeout(self):
        await self.navi.browser_timeout()