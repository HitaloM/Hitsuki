import asyncio
from importlib import import_module

from sophie_bot import TOKEN, bot, logger
from sophie_bot.modules import ALL_MODULES

for module_name in ALL_MODULES:
    imported_module = import_module("sophie_bot.modules." + module_name)

logger.info("Modules loaded!")

bot.start(bot_token=TOKEN)

# Catch up missed updates
logger.info("Catch up missed updates..")

try:
    asyncio.ensure_future(bot.catch_up())
except Exception as err:
    logger.error(err)

# Run loop
logger.info("Running loop..")
logger.info("Bot is alive!")
bot.run_until_disconnected()
