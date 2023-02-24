# encoding: utf-8
import asyncio
import logging

from revChatGPT.V1 import Chatbot

import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(filename)s <%(funcName)s> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger(__name__)

# Firewall:       chat.openai.com.cdn.cloudflare.net (104.18.3.161)
# 
#
# explorer.api.openai.com 52.152.96.252
# chatgpt.duti.tech

class ChatGPT_Task(object):
    chatgpt_bots = {}
    def __init__(self, prompt, wx_key, callback=None, callback_args=None):
        self.prompt = prompt
        self.wx_key = wx_key
        self.callback = callback
        self.callback_args = callback_args
    async def exec(self):
        def create_cgbot():
            # 每次都从配置文件读，如果这时正在写，可能会有偶发的读写冲突，可以暂时不管
            with open('conf/config.json', 'r') as file:
                # Load the data from the file
                config = json.load(file)
                if "session_token" in config:
                    session_token = config["session_token"]
                    #print("Create a new WechatBot")
                    chatgpt_api = Chatbot(config={
                                "session_token": session_token
                                })
                    return chatgpt_api

        prompt = self.prompt
        key = self.wx_key

        log.info("Doing revChatGPT: "+ prompt)
        
        chatgpt_api = None
        if key in ChatGPT_Task.chatgpt_bots:
            #print("1")
            chatgpt_api = ChatGPT_Task.chatgpt_bots.get(key)
        else:
            #创建一个ChatGPT Bot
            #print("2")
            chatgpt_api = create_cgbot()
            #print("3", key)
            ChatGPT_Task.chatgpt_bots[key]= chatgpt_api
            #print("4")
        log.info("To send msg")
        message = "Unknown Error"
        steps = 0
        for data in chatgpt_api.ask(prompt, timeout=99):
            message = data["message"]
            await asyncio.sleep(0.1) #这样的话，timeouterror才能产生 
            steps += 1
            #if steps % 300 == 0:
            #    if self.callback != None:
            #        await self.callback("Please waiting...", self.callback_args)
            # message也包括输入过程的文字，因此等到迭代结束才返回
        if len(message)>0: 
            log.info(message)
            if self.callback != None:
                await self.callback(message, self.callback_args)
           
        return message

# 一辆班车，起点是公平路，
# 在公平路上了两个人，然后下一站是控江路，
# 别着急。这一站上来四个人，二男二女
# 下一站是江浦路，上来两个人，都是男性。
# 下一站是终点站云桥路。请问在到达终点站之前，班车上一共有几个人？几男几女？