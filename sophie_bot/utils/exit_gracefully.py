# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import os
import signal

from sophie_bot.services.redis import redis
from sophie_bot.utils.logger import log


def exit_gracefully(signum, frame):
    log.warning("Bye!")

    try:
        redis.save()
    except Exception:
        log.error("Exiting immediately!")
    os.kill(os.getpid(), signal.SIGUSR1)


# Signal exit
log.info("Setting exit_gracefully task...")
signal.signal(signal.SIGINT, exit_gracefully)
