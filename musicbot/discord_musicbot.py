#! /usr/bin/env python3
import os
import discord
import asyncio
import subprocess
import http
import http.cookiejar
from subprocess import Popen, PIPE
import urllib.request, urllib.parse

p = os.path.dirname(__file__).replace('\\', '/') + '/'
crdir = '' if p == '/' else p
client = discord.Client()

##############################
token = ''
niconico_user = ''
niconico_password = ''
##############################

playlistfile = crdir + 'discord_playlist.txt'
musicdir = crdir + 'discordmusic/'
nico = 'http://www.nicovideo.jp/watch/'
tube = 'https://www.youtube.com/watch?'

voice = None
player = None
playstate = '[]'
mloop_b = False
next_b = False
pindex = 0

help = '''
play                                  >
volume      -+5～           +   or   ++++++   or   -   or   ------
stop                                 []
youtube                          v=xxxxxxxxxx   or   < URL
niconico                          smxxxxxxxxx   or   nmxxxxxxxx   or   < URL
niconicoplaylist             <<< URL
view playlist                   mlist
delete item                     mdel 1  or mdel 1 2 3
swap item                       mswap 1 2
loop                                  mloop
'''

class playlist:
    def __init__(self, path, musicdir):
        self.path = path
        self.musicdir = musicdir
        self.items = []
        if not os.path.exists(musicdir) : os.mkdir(musicdir)
        self.loaditems()
        self.cleandir()
        self.rename()
        self.saveitems()
        for i in self.items : print(i.title, i.path, i.volume)
    
    def additem(self, mitem):
        self.items.append(mitem)
        self.saveitems()
    
    def loaditems(self):
        self.items = []
        try:
            with open(self.path , 'r') as f:
                for i in f.readlines():
                    title, path, volume = i.strip().split(',')
                    if os.path.exists(path):
                        m = musicitem(path, title, int(volume))
                        self.items.append(m)
        except:
            pass
    
    def cleandir(self):
        files = [os.path.basename(x.path) for x in self.items]
        for i in os.listdir(self.musicdir):
            try:
                if not i in files:
                    print('remove', i)
                    os.remove(self.musicdir + i)
            except:
                pass
    
    def rename(self):
        for i in self.items:
            f = os.path.basename(i.path)
            os.rename(i.path, self.musicdir + 't' + f)
            i.path = self.musicdir + '/' + 't' + f
            
        for i, j in enumerate(self.items):
            os.rename(j.path, self.musicdir + 'r' + str(i) + '.mp4')
            j.path = self.musicdir + 'r' + str(i) + '.mp4'
    
    def saveitems(self):
        print('saveitems')
        with open(self.path , 'w') as f:
            for i in self.items:
                if i.checkfile(): 
                    f.write(i.title + ',' + str(i.path) + ',' + str(i.volume) + '\n')
    
    def cleanplaylist(self):
        l = []
        for i, j in enumerate(self.items):
            if not j.checkfile() : l += [i]
        for i in l : self.pop(i)
        if l : self.saveitems()
        
    def __len__(self):
        return len(self.items)
        
    def pop(self, n):
        self.items.pop(n)
        
    def swap(self, a, b):
        self.items[a], self.items[b] = self.items[b], self.items[a]

class downloader:
    def __init__(self, nicouser, nicopass, dir):
        self.nicouser = nicouser
        self.nicopass = nicopass
        self.num = 0
        self.dir = dir
    
    async def download(self, url):
        num = self.num
        self.num += 1
        path = self.filepath(num)
        title = self.get_title(url)
        dcmd = ' '.join(self.cmd(url) + ['-o', path, '--no-part --no-continue'])
        Popen(dcmd)
        if await self.dl_check(self.filepath(num)):
            return path, title
        else:
            return None
    
    async def dl_check(self, path):
        for i in range(10):
            await asyncio.sleep(1)
            if os.path.exists(path) : return True
        return False
    
    def filepath(self, num):
        return self.dir + str(num) + '.mp4'
    
    def get_title(self, url):
        title = 'untitled'
        tcmd = ' '.join(self.cmd(url) + ['--get-title'])
        p = Popen(tcmd, stdout = PIPE).communicate()[0]
        for i in ['utf-8', 'sjis', 'iso-2022-jp']:
            try:
                title = p.decode(i).replace('\r\n', '\n').replace('\n', '')
                title = title.replace(',', '')
                break
            except:
                pass
        return title
        
    def cmd(self, url):
        r = ['youtube-dl.exe -f bestaudio/best']
        if 'nicovideo' in url : r += ['-u', self.nicouser, '-p', self.nicopass]
        return r + [url]

class musicitem:
    def __init__(self, path, title, volume):
        self.path = path
        self.title = title
        self.volume = volume
    
    def checkfile(self):
        return os.path.exists(self.path)

def next_music():
    global pindex
    pindex = (pindex + 1) % len(plist)

def prev_music():
    global pindex
    pindex = (len(plist) + pindex - 1) % len(plist)

def get_pindex():
    global pindex
    plist.cleanplaylist()
    if not pindex < len(plist) : pindex = 0
    return pindex

def isplaying():
    return player != None and player.is_playing()

def mdel(n):
    global pindex
    l = len(plist)
    n -= 1
    if 0 <= n < l:
        print('mdel', n+1)
        if n < pindex : pindex -= 1
        plist.pop(n)
    plist.saveitems()

def mswap(a, b):
    l = len(plist)
    a -= 1; b -= 1
    if 0 <= a < l and 0 <= b < l:
        plist.swap(a, b)
    plist.saveitems()

async def mlist(ch):
    l = get_pindex()
    s = ''
    e = [':arrow_forward:', ':arrows_counterclockwise:'][mloop_b]
    if not isplaying() : e = ':small_blue_diamond:'
    for i in range(len(plist)):
        s += [':black_small_square:', e][l == i] + wnum(i+1, 2) + ':'
        v = (plist.items[i].volume > 0) + (plist.items[i].volume > 50)
        s += [':speaker:', ':sound:', ':loud_sound:'][v]
        s += wnum(plist.items[i].volume, 3) + ':'
        s += limitstr(plist.items[i].title, 32)
        s += '\n'
    if s == '' : s = 'None'
    await client.send_message(ch, s)

async def mdl(ch, index):
    if plist.items[index-1].checkfile():
        await client.send_file(ch, plist.items[index-1].path, filename = plist.items[index-1].title + '.mp4')

mlock = 0
async def mmyilist(ch, url):
    global mlock
    if mlock == 1:
        await client.send_message(ch, '他のニコニコマイリスト処理中です')
        return
    mlock = 1
    try:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.LWPCookieJar()))
        user = {'mail_tel': niconico_user, 'password': niconico_password}
        post = urllib.parse.urlencode(user).encode('utf-8')
        opener.open('https://secure.nicovideo.jp/secure/login?site=niconico', post)
        result = opener.open(url).read()
        orders = []
        for i in result.decode('utf-8').split('"video_id":"')[1:]:
            url = nico + nicoid(i.split('"')[0])
            orders += [url]
        await client.send_message(ch, 'ニコニコマイリストアイテム数 : ' + str(len(orders)))
        if len(orders) > 10:
            await client.send_message(ch, '１０曲まで取得します')
            orders = orders[:10]
        cnt = 1;
        for i in orders:
            print(cnt)
            path, title = await pdown.download(i)
            m = musicitem(path, title, 20)
            plist.additem(m)
            await client.send_message(ch, str(cnt) + '/' + str(len(orders)))
            if cnt > 11 or cnt == len(orders): break
            await asyncio.sleep(60)
            cnt += 1
        await mlist(ch)
    except:
        print('except mlist')
    mlock = 0

def wnum(n, m):
    r = ''
    for i in str(n):
        r += '０１２３４５６７８９'[int(i)]
    return r.rjust(m, '　')

def limitstr(s, n):
    if n <= 3:
        s = s[:n]
    elif len(s) > n:
        s = s[:n-3] + '...'
    return s

async def move_voice_channel(user):
    global voice
    name = str(user).split('#')[0]
    for i in client.servers:
        for j in i.channels:
            if str(j.type) == 'voice' and any(name == x.name for x in j.voice_members):
                if voice != None : await voice.disconnect()
                voice = await client.join_voice_channel(j)
                break
    await start_music_loop()

async def start_music_loop():
    global playstate
    if playstate == '[]':
        playstate = '>'
        await asyncio.gather(player_loop())

async def player_loop():
    global player, playstate, next_b, pindex
    print('loop', playstate)
    while playstate == '>':
        await asyncio.sleep(1)
        try:
            if voice != None and len(voice.channel.voice_members) < 2:
                await stop_player()
                break
            a = not isplaying()
            c = voice != None
            d = len(plist)
            if all((a, c, d)):
                if next_b and not mloop_b : next_music()
                print(plist.items[get_pindex()].path)
                player = voice.create_ffmpeg_player(plist.items[get_pindex()].path)
                player.volume = plist.items[get_pindex()].volume / 100
                player.start()
                next_b = True
                await asyncio.sleep(10)
        except ValueError:
            print(ValueError)
            playstate = '[]'

def nicoid(s):
    if '/' in s : s = s.split('/')[-1]
    if '?' in s : s = s.split('?')[0]
    if len(s) > 14 or any([x in s for x in ' ;%&|']) : s = ''
    return s

def tubeid(s):
    if '?' in s : s = s.split('?', 1)[1]
    if '&' in s : s = s.split('&')[0]
    if len(s) > 14 or any([x in s for x in ' ;%&|']) : s = ''
    return s

async def stop_player():
    global player, playstate
    playstate = '[]'
    if player != None:
        player.stop()
        await voice.disconnect()

async def music_cmd(message):
    global player, playstate, next_b, mloop_b, pindex
    if message.author == client.user : return
    mc = message.content
    ch = message.channel
    if mc.startswith('[]') : await stop_player()
    if mc.startswith('>') and mc != '>>':
        if len(mc) > 2 : pindex = int(mc[2:]) - 1
        next_b = False
        await move_voice_channel(message.author)
    if any([mc.startswith(x) for x in ['v=', '< ' + tube]]):
        url = tube + tubeid(mc)
        path, title = await pdown.download(url)
        m = musicitem(path, title, 20)
        plist.additem(m)
        await mlist(ch)
    if any([mc.startswith(x) for x in ['sm', 'nm', '< '+ nico]]) and niconico_user != '':
        url = nico + nicoid(mc)
        path, title = await pdown.download(url)
        m = musicitem(path, title, 20)
        plist.additem(m)
        await mlist(ch)
    if mc.startswith('<<< ') and not mc.startswith('<<< http://www.nicovideo.jp/mylist/'):
        url = mc[4:]
        path, title = await pdown.download(url)
        m = musicitem(path, title, 20)
        plist.additem(m)
        await mlist(ch)
    if mc.startswith('mlist') : await mlist(ch)
    if mc.startswith('mdel'):
        *dels, = map(int, mc[5:].split())
        for i in sorted(dels)[::-1] : mdel(i)
        await mlist(ch)
    if mc == '<<' or mc == '>>':
        if mc == '>>':
            next_music()
        else:
            prev_music()
        next_b = False
        b = playstate
        await stop_player()
        await asyncio.sleep(1)
        playstate = b
        if playstate == '>' : await move_voice_channel(message.author)
    if all([x == '+' for x in mc]) and len(plist) and len(mc):
        plist.items[get_pindex()].volume = min(max(plist.items[get_pindex()].volume + 5 * mc.count('+'), 0), 100)
        if player != None : player.volume = plist.items[get_pindex()].volume / 100
        plist.saveitems()
        await mlist(ch)
    if all([x == '-' for x in mc]) and len(plist) and len(mc):
        plist.items[get_pindex()].volume = min(max(plist.items[get_pindex()].volume - 5 * mc.count('-'), 0), 100)
        if player != None : player.volume = plist.items[get_pindex()].volume / 100
        plist.saveitems()
        await mlist(ch)
    if mc.startswith('mswap '):
        a, b = map(int, mc[6:].split())
        mswap(a, b)
        await mlist(ch)
    if mc.startswith('mloop'):
        mloop_b = not mloop_b
        await mlist(ch)
    if mc.startswith('mdl') : await mdl(ch, int(mc[4:]))
    if mc.startswith('<<< http://www.nicovideo.jp/mylist/'):
        await mmyilist(ch, mc[4:])

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.author == client.user : return
    mc = message.content
    ch = message.channel
    id = message.author.id
    await music_cmd(message)
    if message.content.startswith('help') : await client.send_message(ch, help)

plist = playlist(playlistfile, musicdir)
pdown = downloader(niconico_user, niconico_password, musicdir)
client.run(token)
