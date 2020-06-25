# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import asyncio
import pickle

from sophie_bot.utils.logger import log
from sophie_bot.services.redis import bredis


async def set_value(key, value, ttl):
    value = pickle.dumps(value)
    bredis.set(key, value)
    if ttl:
        bredis.expire(key, ttl)


def cached(ttl=600, key=None, noself=False):
    def wrapped(func):
        async def wrapped0(*args, **kwargs):
            ordered_kwargs = sorted(kwargs.items())
            new_key = key
            if not new_key:
                new_key = (func.__module__ or "") + func.__name__
                new_key += str(args[1:] if noself else args)
                new_key += str(ordered_kwargs)

            value = bredis.get(new_key)
            if value is not None:
                return pickle.loads(value)

            result = await func(*args, **kwargs)
            asyncio.ensure_future(set_value(new_key, result, ttl))
            log.debug(f'Cached: writing new data for key - {new_key}')
            return result

        return wrapped0

    return wrapped
