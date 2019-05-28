import requests
import random

from sophie_bot import TOKEN, decorator, logger
from sophie_bot.modules.helper_func.flood import flood_limit_dec
from sophie_bot.modules.language import get_string
from sophie_bot.modules.users import get_user, user_link, user_admin_dec
from sophie_bot.modules.disable import disablable_dec
from telethon.errors import BadRequestError
from telethon.tl.types import ChatAdminRights
from telethon.tl.functions.channels import EditAdminRequest


RUN_STRINGS = (  # Thanks PaulSonOfLars
    "Where do you think you're going?",
    "Huh? what? did they get away?",
    "ZZzzZZzz... Huh? what? oh, just them again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear that's fun.",
    "Go bother someone else, no-one here cares.",
    "You can run, but you can't hide.",
    "Is that all you've got?",
    "I'm behind you...",
    "You've got company!",
    "We can do this the easy way, or the hard way.",
    "You just don't get it, do you?",
    "Yeah, you better run!",
    "Please, remind me how much I care?",
    "I'd run faster if I were you.",
    "That's definitely the droid we're looking for.",
    "May the odds be ever in your favour.",
    "Famous last words.",
    "And they disappeared forever, never to be seen again.",
    "\"Oh, look at me! I'm so cool, I can run from a bot!\" - this person",
    "Yeah yeah, just tap /kickme already.",
    "Here, take this ring and head to Mordor while you're at it.",
    "Legend has it, they're still running...",
    "Unlike Harry Potter, your parents can't protect you from me.",
    "Fear leads to anger. Anger leads to hate. Hate leads to suffering."
    "If you keep running in fear, you might "
    "be the next Vader.",
    "Multiple calculations later, I have decided my interest in your shenanigans is exactly 0.",
    "Legend has it, they're still running.",
    "Keep it up, not sure we want you here anyway.",
    "You're a wiza- Oh. Wait. You're not Harry, keep moving.",
    "NO RUNNING IN THE HALLWAYS!",
    "Hasta la vista, baby.",
    "Who let the dogs out?",
    "It's funny, because no one cares.",
    "Ah, what a waste. I liked that one.",
    "Frankly, my dear, I don't give a damn.",
    "My milkshake brings all the boys to yard... So run faster!",
    "You can't HANDLE the truth!",
    "A long time ago, in a galaxy far far away... "
    "Someone would've cared about that. Not anymore though.",
    "Hey, look at them! They're running from the inevitable banhammer... Cute.",
    "Han shot first. So will I.",
    "What are you running after, a white rabbit?",
    "As The Doctor would say... RUN!",
)


@decorator.command("id", arg=True)
@disablable_dec("id")
@flood_limit_dec("id")
async def id(event):
    text = get_string("misc", "your_id", event.chat_id).format(event.from_id)
    text += get_string("misc", "chat_id", event.chat_id).format(event.chat_id)

    if event.message.reply_to_msg_id:
        msg = await event.get_reply_message()
        userl = await user_link(msg.from_id)
        text += get_string("misc", "user_id", event.chat_id).format(userl, msg.from_id)

    elif len(event.message.raw_text) == 3:
        await event.reply(text)
        return

    else:
        user = await get_user(event)
        userl = await user_link(user['user_id'])
        text += get_string("misc", "user_id", event.chat_id).format(userl, user['user_id'])

    await event.reply(text)


@decorator.command("pin", arg=True)
@user_admin_dec
async def pinMessage(event):
    tagged_message = await event.get_reply_message()
    if not tagged_message:
        await event.reply(get_string('misc', 'no_reply_msg', event.chat_id))
        return
    msg_2_pin = tagged_message.id
    base_url = 'https://api.telegram.org/bot{}/pinChatMessage'.format(TOKEN)
    data = {'chat_id': event.chat_id, 'message_id': msg_2_pin}
    chk = event.pattern_match.group(1)
    args = chk.lower()
    tru_txt = ['loud', 'notify']
    if args in tru_txt:
        d1 = {'disable_notification': False}  # Thats How mafia Works! :P
        data.update(d1)
    else:
        d1 = {'disable_notification': True}
        data.update(d1)
    try:
        requests.post(base_url, data)  # TODO: Wait for telethon support pin :D
    except Exception as err:
        await event.reply(err)
        logger.error(err)
# CatchError=bot API throw error{error: chat_not_modified}[not in shell] if pin on already pined msg
    await event.reply(get_string('misc', 'pinned_success', event.chat_id))


@decorator.command("runs")
async def runs(event):
    await event.reply(random.choice(RUN_STRINGS))


@decorator.command("unpin")
@user_admin_dec
async def unpin_message(event):
    base_url = 'https://api.telegram.org/bot{}/unpinChatMessage'.format(TOKEN)
    data = {'chat_id': event.chat_id}
    try:
        requests.post(base_url, data)
    except Exception as err:
        await event.reply(err)
        logger.error(err)
    await event.reply(get_string('misc', 'unpin_success', event.chat_id))


@decorator.command("promote")
@user_admin_dec
async def promote(event):
<<<<<<< HEAD

    chat = await event.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
=======
>>>>>>> 5563df9... Improve code style

    user = await get_user(event)
    if user:
        pass
    else:
        return

    new_rights = ChatAdminRights(
        add_admins=True,
        invite_users=True,
        change_info=True,
        ban_users=True,
        delete_messages=True,
        pin_messages=True
    )

    try:
        await event.client(
            EditAdminRequest(
                event.chat_id,
                user.id,
                new_rights
            )
        )
        await event.reply(get_string('misc', 'promote_success', event.chat_id))

    except BadRequestError:
        await event.reply(get_string('misc', 'promote_failed', event.chat_id))
        return


@decorator.command("demote")
@user_admin_dec
async def demote(event):
    # Admin right check

    user = await get_user(event)
    if user:
        pass
    else:
        return

    # New rights after demotion
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None
    )
    # Edit Admin Permission
    try:
        await event.client(
            EditAdminRequest(
                event.chat_id,
                user.id,
                newrights
            )
        )

    # If we catch BadRequestError from Telethon
    # Assume we don't have permission to demote
    except BadRequestError:
        await event.reply(get_string('misc', 'demote_failed', event.chat_id))
        return
    await event.reply(get_string('misc', 'demote_success', event.chat_id))
