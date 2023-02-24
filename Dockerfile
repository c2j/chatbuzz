FROM ubuntu:22.04

RUN apt update; apt install -y python3 python3-pip; pip3 install --upgrade pip; apt clean cache
RUN apt install -y chromium-browser xvfb libnss3; apt clean cache
RUN apt install -y wget; \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; \
    apt install -y ./google-chrome-stable_current_amd64.deb; \
    apt clean cache; \
    rm -rf ./google-chrome-stable_current_amd64.deb

COPY requirements.txt /approot1/

RUN pip3 install -r /approot1/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple; \
    pip3 cache purge

COPY conf /approot1/conf
COPY config_app /approot1/config_app
COPY gptbot_app /approot1/gptbot_app
COPY wechatbot_app /approot1/wechatbot_app

WORKDIR /approot1

