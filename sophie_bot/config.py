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
