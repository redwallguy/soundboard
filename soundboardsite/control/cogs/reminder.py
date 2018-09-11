from discord.ext import commands

class ReminderCog:

    def __init__(self, bot):
        self.bot = bot

    async def no_reminder(ctx):
        if remindObj.is_pending(ctx.author.id):
            return False
        else:
            return True

    @commands.command()
    @commands.check(no_reminder)
    async def remindat(ctx, date: to_date, msg=None):
        """
        Sends reminder back to channel at time specified by [date] with the given message.
        Date should be formatted as mm/dd/yyyy/hh:mm (UTC time).

        If no message is provided, then the message '[author] has been reminded!' will be sent by default.
        The furthest in the future you can set a reminder is 2 weeks.
        Each user may only have one reminder pending, with maximum 30 total reminders over the entire server.
        """
        default_msg = "<@" + str(ctx.author.id) + ">" + " has been reminded!"
        if msg is None:
            remind.apply_async(args=[ctx.author.id, default_msg], eta=date)
            remindObj.add_user(ctx.author.id)
            return
        else:
            remind.apply_async(args=[ctx.author.id, "<@" + str(ctx.author.id) + "> " + msg], eta=date)
            remindObj.add_user(ctx.author.id)

    @bot.command()
    @commands.check(no_reminder)
    async def remindafter(ctx, hours: int, minutes: int, msg=None):
        """
        Sends reminder back to the channel after [hours] hours and [minutes] minutes, with the given message.

        If no message is provided, then the message '[author] has been reminded!' will be sent by default.
        The furthest in the future you can set a reminder is 2 weeks.
        Each user may only have one reminder pending, with maximum 30 total reminders over the entire server.
        """
        default_msg = "<@" + str(ctx.author.id) + ">" + " has been reminded!"
        delay_in_sec = (hours * 3600) + (minutes * 60)
        if hours < 0 or minutes < 0:
            await ctx.send("I can't go back in time, sorry.")
            return
        if delay_in_sec > 1209600:
            await ctx.send("You can only set a reminder up to 2 weeks in advance.")
            return
        if msg is None:
            remind.apply_async(args=[ctx.author.id, default_msg], countdown=delay_in_sec)
            remindObj.add_user(ctx.author.id)
            return
        else:
            remind.apply_async(args=[ctx.author.id, "<@" + str(ctx.author.id) + "> " + msg], countdown=delay_in_sec)
            remindObj.add_user(ctx.author.id)
            return

    @remindat.error
    async def remindat_error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Your reminder time is bad. Type !help remindat to see the rules for setting a reminder.")

def setup(bot):
    bot.add_cog(ReminderCog(bot))