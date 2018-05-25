#! /usr/bin/env python3
import os
import sys
import time
import datetime
import discord
import asyncio
import ctypes

token = ''
text_ch_name = ''# text channel
voice_ch_name = ''# voice channel
screenshot_path = ''# スクリーンショットフォルダのパス
message_file = [(0x48, 'help.wav', '7 Days To Die')]# (キーコード, ファイルパス, ターゲットのウィンドウタイトルのキーワード　''ならすべて)  0x48 h key

class Bot:
    def __init__(self, token, tch_name, vch_name, screenshot_path, message_file):
        client = discord.Client()
        self.client = client
        self.tch_name = tch_name
        self.vch_name = vch_name
        self.tch = None
        self.vch = None
        self.screenshot_path = screenshot_path
        self.mfile = message_file
        self.voice = None
        self.player = None
        self.vlist = []
        self.last_unix = time.mktime(datetime.datetime.now().timetuple())
        
        @client.event
        async def on_ready():
            await self.on_ready()
        @client.event
        async def on_message(message):
            await self.on_message(message)
        
        client.run(token)
    
    async def on_ready(self):
        print('on_reaby')
        print(self.client.user.name)
        print(self.client.user.id)
        await self.set_tch()
        await self.set_vch()
        if self.tch == None or self.vch == None : exit()
        print('Found Discord Channel')
        asyncio.ensure_future(self.screenshot_loop())
        asyncio.ensure_future(self.key_voice_loop())
        asyncio.ensure_future(self.play_voice_loop())
    
    async def on_message(self, message):
        pass
    
    async def set_tch(self):
        for i in self.client.servers:
            for j in i.channels:
                if self.tch_name == str(j):
                    self.tch = j
                    return
    
    async def set_vch(self):
        for i in self.client.servers:
            for j in i.channels:
                if self.vch_name == str(j) and str(j.type) == 'voice':
                    self.vch = j
                    self.voice = await self.client.join_voice_channel(j)
                    return
    
    async def screenshot_loop(self):
        ssp = self.screenshot_path
        while 1:
            await asyncio.sleep(10)
            first = True
            for i in os.listdir(ssp):
                t = os.path.getmtime(ssp+i)
                if i.endswith('jpg') and t > self.last_unix:
                    print(i, t)
                    self.last_unix = t
                    await self.client.send_file(self.tch, ssp+i, filename=i)
                    if first:
                        first = False
    
    async def key_voice_loop(self):
        while 1:
            await asyncio.sleep(0.1)
            for k, f, t in self.mfile:
                if ctypes.windll.user32.GetAsyncKeyState(k) != 0:
                    if not f in self.vlist and self.is_target_app(t):
                        self.vlist += [f]
    
    async def play_voice_loop(self):
        while 1:
            await asyncio.sleep(1)
            if self.voice and not self.is_play() and self.vlist:
                t = self.vlist.pop()
                self.player = self.voice.create_ffmpeg_player(t)
                self.player.volume = 20 / 100
                self.player.start()
    
    def is_play(self):
        return self.voice != None and self.player != None and self.player.is_playing()
    
    def is_target_app(self, t):
        if t == '' : return True
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        l = ctypes.windll.user32.GetWindowTextLengthW(ctypes.c_int(hwnd))
        if l != 0:
            b = ctypes.create_unicode_buffer(l+1)
            ctypes.windll.user32.GetWindowTextW(ctypes.c_int(hwnd), b, ctypes.sizeof(b))
            return t in b.value
        else:
            return False

def main():
    Bot(token, text_ch_name, voice_ch_name, screenshot_path, message_file)
    
if __name__ == '__main__':
    main()
