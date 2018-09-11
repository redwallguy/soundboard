@bot.command()
@commands.check(isMod)
async def bye(ctx):
    """
    Disconnects bot from voice.
    """
    if alreadyInVoice() is not None:
        await alreadyInVoice().disconnect()


@bot.command(aliases=['sb', 'switch'])
async def switchBoards(ctx, board):
    """
    Switches the soundboard to <board>
    Only usable by mods.
    """
    if switchBoardsHelper(board):
        await listBoardHelper(ctx, board)
        await ctx.send("Board switched to " + board)


def switchBoardsHelper(board):
    boards = getBoards()
    if boards.filter(name__exact=board).exists():
        curbd.changeCurrent(board)
        print("Board switched to " + curbd.currentBoard)
        return True
    else:
        return False


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

    await playHelper(ctx.author, SN, "fav")


@bot.command()
async def play(ctx, songName, b=None):
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
    if await playHelper(ctx.author, songName, b):
        return
    else:
        ctx.send("Only humans in voice channels accepted here.")


async def playHelper(member, songName, board):
    boards = getBoards()
    print(board)
    if member.voice is not None and not member.bot:
        b_to_search = boards.get(name__exact=board)
        clip_set = b_to_search.clip_set.all()
        try:
            song = clip_set.get(name__exact=songName)
            songUrl = song.sound.url
            if not alreadyConnected(member.voice.channel):
                if not alreadyInVoice():
                    vc = await member.voice.channel.connect()
                else:
                    vc = alreadyInVoice()
                    await vc.move_to(member.voice.channel)
                vc.play(discord.FFmpegPCMAudio(songUrl))
            else:
                vc = clientFromChannel(member.voice.channel)
                if not vc.is_playing():
                    vc.play(discord.FFmpegPCMAudio(songUrl))
            return True
        except ObjectDoesNotExist:
            print("Name does not match, searching aliases...")
            try:
                aliConn = models.Alias.objects.all().get(name__exact=
                                                         songName,
                                                         clip__board__name__exact=
                                                         board)
                songUrl = aliConn.clip.sound.url
                if not alreadyConnected(member.voice.channel):
                    if not alreadyInVoice():
                        vc = await member.voice.channel.connect()
                    else:
                        vc = alreadyInVoice()
                        await vc.move_to(member.voice.channel)
                    vc.play(discord.FFmpegPCMAudio(songUrl))
                else:
                    vc = clientFromChannel(member.voice.channel)
                    if not vc.is_playing():
                        vc.play(discord.FFmpegPCMAudio(songUrl))
                return True
            except ObjectDoesNotExist:
                print("No aliases match on specified board")
                return True
    else:
        return False


# Helper commands
#
#
#
@bot.command(aliases=['ls'])
async def listBoard(ctx, bd=None):
    """
    Shows the list of soundboards available.

    If <bd> is '-c', then all clips from the current board are listed,
    as well as their aliases.
    """
    await listBoardHelper(ctx, bd)


async def listBoardHelper(ctx, board):
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


# Voice join intro functions
#
#
#
async def clipExists(songName, board):
    boards = getBoards()
    b_to_search = boards.get(name__exact=board)
    clip_set = b_to_search.clip_set.all()
    try:
        song = clip_set.get(name__exact=songName)
        return True
    except ObjectDoesNotExist:
        print("Name does not match, searching aliases...")
        try:
            aliConn = models.Alias.objects.all().get(name__exact=
                                                     songName,
                                                     clip__board__name__exact=
                                                     board)
            return True
        except ObjectDoesNotExist:
            print("No aliases match on specified board")
            return False


@bot.command()
async def setIntro(ctx, songName, board):
    """
    Sets an intro from the soundboard that plays whenever you
    enter a voice channel.
    """
    if clipExists(songName, board):
        introSt.changeIntro(ctx.author.id, songName, board)
        introSt.sendToRedis(r)
        await ctx.send("Success")
    else:
        await ctx.send("That clip does not exist. Rip.")


@bot.command()
async def remIntro(ctx):
    """
    Removes your intro.
    """
    introSt.changeIntro(ctx.author.id)
    introSt.sendToRedis(r)


@bot.command()
async def myIntro(ctx):
    """
    Returns your intro.
    """
    await ctx.send(introSt.getIntroStr(ctx.author.id))


@bot.event
async def on_voice_state_update(member, before, after):
    goAhead = False
    if before is None and after.channel.guild in bot.guilds and introSt.getIntro(member.id) is not None:
        goAhead = True
    else:
        try:
            if before.channel is None and after.channel.guild in bot.guilds and introSt.getIntro(member.id) is not None:
                goAhead = True
        except:
            pass
    if goAhead:
        board = introSt.getIntro(member.id)["board"]
        songName = introSt.getIntro(member.id)["songName"]
        await playHelper(member, songName, board)

    if await num_in_voice(member.guild) == 1 and alreadyInVoice() is not None:
        await alreadyInVoice().disconnect()

    # TODO add command sound for "now it's a party" or something and trigger it if numvoice == 10


async def num_in_voice(guild):
    num_mem = 0
    for chan in guild.voice_channels:
        num_mem += len(chan.members)
    return num_mem


# Milton app commands
#
#
#
@bot.command(hidden=True)
async def milton(ctx, clip, board, discid):
    try:
        web_id = ctx.webhook_id
    except AttributeError:
        return
    for guild in bot.guilds:
        member = discord.utils.get(guild.members, id=discid)
        if member is not None and member.voice is not None:
            break
    if member is not None and member.voice is not None:
        playHelper(member, clip, board)

