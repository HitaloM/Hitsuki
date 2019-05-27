# start from base
FROM python:3.7.3-stretch

# install system-wide deps for python and node
RUN apt install gcc wget

# copy our application code
ADD . /opt/sophie_bot
WORKDIR /opt/sophie_bot

RUN rm -rf /opt/sophie_bot/data
RUN rm -rf /data

# Port
#EXPOSE 443

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# fetch app specific deps
RUN ls ./
RUN pip install -r requirements.txt

# start app
CMD [ "python", "-m", "sophie_bot" ]