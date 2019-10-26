# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
# Copyright (C) 2019 Aiogram
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

from envparse import env
from sophie_bot.utils.logger import log
import yaml
import os

DEFAULTS = {
    'LOAD_MODULES': True,
    'DEBUG_MODE': True,

    'REDIS_HOST': 'localhost',
    'REDIS_PORT': 6379,
    'REDIS_DB_FSM': 1,

    'MONGODB_URI': 'localhost'
}


if os.path.isfile('data/bot_conf.yaml'):
    for item in (data := yaml.load(open('data/bot_conf.yaml', "r"), Loader=yaml.CLoader)):
        DEFAULTS[item.upper()] = data[item]


def get_str_key(name, required=False):
    if name in DEFAULTS:
        default = DEFAULTS[name]
    else:
        default = None
    if not (data := env.str(name, default=default)) and not required:
        log.warn('No str key: ' + name)
        return None
    elif not data:
        log.critical('No str key: ' + name)
        exit(2)
    else:
        return data


def get_int_key(name, required=False):
    if name in DEFAULTS:
        default = DEFAULTS[name]
    else:
        default = None
    if not (data := env.int(name, default=default)) and not required:
        log.warn('No int key: ' + name)
        return None
    elif not data:
        log.critical('No int key: ' + name)
        exit(2)
    else:
        return data


def get_list_key(name, required=False):
    if name in DEFAULTS:
        default = DEFAULTS[name]
    else:
        default = None
    if not (data := env.list(name, default=default)) and not required:
        log.warn('No list key: ' + name)
        return []
    elif not data:
        log.critical('No list key: ' + name)
        exit(2)
    else:
        return data


def get_bool_key(name, required=False):
    if name in DEFAULTS:
        default = DEFAULTS[name]
    else:
        default = None
    if not (data := env.bool(name, default=default)) and not required:
        log.warn('No bool key: ' + name)
        return []
    elif not data:
        log.critical('No bool key: ' + name)
        exit(2)
    else:
        return data
