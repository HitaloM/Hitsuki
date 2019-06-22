import sys
import asyncio
import signal

from importlib import import_module

from sophie_bot import CONFIG, TOKEN, tbot, redis, logger, dp, bot
from sophie_bot.modules import ALL_MODULES

from aiogram import executor

LOAD_COMPONENTS = CONFIG["advanced"]["load_components"]
CATCH_UP = CONFIG["advanced"]["skip_catch_up"]

# webhook settings
WEBHOOK_HOST = CONFIG["advanced"]["webhook_host"]
WEBHOOK_URL = f"{WEBHOOK_HOST}{TOKEN}"

# webserver settings
WEBAPP_HOST = CONFIG["advanced"]["webapp_host"]
WEBAPP_PORT = CONFIG["advanced"]["webapp_port"]

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


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    # insert code here to run it before shutdown
    pass


# Run loop
logger.info("Running loop..")
logger.info("tbot is alive!")
signal.signal(signal.SIGINT, exit_gracefully)

if CONFIG['advanced']['webhooks'] is True:
    logger.info("Using webhooks method")
    executor.start_webhook(dispatcher=dp,
                           webhook_path=TOKEN,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown,
                           skip_updates=CATCH_UP,
                           host=WEBAPP_HOST,
                           port=WEBAPP_PORT)
else:
    logger.info("Using polling method")
    executor.start_polling(dp, skip_updates=CATCH_UP)
# asyncio.get_event_loop().run_forever()
