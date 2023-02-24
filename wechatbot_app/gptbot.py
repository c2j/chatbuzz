# encoding: utf-8
import asyncio
import logging


from pyChatGPT import ChatGPT

import json

# Firewall:       chat.openai.com.cdn.cloudflare.net (104.18.3.161)
# 
#
from abc import ABC, abstractmethod
class Task(ABC):
    def __init__(self, prompt, wx_key, callback=None, callback_args=None):
        self.prompt = prompt
        self.wx_key = wx_key
        self.callback = callback
        self.callback_args = callback_args
        
    @abstractmethod
    async def exec(self):
        pass

class ChatGPT_Task(Task):
    async def exec(self, chatgpt_bots):
        def create_cgbot():
            # 每次都从配置文件读，如果这时正在写，可能会有偶发的读写冲突，可以暂时不管
            with open('conf/config.json', 'r') as file:
                # Load the data from the file
                config = json.load(file)
                if "session_token" in config:
                    session_token = config["session_token"]
            chatgpt_api = ChatGPT(session_token)
            return chatgpt_api

        prompt = self.prompt
        key = self.wx_key

        print("Doing ChatGPT", prompt, key)
        
        chatgpt_api = None
        if key in chatgpt_bots:
            print("1")
            chatgpt_api = chatgpt_bots.get(key)
        else:
            #创建一个ChatGPT Bot
            print("2")
            chatgpt_api = create_cgbot()
            chatgpt_bots[key]= chatgpt_api
        print("To send msg")
        message = "Unknown Error"
        try:
            msg = chatgpt_api.send_message(prompt)
            print(msg)
            message = msg['message'] #"Closed"
        except:
            msg = chatgpt_api.send_message(prompt)
            print(msg)
            message = msg['message'] #     
        print(message)
        if self.callback != None:
            await self.callback(message, self.callback_args)
        return message
