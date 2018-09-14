from discord.ext import commands
from celery import Celery
import os
from .utils import miltonredis as mr
from .utils import checks
from .utils import converters
import requests

app = Celery('soundboard', broker=os.environ.get("REDIS_URL"))

@app.task(name='soundboardsite.control.cogs.reminder.remind')
def remind(aid, message):
    remindObj.dec_user(aid)
    requests.post(os.environ.get("WEBHOOK_URL"), headers={'Content-Type': 'application/json'},
                  json={'content': message})

def reminder_lim_check(ctx):
    if remindObj.num_pending(ctx.author.id) <= remindObj.REMINDER_LIMIT:
        return True
    else:
        return False

def reminder_lim():
    return commands.check(reminder_lim_check)

class Remind:

    def __init__(self):
        self.REMINDER_LIMIT = 5
        if mr.get_value("reminder") is None:
            mr.set_json_value("reminder", {})
            self.remind_dict = {}
        else:
            self.remind_dict = mr.get_json_value("reminder")

    def num_pending(self, aid):
        aid = str(aid)
        if aid in self.remind_dict:
            return self.remind_dict[aid]
        else:
            return 0

    def inc_user(self, aid):
        aid = str(aid)
        if self.num_pending(aid) == 0:
            self.remind_dict[aid] = 1
        else:
            self.remind_dict[aid] += 1
        mr.set_json_value("reminder", self.remind_dict)

    def dec_user(self, aid):
        aid = str(aid)
        if self.num_pending(aid) <= 0:
            self.remind_dict[aid] = 0
        else:
            self.remind_dict[aid] -= 1
        mr.set_json_value("reminder", self.remind_dict)

remindObj = Remind()


class ReminderCog:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @reminder_lim()
    @checks.is_mod()
    async def remindat(self, ctx, date: converters.to_date, msg=None):
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
            remindObj.inc_user(ctx.author.id)
            return
        else:
            remind.apply_async(args=[ctx.author.id, "<@" + str(ctx.author.id) + "> " + msg], eta=date)
            remindObj.inc_user(ctx.author.id)

    @commands.command()
    @reminder_lim()
    @checks.is_mod()
    async def remindafter(self, ctx, hours: int, minutes: int, msg=None):
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
            remindObj.inc_user(ctx.author.id)
            return
        else:
            remind.apply_async(args=[ctx.author.id, "<@" + str(ctx.author.id) + "> " + msg], countdown=delay_in_sec)
            remindObj.inc_user(ctx.author.id)
            return

    @remindat.error
    async def remindat_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Your reminder time is bad. Type !help remindat to see the rules for setting a reminder.")

def setup(bot):
    bot.add_cog(ReminderCog(bot))