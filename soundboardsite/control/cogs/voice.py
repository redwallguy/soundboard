import discord
from discord.ext import commands
from .utils import miltonredis, checks
from .. import models
from django.core.exceptions import ObjectDoesNotExist
import logging

logging.basicConfig(level=logging.INFO)


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
            miltonredis.set_json_value("intro", self.introDict)
        else:
            if uid in self.introDict:
                self.introDict.pop(uid)
                miltonredis.set_json_value("intro", self.introDict)

    def getIntro(self, uid):
        uid = str(uid)
        if uid in self.introDict:
            return self.introDict[uid]

    def getIntroStr(self, uid):
        uid = str(uid)
        if uid in self.introDict:
            introStr = "Your intro is " + \
                       self.introDict[uid]["songName"] + \
                       " from the " + self.introDict[uid]["board"] + \
                       " board."
            return introStr
        else:
            return "You have no intro at this time."


introSt = introState(miltonredis.get_json_value("intros"))
curbd = boardState()


def getBoards():
    return models.Board.objects.all()


class VoiceCog:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_mod()
    async def bye(self, ctx):
        """
        Disconnects bot from voice.
        """
        if self.alreadyInVoice() is not None:
            await self.alreadyInVoice().disconnect()


    @commands.command(aliases=['sb', 'switch'])
    async def switchBoards(self, ctx, board):
        """
        Switches the soundboard to <board>
        """
        if self.switchBoardsHelper(board):
            await self.listBoardHelper(ctx, board)
            await ctx.send("Board switched to " + board)


    def switchBoardsHelper(self, board):
        boards = getBoards()
        if boards.filter(name__exact=board).exists():
            curbd.changeCurrent(board)
            print("Board switched to " + curbd.currentBoard)
            return True
        else:
            return False


    def alreadyConnected(self, vc):
        for client in self.bot.voice_clients:
            if vc == client.channel:
                return True
        return False


    def alreadyInVoice(self):
        for client in self.bot.voice_clients:
            if client.is_connected():
                return client
        return False


    def clientFromChannel(self, chan):
        for client in self.bot.voice_clients:
            if chan == client.channel:
                return client


    @commands.command()
    async def playf(self, ctx, SN):
        """
        Plays clip from 'favorites' board
        """

        await self.playHelper(ctx.author, SN, "fav")


    @commands.command()
    async def play(self, ctx, songName, b=None):
        """
        Plays clip <songName> or any clip it is an alias of.

        Ex. +play hellothere
            +play hello

        If <b> is specified, then the clip will be searched for in board <b>.
        Else, it will be searched for in the current board.

        Ex. +play rng kripp
        """
        if b is None:
            b = curbd.currentBoard
        if await self.playHelper(ctx.author, songName, b):
            return
        else:
            ctx.send("Only humans in voice channels accepted here.")


    async def playHelper(self, member, songName, board):
        boards = getBoards()
        if member.voice is not None:
            b_to_search = boards.get(name__exact=board)
            clip_set = b_to_search.clip_set.all()
            try:
                song = clip_set.get(name__exact=songName)
                songUrl = song.sound.url
                if not self.alreadyConnected(member.voice.channel):
                    if not self.alreadyInVoice():
                        vc = await member.voice.channel.connect()
                    else:
                        vc = self.alreadyInVoice()
                        await vc.move_to(member.voice.channel)
                    vc.play(discord.FFmpegPCMAudio(songUrl))
                else:
                    vc = self.clientFromChannel(member.voice.channel)
                    if not vc.is_playing():
                        vc.play(discord.FFmpegPCMAudio(songUrl))
                return True
            except ObjectDoesNotExist:
                logging.info("Name does not match, searching aliases...")
                try:
                    aliConn = models.Alias.objects.all().get(name__exact=
                                                             songName,
                                                             clip__board__name__exact=
                                                             board)
                    songUrl = aliConn.clip.sound.url
                    if not self.alreadyConnected(member.voice.channel):
                        if not self.alreadyInVoice():
                            vc = await member.voice.channel.connect()
                        else:
                            vc = self.alreadyInVoice()
                            await vc.move_to(member.voice.channel)
                        vc.play(discord.FFmpegPCMAudio(songUrl))
                    else:
                        vc = self.clientFromChannel(member.voice.channel)
                        if not vc.is_playing():
                            vc.play(discord.FFmpegPCMAudio(songUrl))
                    return True
                except ObjectDoesNotExist:
                    logging.info("No aliases match on specified board")
                    return True
        else:
            return False


    # Helper commands
    #
    #
    #
    @commands.command(name='listboard', aliases=['ls'])
    async def list_board(self, ctx, bd=None):
        """
        Shows the list of soundboards available.

        If <bd> is '-c', then all clips from the current board are listed,
        as well as their aliases.
        """
        await self.listBoardHelper(ctx, bd)


    async def listBoardHelper(self, ctx, board):
        if board is None:
            shmsg = "Boards\n--------------------\n"
            boards = getBoards()
            for b in boards:
                shmsg += b.name + "\n"
            await ctx.send(shmsg)
            return
        elif board == "-c":
            shmsg = curbd.currentBoard + "\n----------------\n"
            boards = getBoards()
            b_to_cycle = boards.get(name__exact=curbd.currentBoard)
            for c in b_to_cycle.clip_set.all():
                shmsg += c.name + " ["
                for a in c.alias_set.all():
                    shmsg += a.name + ","
                shmsg += "]\n"
            await ctx.send(shmsg)
            return
        else:
            shmsg = board + "\n----------------\n"
            boards = getBoards()
            try:
                b_to_cycle = boards.get(name__exact=board)
                for c in b_to_cycle.clip_set.all():
                    shmsg += c.name + " ["
                    for a in c.alias_set.all():
                        shmsg += a.name + ","
                    shmsg += "]\n"
                await ctx.send(shmsg)
                return
            except ObjectDoesNotExist:
                return


    # Voice join intro functions
    #
    #
    #
    async def clipExists(self, songName, board):
        boards = getBoards()
        b_to_search = boards.get(name__exact=board)
        clip_set = b_to_search.clip_set.all()
        try:
            song = clip_set.get(name__exact=songName)
            return True
        except ObjectDoesNotExist:
            logging.info("Name does not match, searching aliases...")
            try:
                aliConn = models.Alias.objects.all().get(name__exact=
                                                         songName,
                                                         clip__board__name__exact=
                                                         board)
                return True
            except ObjectDoesNotExist:
                print("No aliases match on specified board")
                return False


    @commands.command(name='setintro')
    async def set_intro(self, ctx, songName, board):
        """
        Sets an intro from the soundboard that plays whenever you
        enter a voice channel.
        """
        if self.clipExists(songName, board):
            introSt.changeIntro(ctx.author.id, songName, board)
            await ctx.send("Success")
        else:
            await ctx.send("That clip does not exist. Rip.")


    @commands.command(name='remintro')
    async def rem_intro(self, ctx):
        """
        Removes your intro.
        """
        introSt.changeIntro(ctx.author.id)


    @commands.command(name='myintro')
    async def my_intro(self, ctx):
        """
        Returns your intro.
        """
        await ctx.send(introSt.getIntroStr(ctx.author.id))


    async def on_voice_state_update(self, member, before, after):
        goAhead = False
        if before is None and after.channel.guild in self.bot.guilds and introSt.getIntro(member.id) is not None:
            goAhead = True
        else:
            try:
                if before.channel is None and after.channel.guild in self.bot.guilds and introSt.getIntro(member.id) is not None:
                    goAhead = True
            except:
                pass
        if goAhead:
            board = introSt.getIntro(member.id)["board"]
            songName = introSt.getIntro(member.id)["songName"]
            await self.playHelper(member, songName, board)

        if self.num_in_voice(member.guild) == 1 and self.alreadyInVoice() is not None:
            await self.alreadyInVoice().disconnect()

        # TODO add command sound for "now it's a party" or something and trigger it if numvoice == 10
        # TODO play "great to see the gang back together" when me, jon, iain, dolan, tim all on


    def num_in_voice(self, guild):
        num_mem = 0
        for chan in guild.voice_channels:
            num_mem += len(chan.members)
        return num_mem


    # Milton app commands
    #
    #
    #
    @commands.command(hidden=True)
    async def milton(self, ctx, clip, board, discid):
        try:
            web_id = ctx.webhook_id
        except AttributeError:
            return
        for guild in self.bot.guilds:
            member = discord.utils.get(guild.members, id=discid)
            if member is not None and member.voice is not None:
                break
        try:
            if member is not None and member.voice is not None:
                await self.playHelper(member, clip, board)
        except AttributeError:
            pass

def setup(bot):
    bot.add_cog(VoiceCog(bot))