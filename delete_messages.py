from nextcord import NotFound
import logging

user_msg_channel_binder = {} 

async def list_last_msg_id(interaction, client):    #binds the message id to its channel id to the id of the user who activated the bot
    last_msg = await interaction.channel.history().get(author=client.user)
    if interaction.user.id in user_msg_channel_binder.keys():
        user_msg_channel_binder[interaction.user.id].append((last_msg.id, last_msg.channel.id))
    else:
        user_msg_channel_binder[interaction.user.id] = [(last_msg.id, last_msg.channel.id)]


async def delete_messages(interaction, client): #delete messages in reverse order
    for message_id, channel_id in user_msg_channel_binder[interaction.user.id][::-1]:
        try:
            await client.http.delete_message(channel_id, message_id)
        except NotFound:
            logging.warning("\033[1;33;40mWarning: \033[0;37;40mCould not delete message with id '" + str(message_id) + "' in channel with id '" + str(channel_id) + "'. This is most likely because the user spammed the bot with messages.")
    

    user_msg_channel_binder[interaction.user.id] = [] #reset user's msg list
