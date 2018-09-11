import discord
import asyncio
import os
from discord.ext import commands
import redis
import json
import control.models as models
import time
from django.core.management.base import BaseCommand
from control.cogs.utils import checks
import logging


class Command(BaseCommand):
    def handle(self, *args, **options):
        class boardState:
            def __init__(self):
                self.currentBoard = "kripp"

            def changeCurrent(self, board):
                self.currentBoard = board
        class introState:
            def __init__(self, introDict={}):
                self.introDict = introDict

            def changeIntro(self, uid, songName=None, board=None):
                uid = str(uid)
                if songName is not None:
                    self.introDict[uid] = {"songName": songName, "board": board}
                else:
                    if uid in self.introDict:
                        self.introDict.pop(uid)

            def getIntro(self, uid):
                uid = str(uid)
                if uid in self.introDict:
                    return self.introDict[uid]

            def getIntroStr(self, uid):
                uid = str(uid)
                if uid in self.introDict:
                    introStr = "Your intro is " +\
                               self.introDict[uid]["songName"] +\
                               " from the " + self.introDict[uid]["board"] +\
                               " board."
                    return introStr
                else:
                    return "You have no intro at this time."

            def sendToRedis(self, red):
                red.set("intros",json.dumps(self.introDict))

        # Variable imports and client initializations
        #
        #
        #
        discToken = os.environ.get('DISCORD_TOKEN')

        bot = commands.Bot(command_prefix='+')
        r = redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)

        introSt = introState(json.loads(r.get("intros")))
        curbd = boardState()

        # Helper functions and checks
        #
        #
        #
        logging.basicConfig(level=logging.INFO)
        checks.master_check(bot)

        def getBoards():
            return models.Board.objects.all()

                
        @bot.event
        async def on_command(ctx):
            checks.spam.incrSpam(ctx.author.id)

        @bot.event
        async def on_ready():
            if not discord.opus.is_loaded():
                discord.opus.load_opus('libopus.so.0')
            while True:
                checks.spam.flush()
                await asyncio.sleep(5)
        # Run bot
        #
        #
        #
        bot.load_extension("control.cogs.admin")
        while True:
            try:
                bot.run(discToken)
            except Exception as e:
                print(e)
                time.sleep(60)

#TODO convert command_sounds into playHelper paradigm, make commandsounds board which is locked from all but superuser
