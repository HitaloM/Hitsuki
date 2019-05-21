import asyncio
from importlib import import_module

from sophie_bot import TOKEN, bot, logger
from sophie_bot.modules import ALL_MODULES

for module_name in ALL_MODULES:
    imported_module = import_module("sophie_bot.modules." + module_name)

logger.info("Modules loaded!")

bot.start(bot_token=TOKEN)
logger.info("Bot is alive!")

# Catch up missed updates
asyncio.ensure_future(bot.catch_up())

# Run loop
bot.run_until_disconnected()
