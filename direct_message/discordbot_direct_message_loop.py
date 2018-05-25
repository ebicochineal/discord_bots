#! /usr/bin/env python3
import discord
import asyncio

client = discord.Client()

token = ''
target_id = ''
message = 'test'

def find_user():
    for s in client.servers:
        for m in s.members:
            if target_id in str(m) : return m
    return None

async def direct_message_loop():
    print('direct_message_loop')
    while 1:
        await asyncio.sleep(5)# 5second
        user = find_user()
        if user:
            print('send message')
            await client.send_message(user, message)

@client.event
async def on_ready():
    print('on_ready')
    asyncio.ensure_future(direct_message_loop())

@client.event
async def on_message(message):
    if message.author == client.user : return
    mc = message.content
    ch = message.channel
    id = message.author.id

client.run(token)