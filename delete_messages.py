async def list_last_msg_id(ctx, user_msg_binder, client):
    last_msg = await ctx.channel.history().get(author=client.user)
    if ctx.author.id in user_msg_binder.keys():
        user_msg_binder[ctx.author.id].append(last_msg.id) #if user id is in dict, append last msg id to user
    else:
        user_msg_binder[ctx.author.id] = [last_msg.id] #else, create new key in dict with last msg id


async def delete_messages(ctx, user_msg_binder, client):
    for message in (user_msg_binder[ctx.author.id])[::-1]: #delete messages in reverse order
        await client.http.delete_message(ctx.channel.id, message) #only works if last msg is in the same channel as the first message the bot needs to delete.

    user_msg_binder[ctx.author.id] = [] #reset user's msg list