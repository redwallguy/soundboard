import discord
import asyncio
import os
from discord.ext import commands
import boto3
import redis
import json
import shutil
import re

#-----------------------------------------------------------
# Variable imports and client initializations
#-----------------------------------------------------------
discToken = os.environ.get('DISCORD_TOKEN')
bucketName = os.environ.get('S3_BUCKET_NAME')

bot = commands.Bot(command_prefix='+')
r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

boards = r.lrange("boards",0,-1)
overlord = int(r.get("discord_admin"))
mods = [int(x) for x in r.lrange("mods",0,-1)]
banned = [int(x) for x in r.lrange("banned",0,-1)]
aliases = {}
ali={}
currentBoard = ""

s3 = boto3.resource('s3')
s3client = boto3.client('s3')

spam_dict = {}

#-----------------------------------------------------------
# Helper functions and checks
#-----------------------------------------------------------
async def isMod(ctx):
    if ctx.author.id in mods or ctx.author.id == overlord:
        return True
    else:
        return False

async def isAdmin(ctx):
    return ctx.author.id == overlord

async def getBoards():
    return boards

#-----------------------------------------------------------
# Spam prevention
#-----------------------------------------------------------
#Look at @cooldown decorator for future bots
@bot.check
async def notBanned(ctx):
    if ctx.author.id in banned and ctx.author.id != overlord:
        return False
    else:
        return True

@bot.check
async def notBot(ctx):
    return not ctx.author.bot

@bot.check
async def stopSpamming(ctx):
    if ctx.author.id == overlord:
        return True
    else:
        if ctx.author.id in spam_dict:
            if spam_dict[ctx.author.id] == 5:
                return False
        return True
        
@bot.event
async def on_command(ctx):
    if ctx.author.id not in spam_dict:
        spam_dict[ctx.author.id] = 1
    else:
        spam_dict[ctx.author.id] += 1
        if spam_dict[ctx.author.id] > 5:
            spam_dict[ctx.author.id] = 5

def flushTempBan():
    global spam_dict
    spam_dict={}

@bot.event
async def on_ready():
    switchBoardsHelper("kripp")
    if not discord.opus.is_loaded():
        discord.opus.load_opus()
    while True:
        flushTempBan()
        await asyncio.sleep(5)

#-----------------------------------------------------------
# Bot commands (Administrative)
#-----------------------------------------------------------
#change to make play Elohim quotes on command (pass ctx?)

@bot.command()
@commands.check(isAdmin)
async def makeMod(ctx,member: discord.Member):
    """
    Promote member to mod.
    Only usable by [REDACTED]
    """
    uid = member.id
    if uid not in mods:
        r.lpush("discord_mods",uid)
        mods.append(uid)
        await ctx.send("Come, and dine with gods.")
        return True
    else:
        return False

@bot.command()
@commands.check(isAdmin)
async def delMod(ctx,member: discord.Member):
    """
    Remove mod powers from member.
    Only usable by [REDACTED]
    """
    uid = member.id
    if uid in mods:
        r.lrem("discord_mods", uid)
        mods.remove(uid)
        await ctx.send("How the mighty have fallen...")
        return True
    else:
        return False

@bot.command()
@commands.check(isMod)
async def ban(ctx, member: discord.Member):
    """
    Ban member.
    Only usable by mods.
    """
    #use CEASE from Elohim
    uid = member.id
    if uid not in mods and uid not in banned and uid != overlord:
        r.lpush("banned", uid)
        banned.append(uid)
        await ctx.send("Begone!")
        return True
    else:
        return False

@bot.command()
@commands.check(isMod)
async def unban(ctx,member: discord.Member):
    """
    Unban member.
    Only usable by mods.
    """
    uid = member.id
    if uid in banned:
        r.lrem("banned", uid)
        banned.remove(uid)
        await ctx.send("Welcome back, child.")
        return True
    else:
        return False

@bot.command()
async def getMods(ctx):
    """
    Display list of mods.
    """
    modmsg = "These are your current rulers of the Boards:\n"\
             "-------------------------------------------\n"
    for mod in mods:
        modmem = await bot.get_user_info(mod)
        modmsg += modmem.name + "\n"
    await ctx.send(modmsg)

@bot.command()
async def getBannedOnes(ctx):
    """
    Display list of banned members.
    """
    banmsg = "These are the exiles. Look upon them and weep.\n"\
             "----------------------------------------------\n"
    for banppl in banned:
        banmem = await bot.get_user_info(banppl)
        banmsg += banmem.name + "\n"
    await ctx.send(banmsg)

#-----------------------------------------------------------
# Bot commands and helper functions (audio)
#-----------------------------------------------------------
@bot.command()
async def bye(ctx):
    """
    Disconnects bot from voice channel user is in
    """
    if ctx.author.voice is not None:
        if alreadyConnected(ctx.author.voice.channel):
            vc = clientFromChannel(ctx.author.voice.channel)
            await vc.disconnect()

@bot.command(aliases=['sb','switch'])
async def switchBoards(ctx, board):
    """
    Switches the soundboard to {board}
    Only usable by mods.
    """
    switchBoardsHelper(board)
    await ctx.send("Board switched to " + board)

def switchBoardsHelper(board):
    if board in boards:
        try:
            shutil.rmtree('./cache')
            os.mkdir('./cache')
        except Exception as e:
            print(e)
            
        try:
            foldDict = s3client.list_objects_v2(Bucket=bucketName,
                                                Prefix=board+'/')["Contents"]

            for obj in foldDict:
                if obj["Key"].endswith("mp3"):
                    print(obj["Key"])
                    musicRegex = re.compile(r"(?<="+re.escape(board)+r"/).+?mp3")
                    fileName = musicRegex.search(obj["Key"]).group(0)
                    s3.Bucket(bucketName).download_file(obj["Key"],'cache/'+fileName)
                if obj["Key"].endswith("json"):
                    print(obj["Key"])
                    s3.Bucket(bucketName).download_file(obj["Key"],'cache/aliases.json')
        except Exception as e:
            print(e)
        with open('./cache/aliases.json') as f:
            global aliases
            aliases = json.load(f)
        global currentBoard
        currentBoard = board
def alreadyConnected(vc):
    for client in bot.voice_clients:
        if vc == client.channel:
            return True
    return False

def clientFromChannel(chan):
    for client in bot.voice_clients:
        if chan == client.channel:
            return client

@bot.command()
async def play(ctx, SN, b="None"):
    """
    Plays clip {SN} or any clip it is an alias of.

    Ex. +play hellothere
        +play hello

    If {b} is specified, then the clip will be searched for in board {b}.
    Else, it will be searched for in the current board.

    Ex. +play rng kripp
    """
    await playHelper(ctx,SN,b)
                
async def playHelper(ctx, songName, board="None"):
    if board == "None":
        if ctx.author.voice is not None and not ctx.author.bot:
            for song in aliases:
                if songName+'.mp3' == song:
                    if not alreadyConnected(ctx.author.voice.channel):
                        vc = await ctx.author.voice.channel.connect()
                        vc.play(discord.FFmpegPCMAudio('./cache/'+song))
                    else:
                        vc = clientFromChannel(ctx.author.voice.channel)
                        if not vc.is_playing():
                            vc.play(discord.FFmpegPCMAudio('./cache/'+song))
                    return
                for alias in aliases[song]:
                    if songName == alias:
                        if not alreadyConnected(ctx.author.voice.channel):
                            vc = await ctx.author.voice.channel.connect()
                            vc.play(discord.FFmpegPCMAudio('./cache/'+song))
                        else:
                            vc = clientFromChannel(ctx.author.voice.channel)
                            if not vc.is_playing():
                                vc.play(discord.FFmpegPCMAudio('./cache/'+song))
                        return
        else:
            ctx.send("Only humans in voice channels accepted here")
    elif board in boards:
        try:
            s3.Bucket(bucketName).download_file(board+'/aliases.json','ali.json')
            with open('ali.json') as f:
                global ali
                ali = json.load(f)
            if ctx.author.voice is not None and not ctx.author.bot:
                for song in ali:
                    if songName+'.mp3' == song:
                        if not alreadyConnected(ctx.author.voice.channel):
                            vc = await ctx.author.voice.channel.connect()
                            s3.Bucket(bucketName).download_file(board+'/'+song,'temp3.mp3')
                            vc.play(discord.FFmpegPCMAudio('temp3.mp3'))
                        else:
                            vc = clientFromChannel(ctx.author.voice.channel)
                            if not vc.is_playing():
                                s3.Bucket(bucketName).download_file(board+'/'+song,'temp3.mp3')
                                vc.play(discord.FFmpegPCMAudio('temp3.mp3'))
                        return
                    for alias in ali[song]:
                        if songName == alias:
                            if not alreadyConnected(ctx.author.voice.channel):
                                vc = await ctx.author.voice.channel.connect()
                                s3.Bucket(bucketName).download_file(board+'/'+song,'temp3.mp3')
                                vc.play(discord.FFmpegPCMAudio('temp3.mp3'))
                            else:
                                vc = clientFromChannel(ctx.author.voice.channel)
                                if not vc.is_playing():
                                    s3.Bucket(bucketName).download_file(board+'/'+song,'temp3.mp3')
                                    vc.play(discord.FFmpegPCMAudio('temp3.mp3'))
                            return
            else:
                ctx.send("Only humans in voice channels accepted here")
        except Exception as e:
            print(e)
    elif board == "command":
        if ctx.author.voice is not None and not ctx.author.bot:
            if songName == "help":
                if not alreadyConnected(ctx.author.voice.channel):
                    vc = await ctx.author.voice.channel.connect()
                    vc.play(discord.FFmpegPCMAudio('./command_sounds/help.mp3'))
                else:
                    vc = clientFromChannel(ctx.author.voice.channel)
                    if not vc.is_playing():
                        vc.play(discord.FFmpegPCMAudio('./command_sounds/help.mp3'))
                return
            elif songName == "bye":
                if not alreadyConnected(ctx.author.voice.channel):
                    vc = await ctx.author.voice.channel.connect()
                    vc.play(discord.FFmpegPCMAudio('./command_sounds/cease.mp3'))
                else:
                    vc = clientFromChannel(ctx.author.voice.channel)
                    if not vc.is_playing():
                        vc.play(discord.FFmpegPCMAudio('./command_sounds/cease.mp3'))
                return
#-----------------------------------------------------------
# Helper commands .
#-----------------------------------------------------------
@bot.command(aliases=['ls'])
async def listBoard(ctx, bd = "None"):
    """
    Shows the list of soundboards available.

    If {board} is specified, then all clips from {board} are listed,
    as well as their aliases.
    """
    if bd == "None":
        shmsg = "Boards:\n------------------------------\n"
        for b in boards:
            shmsg += b + "\n"
        await ctx.send(shmsg)
    elif bd == "Current":
        shmsg = "Board: "+currentBoard+"\n-------------------------\n"
        for s in aliases:
            shmsg += s + ' ['
            for m in aliases[s]:
                shmsg += m+','
            shmsg += ']\n'
        await ctx.send(shmsg)

@bot.event
async def on_message(message):
    if message.content == "+help":
        if message.author.voice is not None and not message.author.bot:
            if not alreadyConnected(message.author.voice.channel):
                vc = await message.author.voice.channel.connect()
                vc.play(discord.FFmpegPCMAudio('./command_sounds/help.mp3'))
            else:
                vc = clientFromChannel(message.author.voice.channel)
                if not vc.is_playing():
                    vc.play(discord.FFmpegPCMAudio('./command_sounds/help.mp3'))
    await bot.process_commands(message)

#-----------------------------------------------------------
# Run bot
#-----------------------------------------------------------
bot.run(discToken)
