#! /usr/bin/env python3
import os
import sys
import time
import discord
import asyncio
import shutil
import requests
from PIL import Image, ImageDraw
from subprocess import Popen, PIPE

token = ''
ch = 'general'# target channel

class Bot:
    def __init__(self, token, ch):
        client = discord.Client()
        self.client = client
        self.token = token
        self.cd = os.path.abspath(os.path.dirname(__file__))
        
        self.ch = None
        self.n = '1000'
        
        @client.event
        async def on_ready():
            await self.on_ready()
        @client.event
        async def on_message(message):
            await self.on_message(message)
        
    def run(self):
        self.client.run(self.token)
    
    async def on_message(self, message):
        if message.author == self.client.user : return
        mc = message.content
        ch = message.channel
        id = message.author.id
        
        url = ''
        if os.path.exists('lock') or not str(ch.type) == 'private' : return
        
        if mc.startswith('n=') or mc.startswith('N='):
            try:
                self.n = str(min(max(int(mc.split('=')[1]), 20), 1000))
                print('N=' + self.n)
                await self.client.send_message(ch, 'N=%sに設定しました' % self.n)
            except:
                pass
        
        if message.attachments : url = message.attachments[0]['url']
        if not url:
            for i in mc.split():
                if '.jpg' in i or '.png' in i : url = i
        if url:
            if self.image_download(url):
                await self.client.send_message(ch, '画像作成中...')
                asyncio.ensure_future(self.create_wait_loop())
                print('create_wait_loop')
                cmd = 'python ' + self.cd + '/' + 'circlesmix.py' + ' ' + self.n
                with open(self.cd + '/' + 'lock', 'w') as f : pass
                Popen(cmd, stdin=None, stdout=None, stderr=None, close_fds=True)
    
    async def create_wait_loop(self):
        file = self.cd + '/' + 'circlesmix.png'
        if os.path.exists(file) : os.remove(file)
        cnt = 0
        while cnt < 300:
            await asyncio.sleep(1)
            if os.path.exists(file):
                await asyncio.sleep(1)
                if self.ch:
                    print('send')
                    await self.client.send_file(self.ch, file, filename = 'circlesmix.png')
                    await self.client.send_message(self.ch, 'topcoder Marathon Match 95')
                await asyncio.sleep(1)
                break
            cnt += 1
    
    def image_download(self, url):
        print('image download')
        r = False
        try:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(self.cd + '/' + 'image', 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
                    r = True
        except:
            pass
        return r
    
    async def on_ready(self):
        print('on_reaby')
        print(self.client.user.name)
        print(self.client.user.id)
        
        if os.path.exists('lock') : os.remove('lock')
        for i in self.client.servers:
            for j in i.channels:
                if str(j) == ch : self.ch = j

def main():
    bot = Bot(token, ch)
    bot.run()

if __name__ == '__main__':
    main()
