import sys
import asyncio
import signal

from importlib import import_module

from sophie_bot import TOKEN, bot, redis, logger
from sophie_bot.modules import ALL_MODULES
from sophie_bot.modules.components import ALL_COMPONENTS

for module_name in ALL_MODULES:
    logger.debug("Importing " + module_name)
    imported_module = import_module("sophie_bot.modules." + module_name)

logger.info("Modules loaded!")

for module_name in ALL_COMPONENTS:
    logger.debug("Importing " + module_name)
    imported_module = import_module("sophie_bot.modules.components." + module_name)

logger.info("Components loaded!")

bot.start(bot_token=TOKEN)

# Catch up missed updates
logger.info("Catch up missed updates..")

try:
    asyncio.ensure_future(bot.catch_up())
except Exception as err:
    logger.error(err)


def exit_gracefully(signum, frame):
    redis.bgsave()
    logger.info("Bye!")
    logger.info("--------------------")
    sys.exit(1)


# Run loop
logger.info("Running loop..")
logger.info("Bot is alive!")
original_sigint = signal.getsignal(signal.SIGINT)
signal.signal(signal.SIGINT, exit_gracefully)
bot.run_until_disconnected()
