async def list_last_msg_id(ctx, msg_user_binder, client):
    last_msg = await ctx.channel.history().get(author=client.user)
    if ctx.author.id in msg_user_binder.keys():
        msg_user_binder[ctx.author.id].append(last_msg.id) #if user id is in dict, append last msg id to user
    else:
        msg_user_binder[ctx.author.id] = [last_msg.id] #else, create new key in dict with last msg id


async def delete_messages(ctx, msg_user_binder, client):
    last_msg = await ctx.channel.history().get(author=client.user)

    for message in (msg_user_binder[ctx.author.id])[::-1]: #delete messages in reverse order
        await client.http.delete_message(ctx.channel.id, message) #only works if last msg is in the same channel as the first message the bot needs to delete.

    msg_user_binder[ctx.author.id] = [] #reset user's msg list

