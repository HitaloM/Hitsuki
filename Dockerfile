# start from base
FROM ubuntu:cosmic

# install system-wide deps for python and node
RUN apt-get -yqq update
RUN apt-get -yqq install python3.7 python3.7-dev python3.7-distutils
RUN apt-get -yqq install gcc
RUN apt-get -yqq install wget

# copy our application code
ADD . /opt/sophie_bot
WORKDIR /opt/sophie_bot

# Port
EXPOSE 443
EXPOSE 6379
EXPOSE 27017

# Install pip
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.7 get-pip.py

# fetch app specific deps
RUN ls ./
RUN pip install -r requirements.txt

# start app
CMD [ "python3.7", "-m", "sophie_bot" ]