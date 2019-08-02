from nostril import nonsense

from sophie_bot import decorator, tbot
from telethon.tl.functions.photos import GetUserPhotosRequest
from sophie_bot.modules.users import aio_get_user, user_link_html


NAMES = []

with open('sophie_bot/names.txt') as f:
    for line in f:
        NAMES.append(line.lower().replace('\n', ''))


@decorator.command('checkspammer', is_sudo=True)
async def check_manually(message, **kwargs):
    user, txt = await aio_get_user(message, allow_self=True)

    print(user)

    name = user['first_name']
    user_pics = await tbot(GetUserPhotosRequest(
        int(user['user_id']),
        offset=0,
        max_id=0,
        limit=100))

    print(user_pics)

    if user['last_name']:
        name += user['last_name']

    num = 0

    text = "User " + await user_link_html(user['user_id'])
    text += "\nName: " + name
    text += "\nID: <code>" + str(user['user_id']) + '</code>'

    text += '\n'

    if user['first_name'].replace(' ', '').isdigit():
        text += "\n<b>Warn! User have name with only numbers!</b>"
        num += 80

    if user['first_name'].lower() in NAMES:
        text += "\n<b>Warn! User have real name (Mostly spammers try to be like real human)!</b>"
        num += 75

    if user_pics and len(user_pics.photos) == 1:
        text += "\n<b>Warn! User have only 1 display picture!</b>"
        num += 40

    try:
        check = nonsense(name)
        if check is True:
            text += "\n<b>Warn! User have noncence name!</b>"
            num += 98
        else:
            text += "\nUser have normal name"
    except ValueError:
        text += "\nName too short to analyse it"

    text += '\n\n<b>Suspicion: </b><code>' + str(num) + "%</code>"

    if num > 100:
        num = 100

    await message.reply(str(text))
