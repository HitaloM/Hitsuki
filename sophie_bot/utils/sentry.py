import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.flask import FlaskIntegration

from sophie_bot.utils.logger import log
from sophie_bot.config import get_str_key


log.info("Starting sentry.io integraion...")

sentry_sdk.init(
    get_str_key('SENTRY_API_KEY'),
    integrations=[RedisIntegration(), FlaskIntegration()]
)
