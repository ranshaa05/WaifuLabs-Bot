async def list_last_msg_id(ctx, msg_id, msg_user_binder, client):
    last_msg = await ctx.channel.history().get(author=client.user)
    msg_user_binder[ctx.author.id] = last_msg.id
    msg_id.append(last_msg.id)


async def delete_messages(ctx, msg_id, msg_user_binder, client):
    last_msg = await ctx.channel.history().get(author=client.user)
    
    if last_msg.id == msg_user_binder[ctx.author.id]:
        await client.http.delete_message(ctx.channel.id, msg_user_binder[ctx.author.id])
        msg_id.pop(-1)

        try:
            msg_user_binder[ctx.author.id] = msg_id[-1]
        except IndexError:
            return

        return await delete_messages(ctx, msg_id, msg_user_binder, client)

