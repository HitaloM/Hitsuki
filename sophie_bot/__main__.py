from importlib import import_module
from sophie_bot.modules import ALL_MODULES
from sophie_bot import bot, TOKEN, LOGGER


for module_name in ALL_MODULES:
    imported_module = import_module("sophie_bot.modules." + module_name)


LOGGER.info("Modules loaded!")

bot.start(bot_token=TOKEN)
LOGGER.info("Bot is alive!")


# =========================
bot.run_until_disconnected()
# =========================
