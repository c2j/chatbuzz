
"""doc"""
import asyncio
from asyncio.exceptions import TimeoutError
import logging
from typing import Optional, Union

from wechaty_puppet import FileBox

from wechaty import Wechaty, Contact
from wechaty.user import Message, Room

#from pyChatGPT import ChatGPT
from libretranslatepy import LibreTranslateAPI

import requests
import json

import random

from gptbot_v1 import ChatGPT_Task

# Firewall 
# chat.openai.com.cdn.cloudflare.net (104.18.3.161)
#



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(filename)s <%(funcName)s> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

log = logging.getLogger(__name__)

sd_style_prompt = {
    "artist": ["by gaude monet", "by edouard manet", "by edgar dagas", "by pierre auguste renoir",
               #抽象画派
               "by W.Kandinsky", "by P.Mondrian",  
               #毕加索-法国现代画派
               "by Picasso",
               "by Hiroshi Yoshida", "by Max Ernst", "by Paul Signac", "by Salvador Dali", 
               "by James Gurney", "by M.C. Escher", "by Thomas Kinkade", "by Ivan Aivazovsky", "by Italo Calvino", 
               "by Norman Rockwell", "by Albert Bierstadt", "by Giorgio de Chirico", "by Rene Magritte", 
               "by Ross Tran", "by Marc Simonetti", "by John Harris", "by Hilma af Klint", "by George Inness", 
               "by Pablo Picasso", "by William Blake", "by Wassily Kandinsky", "by Peter Mohrbacher", 
               "by Greg Rutkowski", "by Paul Signac", "by Steven Belledin", "by Studio Ghibli", "by Josef Thoma"],           
    #风格       机械                  蒸汽朋克        吉卜力
    "style cues": ["with clockwork machines", "Steampunk", "Clockpunk", "Ghibli inspired",
                "concept art", "trending in artstation", "good composition", "hyper realistic", 
                "oil on canvas", "vivid colors", "fantasy vivid colors",
                "trending in artstation HQ"],
    #画质
    "particular medium": ["matte painting", "oil painting", "digital illustration",
            "3d render", "medieval map",
            "painting", "drawing", "sketch", "pencil drawing", "woodblock print", "matte painting", 
            "child's drawing", "charcoal drawing", "an ink drawing", "oil on canvas", "graffiti", 
            "watercolor painting", "fresco", "stone tablet", "cave painting", "sculpture", 
            "work on paper", "needlepoint"],
    #分辨率
    "resolution": ["high resolution", "4k"],

    "musthave": ["detailed"]
}

# 随机选取画风
def get_style_prompt():
    prompt=[]
    for k,v in sd_style_prompt.items():
        if len(v)>1:
            r1 = random.randint(0, len(v)-1)
            prompt.append(v[r1])
        else:
            prompt.append(v[0])
    return prompt

status_store = {}

def translate(cn):
    lt = LibreTranslateAPI("http://192.168.1.4:15000/")
    #print(lt.detect("Hello World"))
    #print(lt.translate("大漠孤烟直，长河落日圆!", "zh", "en"))
    en = lt.translate(cn, "zh", "en")
    return en

def get_wx_key(from_contact, room):
    if room == None:
        return (from_contact)
    else:
        return (room)

async def call_wechat(message, args):

    conversation: Union[
            Room, Contact] = args["from_contact"] if "room" in args and args["room"] is None else args["room"] 
    await conversation.ready()
    await conversation.say(message)        

class StableDiffusion_Task(object):
    def __init__(self, prompt, from_contact, room):
        self.prompt = prompt
        self.from_contact = from_contact
        self.room = room

    async def exec(self):
        def sd_txt2img(prompt):   
            data = {
                'prompt': prompt,
            }
            response = requests.post('http://192.168.1.4:15001/txt2img', data=data)
            result = json.loads(response.text)
            return result

        prompt = self.prompt
        from_contact = self.from_contact
        room = self.room

        if all(ord(char) < 128 for char in prompt): 
            en = prompt
        else:
            #调用LibreTranslate将中文翻译为英文
            en = translate(prompt)
        # 如果以点号或句号结尾，则直接作为提示，否则自动添加其他提示词
        if en.endswith(".") or en.endswith("。"):
            prompt = en
        else:
            prompt = en + ", " + ",".join(get_style_prompt())

        # conversation: Union[
        #     Room, Contact] = from_contact if room is None else room    
        # await conversation.ready()    
        # await conversation.say("STABLEDIFFUSION: "+ prompt)
        message = "STABLEDIFFUSION: "+ prompt
        await call_wechat(message, {"from_contact": from_contact, "room": room})
        #然后调用StableDiffusion生成图片
        #sd_res = {"sample_thumbs": "grid-0036.png", "sample_images": ["samples/00324.png", "samples/00325.png", "samples/00326.png", "samples/00327.png", "samples/00328.png", "samples/00329.png", "samples/00330.png", "samples/00331.png", "samples/00332.png"]}
        sd_res = sd_txt2img(prompt)
        log.info(sd_res)
        thumb_img = 'http://192.168.1.4:15001/getimg?img=%s' % (sd_res.get("sample_thumbs"))
        log.info(thumb_img)
        file_box = FileBox.from_url(
            thumb_img,
            name=sd_res.get("sample_thumbs"))
        
        #await conversation.say(file_box)
        await call_wechat(file_box, {"from_contact": from_contact, "room": room})

        for simg in sd_res.get("sample_images"):
            img_url = 'http://192.168.1.4:15001/getimg?img=%s' % (simg)
            log.info(img_url)
            file_box1 = FileBox.from_url(img_url, name=simg.replace("/", "_"))
            #await conversation.say(file_box1)
            await call_wechat(file_box1, {"from_contact": from_contact, "room": room})

async def message(msg: Message) -> None:
    """back on message"""
    log.info("ON Message")
    #global chatgpt_api
    text = msg.text()
    from_contact = msg.talker()
    room = msg.room()
    #chatgpt_bot.refresh_session()
    key = get_wx_key(from_contact, room)
    if text.startswith('#CHATGPT STOP#'):
        if key in chatgpt_bots:
            chatgpt_api = chatgpt_bots.pop(key)
            if hasattr(chatgpt_api, 'driver'):
                log.info('Closing browser...')
                chatgpt_api.driver.quit()
            if hasattr(chatgpt_api, 'display'):
                log.info('Closing display...')
                chatgpt_api.display.stop()
            if chatgpt_api.conversation_id != None:
                chatgpt_api.delete_conversation(chatgpt_api.conversation_id)
            del chatgpt_api
        # 结束与CHatGPT的对话 
        if key in status_store:
            del status_store[key]
            message = 'Bye'
            # conversation: Union[
            #     Room, Contact] = from_contact if room is None else room
            # await conversation.ready()
            # await conversation.say("CHATGPT: "+message)
            await call_wechat("CHATGPT: "+message, {"from_contact": from_contact, "room": room})
        
    elif text.startswith('#CHATGPT START#'):        
        # 开启与机器人对话的模式
        status_store[key] = 'Start'
        message = 'Welcome'
        # conversation: Union[
        #     Room, Contact] = from_contact if room is None else room
        # await conversation.ready()
        # await conversation.say("CHATGPT: "+message)   
        await call_wechat("CHATGPT: "+message, {"from_contact": from_contact, "room": room})
    elif text.startswith('#CHATGPT#'):
        # 如果消息是以#CHATGPT#打头的，则自动回复
        log.info("From ChatGPT：" + text)        
        prompt = text.lstrip('#CHATGPT#')  #resp       
        # chat_task = ChatGPT_Task(prompt, from_contact, room)
        chat_task = ChatGPT_Task(prompt, key, call_wechat, {"from_contact": from_contact, "room": room})
        log.debug("Async resp...")
        await task_queue.put(chat_task)
        
    elif text.startswith('#STABLEDIFFUSION#') :
        log.info("From StableDiffusion："+ text)
        #测试，
        prompt = text.lstrip('#STABLEDIFFUSION#'); 
        # 应该要放到队列中异步执行
        sd_task = StableDiffusion_Task(prompt, from_contact, room)
        log.debug("Async resp...")
        await task_queue.put(sd_task)
        
    elif key in status_store and status_store[key] == 'Start':
        
        log.info("From ChatGPT: "+ text)
        prompt = text
        chat_task = ChatGPT_Task(prompt, key, call_wechat, {"from_contact": from_contact, "room": room})
        log.debug("Async resp...")
        await task_queue.put(chat_task)
    elif text.startswith("@C3PO"):
        log.info("From @C3PO" + text)        
        prompt = text.lstrip('@C3PO') 
        chat_task = ChatGPT_Task(prompt, key, call_wechat, {"from_contact": from_contact, "room": room})
        log.debug("Async resp...")
        await task_queue.put(chat_task)

bot: Optional[Wechaty] = None

async def bot_main() -> None:
    global bot
    bot = Wechaty().on('message', message)
    await bot.start()
    log.info("BOT MAIN")

# # 专门处理异步指令
async def task_main(queue):
    #await asyncio.sleep(10)
    log.info("TASK MAIN...")
    while True:
        t = await queue.get()
        size = queue.qsize()
        log.info(f"TODO {size} tasks left")
        #await t.exec()
        #至多等待30秒
        try:
            #async with asyncio.timeout(30):
            #    await t.exec()
            await asyncio.wait_for(t.exec(), timeout=100.0)
        except TimeoutError:
            log.error("Timeout error")
    log.info("TASK MAIN end")



async def main():
    global task_queue
    #global chatgpt_bots
    #chatgpt_bots = ChatGPT_Task.chatgpt_bots
    task_queue = asyncio.Queue()
    bot = asyncio.create_task(bot_main())
    task = asyncio.create_task(task_main(task_queue))
    
    await bot
    await task
    

if __name__ == '__main__':
    global chatgpt_bots
    chatgpt_bots = ChatGPT_Task.chatgpt_bots

    asyncio.run(main())
    
