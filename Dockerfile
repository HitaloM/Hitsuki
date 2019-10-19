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

FROM python:3.8-alpine

# install system-wide deps for python and node --no-cache --virtual .build-deps
RUN apk add gcc musl-dev libffi-dev openssl openssl-dev build-base
RUN pip install cython

# copy our application code
ADD . /opt/sophie_bot
WORKDIR /opt/sophie_bot

RUN rm -rf /opt/sophie_bot/data
RUN rm -rf /data

# fetch app specific deps
RUN ls ./
RUN pip install -r requirements.txt

# start app
CMD [ "python", "-m", "sophie_bot" ]