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

import yaml

if os.path.isfile('data/bot_conf.yaml'):
    CONFIG = yaml.load(open('data/bot_conf.yaml', "r"), Loader=yaml.CLoader)
else:
    CONFIG = None


def get_config_key(key):
    if CONFIG and key in CONFIG['Basic']:
        cfg_key = CONFIG['Basic'][key]
    elif CONFIG and key in CONFIG['Advanced']:
        cfg_key = CONFIG['Advanced'][key]
    else:
        cfg_key = None

    cfg = os.environ.get(key, cfg_key)
    if cfg is not None:
        return cfg
    else:
        print("! Missing config key: " + key)
        return None
