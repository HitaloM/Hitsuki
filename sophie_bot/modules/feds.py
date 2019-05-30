import uuid

from sophie_bot import decorator, mongodb
from sophie_bot.modules.language import get_strings_dec
from sophie_bot.modules.users import user_link


@decorator.command('newfed', arg=True)
@get_strings_dec("feds")
async def newFed(event, strings):
    args = event.pattern_match.group(1)
    if not args:
        await event.reply(strings['no_args'])
    fed_name = args
    creator = event.from_id
    fed_id = str(uuid.uuid4())
    data = {'fed_name': fed_name, 'fed_id': fed_id, 'creator': creator}
    check = mongodb.fed_list.insert_one(data)
    if check:
        text = strings['created_fed']
        await event.reply(text.format(name=fed_name, id=fed_id, cr=await user_link(creator)))
