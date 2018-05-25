#! /usr/bin/env python3
import os
import sys
import time
import datetime
import discord
import asyncio
import ctypes
import subprocess

screenshot = True# スクリーンショット自動アップロード機能
token = ''# botのtoken
softalk_path = 'SofTalk.exe'# softalkのパス
text_ch_name = 'general'# text channel
voice_ch_name = ''# voice channel
game_dir_path = 'C:/Program Files (x86)/Steam/steamapps/common/7 Days To Die/'#7DaysToDie.exeのフォルダパス
names = {}# ゲーム内の名前の読み方　{'ebicochineal' : 'えびこちにーる'} 設定しなかったらローマ字読み
message_file = [(0x48, 'help.wav', 20)]# メッセージのwav キー入力がトリガー　(キーコード, ファイルパス, 音量0~100) 0x48 Hキー

class Bot:
    def __init__(self, token, tch_name, vch_name, gamedir, softalk_path):
        client = discord.Client()
        self.client = client
        self.token = token
        self.tch_name = tch_name
        self.vch_name = vch_name
        self.tch = None
        self.vch = None
        self.gamedir = gamedir
        self.mfile = []
        self.names = []
        self.voice = None
        self.player = None
        self.voice_queue = []
        self.now_voice = ()
        self.start_unixtime = time.mktime(datetime.datetime.now().timetuple())
        self.target_game = '7 Days To Die'
        self.softalk_path = softalk_path
        self.screenshot = False
        self.kd = {}
        self.ad = {}
        self.xd = {}
        self.set_hira_dicts()
        self.wav_num = 0
        self.cd = os.path.abspath(os.path.dirname(__file__))
        self.wavs = self.add_path(self.cd, 'wavs')
        self.init_wav_dir()
        
        @client.event
        async def on_ready():
            await self.on_ready()
        @client.event
        async def on_message(message):
            await self.on_message(message)
        
    def run(self):
        self.client.run(self.token)
    
    async def on_ready(self):
        print('on_reaby')
        print(self.client.user.name)
        print(self.client.user.id)
        await self.set_tch()
        await self.set_vch()
        if self.tch == None or self.vch == None : exit()
        print('Found Discord Channel')
        if self.screenshot : asyncio.ensure_future(self.screenshot_loop())
        asyncio.ensure_future(self.key_voice_loop())
        asyncio.ensure_future(self.play_voice_loop())
        asyncio.ensure_future(self.output_log_loop())
    
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
        ltime = self.start_unixtime
        while 1:
            await asyncio.sleep(10)
            first = True
            for i in os.listdir(self.gamedir):
                fp = self.add_path(self.gamedir, i)
                t = os.path.getmtime(fp)
                if i.endswith('jpg') and t > ltime:
                    print(i, t)
                    ltime = t
                    await self.client.send_file(self.tch, fp, filename=i)
                    if first : first = False
    
    async def key_voice_loop(self):
        while 1:
            await asyncio.sleep(0.1)
            for k, f, v in self.mfile:
                if ctypes.windll.user32.GetAsyncKeyState(k) != 0:
                    if not (f, v) in self.voice_queue and self.is_target_app() and (not self.is_play() or (f, v) != self.now_voice):
                        self.voice_queue += [(f, v)]
    
    async def play_voice_loop(self):
        while 1:
            await asyncio.sleep(1)
            if self.voice and not self.is_play() and self.voice_queue:
                self.now_voice = self.voice_queue.pop(0)
                t, v = self.now_voice
                for i in range(5):
                    if os.path.exists(t):
                        self.player = self.voice.create_ffmpeg_player(t)
                        self.player.volume = v / 100
                        self.player.start()
                        break
                    await asyncio.sleep(1)
            elif self.voice and self.is_play():
                if self.player.volume < 0.01:
                    self.player.stop()
                else:
                    self.player.volume *= 0.85
                
    
    def is_play(self):
        return self.voice != None and self.player != None and self.player.is_playing()
    
    def is_target_app(self):
        if self.target_game == '' : return True
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        l = ctypes.windll.user32.GetWindowTextLengthW(ctypes.c_int(hwnd))
        if l != 0:
            b = ctypes.create_unicode_buffer(l+1)
            ctypes.windll.user32.GetWindowTextW(ctypes.c_int(hwnd), b, ctypes.sizeof(b))
            return self.target_game in b.value
        else:
            return False
    
    async def output_log_loop(self):
        self.cmd_call(self.softalk_path)
        logdir = self.add_path(self.gamedir, '7DaysToDie_Data')
        text_last_update = self.start_unixtime
        prev_file_path = ''
        prev_file_size = 0
        
        while 1:
            await asyncio.sleep(2)
            fpath = None
            new_file = 0
            for i in os.listdir(logdir):
                fpath_tmp = self.add_path(logdir, i)
                t = os.path.getmtime(fpath_tmp)
                if i.startswith('output_log') and t > new_file:
                    new_file = t
                    fpath = fpath_tmp
            if fpath:
                fsize = os.path.getsize(fpath)
                if fpath == prev_file_path and fsize == prev_file_size : continue
                prev_file_path = fpath
                prev_file_size = fsize
                with open(fpath, 'r', encoding='UTF-8') as f:
                    for i in f.readlines():
                        if not 'INF' in i : continue
                        t = self.text7dtdtime_to_unixtime(i.split()[0])
                        if t <= text_last_update : continue
                        if 'Chat' in i:
                            name, mes = i.split('Chat: ')[1].replace('\'', '').split(': ')
                            mes = self.alpha_to_hira(mes)
                            name = self.name_yomi(name)
                            
                            # await self.client.send_message(self.tch, '7dtd -> ' + name + ' : ' + mes)
                            
                            fp = self.next_wav_path()
                            cmd = [self.softalk_path, '/V:300', '/R:' + fp, '/W:' + name + ' ' + mes]
                            self.cmd_call(cmd)
                            self.voice_queue += [(fp, 50)]
                            text_last_update = t
                        elif 'Player' in i and 'died' in i:
                            fp = self.next_wav_path()
                            name = self.name_yomi(i.split('Player \'')[1].split('\' died')[0])
                            cmd = [self.softalk_path, '/V:300', '/R:' + fp, '/W:' + name + 'がしんだ']
                            self.cmd_call(cmd)
                            self.voice_queue += [(fp, 60)]
                            text_last_update = t
    
    def next_wav_path(self):
        r = self.add_path(self.wavs, str(self.wav_num)) + '.wav'
        self.wav_num += 1
        return r
    
    def name_yomi(self, s):
        return self.names[s] if s in self.names else self.alpha_to_hira(s)
    
    def add_path(self, a, b):
        a = a.replace('/', '\\')
        b = b.replace('/', '\\')
        if a == '' : return b
        return (a + b) if a[-1] == '\\' else (a + '\\' +  b)
    
    def cmd_call(self, cmd):
        print(cmd)
        subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None, close_fds=True)
    
    def init_wav_dir(self):
        if not os.path.exists(self.wavs) : os.mkdir(self.wavs)
        for i in os.listdir(self.wavs):
            if i.endswith('.wav') : os.remove(self.add_path(self.wavs, i))
    
    def text7dtdtime_to_unixtime(self, s):
        try:
            sd, st = s.split('T')
            d = list(map(int, sd.split('-')))
            t = list(map(int, st.split(':')))
            dt = datetime.datetime(d[0], d[1], d[2], t[0], t[1], t[2], 0)
            return time.mktime(dt.timetuple())
        except:
            return 0
    
    def set_hira_dicts(self):
        a = 'aiueo'
        b = 'kstnhmyrwgzdbp'
        k = 'かきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもや　ゆ　よらりるれろわ　　　をがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ'
        self.kd = {}
        c = 0
        for i in b:
            for j in a:
                self.kd[i+j] = k[c]
                c += 1
        self.ad = {x : y for x, y in zip('aiueon-', 'あいうえおん～')}
        self.xd = {}
        c = 0
        for i in b:
            for ji, jj in zip(['ya', 'yi', 'yu', 'ye', 'yo'], 'ゃぃゅぇょ'):
                self.xd[i+ji] = k[c - c % 5 + 1] + jj
                c += 1
    
    def alpha_to_hira(self, s):
        s = s.replace('nn', 'n')
        for i in 'kstnhmyrwgzdbp':
            s = s.replace(i+i, 'っ' + i)
        for k, v in self.xd.items():
            s = s.replace(k, v)
        for k, v in self.kd.items():
            s = s.replace(k, v)
        for k, v in self.ad.items():
            s = s.replace(k, v)
        return s.replace('\n', '')

def main():
    bot = Bot(token, text_ch_name, voice_ch_name, game_dir_path, softalk_path)
    bot.screenshot = screenshot
    bot.mfile = message_file
    bot.names = names
    bot.run()

if __name__ == '__main__':
    main()
