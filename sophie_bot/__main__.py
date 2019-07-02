import sys
import asyncio
import signal

from importlib import import_module

from sophie_bot import CONFIG, TOKEN, tbot, redis, logger, dp, bot
from sophie_bot.modules import ALL_MODULES

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

from aiogram import executor

LOAD_COMPONENTS = CONFIG["advanced"]["load_components"]
CATCH_UP = CONFIG["advanced"]["skip_catch_up"]

# webhook settings
WEBHOOK_HOST = CONFIG["advanced"]["webhook_host"]
WEBHOOK_URL = f"{WEBHOOK_HOST}{TOKEN}"

# webserver settings
WEBAPP_HOST = CONFIG["advanced"]["webapp_host"]
WEBAPP_PORT = CONFIG["advanced"]["webapp_port"]

RATE_LIMIT = CONFIG["advanced"]["rate_limit"]
DEFAULT_RATE_LIMIT = CONFIG["advanced"]["rate_limit_num"]

loop = asyncio.get_event_loop()

# Import modules
for module_name in ALL_MODULES:
    logger.debug("Importing " + module_name)
    imported_module = import_module("sophie_bot.modules." + module_name)

logger.info("Modules loaded!")

if LOAD_COMPONENTS is True:
    from sophie_bot.modules.components import ALL_COMPONENTS

    for module_name in ALL_COMPONENTS:
        logger.debug("Importing " + module_name)
        imported_module = import_module("sophie_bot.modules.components." + module_name)

    logger.info("Components loaded!")
else:
    logger.info("Components disabled!")


# Functions

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        # Get current handler
        handler = current_handler.get()

        # Get dispatcher from context
        dispatcher = dp.get_current()
        # If handler was configured, get rate limit and key from handler
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        # Use Dispatcher.throttle method.
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            # Execute action
            await self.message_throttled(message, t)

            # Cancel current handler
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        handler = current_handler.get()
        dispatcher = dp.get_current()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta

        msg = ""

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            msg = await message.reply('Too many requests!')

        # Sleep.
        await asyncio.sleep(delta)

        # Check lock status
        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            if msg:
                await bot.edit_message_text('Unlocked.', msg.chat.id, msg.message_id)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    # insert code here to run it before shutdown
    pass


# ==


# Catch up missed updates
if CATCH_UP is False:
    logger.info("Catch up missed updates..")

    try:
        asyncio.ensure_future(tbot.catch_up())
    except Exception as err:
        logger.error(err)


def exit_gracefully(signum, frame):
    logger.info("Bye!")
    try:
        redis.bgsave()
    except Exception as err:
        logger.info("Redis error, exiting immediately!")
        logger.error(err)
        exit(1)
    logger.info("----------------------")
    sys.exit(1)


# Run loop
logger.info("Running loop..")
logger.info("tbot is alive!")
signal.signal(signal.SIGINT, exit_gracefully)

if RATE_LIMIT is True:
    dp.middleware.setup(ThrottlingMiddleware())

if CONFIG['advanced']['webhooks'] is True:
    logger.info("Using webhooks method")
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=TOKEN,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=CATCH_UP,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT
    )
else:
    logger.info("Using polling method")
    executor.start_polling(dp, skip_updates=CATCH_UP)
# asyncio.get_event_loop().run_forever()
