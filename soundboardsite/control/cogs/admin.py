import discord
from discord.ext import commands
from .utils import checks

class AdminCog:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='makemod')
    @checks.is_owner()
    async def make_mod(self, ctx, mod: int):
        """
        Elevates a user to become a mod.
        """
        checks.creds.add_mod(mod)
        await ctx.send("You have become one of my blessed messengers. Welcome to Eternity.")

    @commands.command(name='delmod')
    @checks.is_owner()
    async def del_mod(self, ctx, mod: int):
        """
        Strips a user of their mod privileges.
        """
        checks.creds.del_mod(mod)
        await ctx.send("You are cast down from Eternity. Repent, that you may one day rejoin me in the light.")

    @commands.command()
    @checks.is_mod()
    async def ban(self, ctx, banned: int):
        """
        Ban member.
        Only usable by mods.
        """
        if banned != checks.creds.overlord:
            checks.creds.add_banned(banned)
            await ctx.send("You are banished from my garden. BEGONE!")
            if ctx.author.voice is not None:
                for vc in self.bot.voice_clients:
                    if vc.channel == ctx.author.voice.channel:
                        if not vc.is_playing():
                            vc.play(discord.FFmpegPCMAudio('./command_sounds/bannedude.mp3'))
                        return
                vc = await ctx.author.voice.channel.connect()
                vc.play(discord.FFmpegPCMAudio('./command_sounds/banneddude.mp3'))

    @commands.command()
    @checks.is_mod()
    async def unban(self, ctx, banned: int):
        """
        Unban member.
        Only usable by mods.
        """
        checks.creds.rem_banned(banned)
        await ctx.send("Welcome back into my garden, child.")

    @commands.command(name='getmods')
    async def get_mods(self, ctx):
        """
        Display list of mods.
        """
        modmsg = "These are your mods, with hella nice bods.\n--------------------\n"

        for mod in checks.creds.mods:
            print(mod)
            modmem = await self.bot.get_user_info(mod)
            modmsg += modmem.name + "\n"
        await ctx.send(modmsg)

    @commands.command(name='getbanned')
    async def get_banned(self, ctx):
        """
        Display list of banned members.
        """
        banmsg = "These guys are banned. They probably like sand.\n--------------------\n"

        for banned in checks.creds.banned:
            banmem = await self.bot.get_user_info(banned)
            banmsg += banmem.name + "\n"
        await ctx.send(banmsg)


def setup(bot):
    bot.add_cog(AdminCog(bot))
