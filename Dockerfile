# start from base
FROM python:3.8-rc-alpine

# install system-wide deps for python and node
RUN apk add gcc wget musl-dev

# copy our application code
ADD . /opt/sophie_bot
WORKDIR /opt/sophie_bot

# Port
EXPOSE 443
EXPOSE 6379
EXPOSE 27017

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# fetch app specific deps
RUN ls ./
RUN pip install -r requirements.txt

# start app
CMD [ "python", "-m", "sophie_bot" ]