import discord
import asyncio
import os
from discord.ext import commands
from django.core.management.base import BaseCommand
from ...cogs.utils import checks
import logging
import traceback


class Command(BaseCommand):
    def handle(self, *args, **options):


        # Variable imports and client initializations
        disc_token = os.environ.get('DISCORD_TOKEN')
        bot = commands.Bot(command_prefix='+')

        # Logging and checks
        logging.basicConfig(level=logging.INFO)
        checks.master_check(bot)


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

        @bot.event
        async def on_message(message): #VoiceCog playhelper command because help clip is in filesystem
            if message.content == "+help":
                if message.author.voice is not None and not message.author.bot:
                    if not bot.get_cog("VoiceCog").alreadyConnected(message.author.voice.channel): #bot.get_cog returns class instance
                        if not bot.get_cog("VoiceCog").alreadyInVoice():
                            vc = await message.author.voice.channel.connect()
                        else:
                            vc = bot.get_cog("VoiceCog").alreadyInVoice()
                            await vc.move_to(message.author.voice.channel)
                        vc.play(discord.FFmpegPCMAudio('./command_sounds/help.mp3'))
                    else:
                        vc = bot.get_cog("VoiceCog").clientFromChannel(message.author.voice.channel)
                        if not vc.is_playing():
                            vc.play(discord.FFmpegPCMAudio('./command_sounds/help.mp3'))
            await bot.process_commands(message)

        # Run bot
        extensions = ["control.cogs.admin",
                      "control.cogs.voice",]

        for extension in extensions:
            bot.load_extension(extension)

        try:
            bot.run(disc_token)
        except Exception as e:
            logging.info(traceback.print_exc())

#TODO convert command_sounds into playHelper paradigm, make commandsounds board which is locked from all but superuser
