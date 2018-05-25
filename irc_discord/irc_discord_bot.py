#! /usr/bin/env python3

import socket
import discord
import asyncio

client = discord.Client()

bot_token = ''
discord_channel = 'general'
irc_name = 'mybot'
irc_channel = '' # '#test'
irc_sarver = ''

mjcode = 'iso-2022-jp'# 'utf-8'
port = 6667

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((irc_sarver, port))
sock.send(('NICK ' + irc_name + '\r\n').encode(mjcode))
sock.send(' '.join(['USER', irc_name, 'host', 'server', irc_name, '\r\n']).encode(mjcode))
sock.send(' '.join(['JOIN', irc_channel, '\r\n']).encode(mjcode))
sock.setblocking(0)

def irc_send(s):
    sock.send(('PRIVMSG ' + irc_channel + ' :' + s + '\r\n').encode(mjcode, 'ignore'))

async def irc_recv(ch):
    while 1:
        await asyncio.sleep(1)
        try:
            for i in sock.recv(1024).decode(mjcode, 'ignore').strip().split('\n'):
                m = i.split(':', 2)
                if len(m)>1 and '!~' in m[1] and ('PRIVMSG' in m[1] or 'NOTICE' in m[1]):
                    await client.send_message(ch, m[1].split('!~')[0] + ' > ' + m[2])
                elif i.startswith('PING'):
                    sock.send(' '.join(['PONG', i[6:], '\r\n']).encode(mjcode))
        except:
            pass

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    ch = None
    for i in client.servers:
        for j in i.channels:
            if discord_channel == str(j):
                ch = j
                break
    print(['', 'Not '][ch == None] + 'Found Discord Channel')
    print('------')
    if ch : await irc_recv(ch)

@client.event
async def on_message(message):
    if message.author == client.user : return
    irc_send(message.author.name)
    for i in message.content.split('\n'):
        irc_send(' ' + i)

client.run(bot_token)