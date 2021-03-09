# set base image (host OS)
FROM python:3.8
FROM heroku/heroku:20
FROM debian:latest

# set the working directory in the container
WORKDIR /kaga/

RUN apt -qq update && apt -qq upgrade
RUN apt -qq install -y --no-install-recommends \
    curl \
    git \
    gnupg2 \
    wget \
    
RUN apt update && apt upgrade -y
RUN apt install git curl python3-pip ffmpeg -y
RUN pip3 install -U pip
RUN curl -sL https://deb.nodesource.com/setup_15.x | bash -
RUN apt-get install -y nodejs
RUN npm i -g npm
RUN mkdir /app/
WORKDIR /app/
RUN git clone https://github.com/pytgcalls/pytgcalls && \
    cd pytgcalls && \
    npm install && \
    npm run prepare && \
    cd pytgcalls/js && \
    npm install && \
    cd ../../ && \
    pip3 install -r requirements.txt && \
    cd ../
COPY . /app/


# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip3 install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY . .

# command to run on container start
CMD [ "bash", "./start" ]
