from nextcord import NotFound, Message
from typing import Dict, List, Tuple
import logging

user_msg_channel_binder: Dict[int, List[Tuple[int, int]]] = {}

async def list_msg_id(message: Message, interaction) -> None:
    """Binds the message id to its channel id to the id of the user who activated the bot"""
    if interaction.user.id in user_msg_channel_binder.keys():
        user_msg_channel_binder[interaction.user.id].append((message.id, message.channel.id))
    else:
        user_msg_channel_binder[interaction.user.id] = [(message.id, message.channel.id)]

async def delete_messages(interaction, client) -> None:
    """Delete messages in reverse order"""
    for message_id, channel_id in reversed(user_msg_channel_binder.get(interaction.user.id, [])):
        try:
            await client.http.delete_message(channel_id, message_id)
        except NotFound:
            logging.warning(f"Warning: Could not delete message with id '{message_id}' in channel with id '{channel_id}'")
    user_msg_channel_binder[interaction.user.id] = [] #reset user's msg list
