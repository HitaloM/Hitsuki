def need_args_dec(num=1):
    def wrapped(func):
        async def wrapped_1(event, *args, **kwargs):
            print(event)
            if len(event.text.split(" ")) > num:
                return await func(event, *args, **kwargs)
            else:
                await event.reply("No enoff args!")
        return wrapped_1
    return wrapped
