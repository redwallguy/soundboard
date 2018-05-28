import discord
import asyncio
import os
from discord.ext import commands
import boto3
import redis
import json
import shutil
import re
import control.models as models
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        class boardState:
            def __init__(self):
                self.currentBoard = ""

            def changeCurrent(self, board):
                self.currentBoard = board
        class spamState:
            def __init__(self):
                self.spam_dict = {}

            def incrSpam(self, authId):
                if authId not in self.spam_dict:
                    self.spam_dict[authId] = 1
                elif self.spam_dict[authId] < 5:
                    self.spam_dict[authId] += 1
                else:
                    self.spam_dict = 5

            def flush(self):
                self.spam_dict = {}
        #-----------------------------------------------------------
        # Variable imports and client initializations
        #-----------------------------------------------------------
        discToken = os.environ.get('DISCORD_TOKEN')

        bot = commands.Bot(command_prefix='+')
        r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

        overlord = int(r.get("discord_admin"))
        mods = [int(x) for x in r.lrange("mods",0,-1)]
        banned = [int(x) for x in r.lrange("banned",0,-1)]
        curbd = boardState()
        spamOb = spamState()

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

        def getBoards():
            return models.Board.objects.all()
            

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
                if ctx.author.id in spamOb.spam_dict:
                    if spamOb.spam_dict[ctx.author.id] == 5:
                        return False
                return True
                
        @bot.event
        async def on_command(ctx):
            spamOb.incrSpam(ctx.author.id)

        @bot.event
        async def on_ready():
            if not discord.opus.is_loaded():
                discord.opus.load_opus('libopus.so.0')
            switchBoardsHelper("kripp")
            while True:
                spamOb.flush()
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
            uid = member.id
            if uid not in mods and uid not in banned and uid != overlord:
                r.lpush("banned", uid)
                banned.append(uid)
                if message.author.voice is not None and not message.author.bot:
                    if not alreadyConnected(message.author.voice.channel):
                        vc = await message.author.voice.channel.connect()
                        vc.play(discord.FFmpegPCMAudio('./command_sounds/banneddude.mp3'))
                    else:
                        vc = clientFromChannel(message.author.voice.channel)
                        if not vc.is_playing():
                            vc.play(discord.FFmpegPCMAudio('./command_sounds/banneddude.mp3'))
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

        @bot.command()
        async def ping(ctx):
            await ctx.send("pong")

        #-----------------------------------------------------------
        # Bot commands and helper functions (audio)
        #-----------------------------------------------------------
        @bot.command()
        @commands.check(isMod)
        async def bye(ctx):
            """
            Disconnects bot from voice channel user is in
            """
            if ctx.author.voice is not None:
                if alreadyConnected(ctx.author.voice.channel):
                    vc = clientFromChannel(ctx.author.voice.channel)
                    await vc.disconnect()

        @bot.command(aliases=['sb','switch'])
        @commands.check(isMod)
        async def switchBoards(ctx, board):
            """
            Switches the soundboard to <board>
            Only usable by mods.
            """
            switchBoardsHelper(board)
            await ctx.send("Board switched to " + board)

        def switchBoardsHelper(board):
            boards = getBoards()
            if boards.filter(name__exact=board).exists():
                curbd.changeCurrent(board)
                print("Board switched to " + curbd.currentBoard)
                
        def alreadyConnected(vc):
            for client in bot.voice_clients:
                if vc == client.channel:
                    return True
            return False

        def alreadyInVoice():
            for client in bot.voice_clients:
                if client.is_connected():
                    return client
            return False

        def clientFromChannel(chan):
            for client in bot.voice_clients:
                if chan == client.channel:
                    return client

        @bot.command()
        async def playf(ctx, SN):
            """
            Plays clip from 'favorites' board
            """

            await playHelper(ctx,SN,"fav")

        @bot.command()
        async def play(ctx, SN, b=None):
            """
            Plays clip <SN> or any clip it is an alias of.

            Ex. +play hellothere
                +play hello

            If <b> is specified, then the clip will be searched for in board <b>.
            Else, it will be searched for in the current board.

            Ex. +play rng kripp
            """
            if b is None:
                b=curbd.currentBoard
            await playHelper(ctx,SN,b)
                        
        async def playHelper(ctx, songName, board):
            boards = getBoards()
            print(board)
            if ctx.author.voice is not None and not ctx.author.bot:
                b_to_search = boards.get(name__exact=board)
                clip_set = b_to_search.clip_set.all()
                try:
                    song = clip_set.get(name__exact=songName)
                    songUrl = song.sound.url
                    if not alreadyConnected(ctx.author.voice.channel):
                        if not alreadyInVoice():
                            vc = await ctx.author.voice.channel.connect()
                        else:
                            vc = alreadyInVoice()
                            await vc.move_to(ctx.author.voice.channel)
                        vc.play(discord.FFmpegPCMAudio(songUrl))
                    else:
                        vc = clientFromChannel(ctx.author.voice.channel)
                        if not vc.is_playing():
                            vc.play(discord.FFmpegPCMAudio(songUrl))
                    return
                except ObjectDoesNotExist:
                    print("Name does not match, searching aliases...")
                    try:
                        aliConn = models.Alias.objects.all().get(name__exact=
                                                                 songName,
                                                                 clip__board__name__exact=
                                                                 board)
                        songUrl = aliConn.clip.sound.url
                        if not alreadyConnected(ctx.author.voice.channel):
                            if not alreadyInVoice():
                                vc = await ctx.author.voice.channel.connect()
                            else:
                                vc = alreadyInVoice()
                                await vc.move_to(ctx.author.voice.channel)
                            vc.play(discord.FFmpegPCMAudio(songUrl))
                        else:
                            vc = clientFromChannel(ctx.author.voice.channel)
                            if not vc.is_playing():
                                vc.play(discord.FFmpegPCMAudio(songUrl))
                        return
                    except ObjectDoesNotExist:
                        print("No aliases match on specified board")
                        return
            else:
                await ctx.send("Only humans in voice channels accepted here")
                return
        #-----------------------------------------------------------
        # Helper commands .
        #-----------------------------------------------------------
        @bot.command(aliases=['ls'])
        async def listBoard(ctx, bd=None):
            """
            Shows the list of soundboards available.

            If <bd> is '-c', then all clips from the current board are listed,
            as well as their aliases.
            """
            if bd is None:
                shmsg="Boards\n--------------------\n"
                boards = getBoards()
                for b in boards:
                    shmsg+=b.name+"\n"
                await ctx.send(shmsg)
                return
            elif bd=="-c":
                shmsg=curbd.currentBoard+"\n----------------\n"
                boards=getBoards()
                b_to_cycle=boards.get(name__exact=curbd.currentBoard)
                for c in b_to_cycle.clip_set.all():
                    shmsg+=c.name+" ["
                    for a in c.alias_set.all():
                        shmsg+=a.name+","
                    shmsg+="]\n"
                await ctx.send(shmsg)
                return
            else:
                shmsg=bd+"\n----------------\n"
                boards = getBoards()
                try:
                    b_to_cycle=boards.get(name__exact=bd)
                    for c in b_to_cycle.clip_set.all():
                        shmsg+=c.name+" ["
                        for a in c.alias_set.all():
                            shmsg+=a.name+","
                        shmsg+="]\n"
                    await ctx.send(shmsg)
                    return
                except ObjectDoesNotExist:
                    return

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

