from discord.ext import commands
from . import miltonredis
import logging

class CheckCreds:
    def __init__(self):
        self.overlord = int(miltonredis.get_value("discord_admin")) # me
        self.mods = [int(x) for x in miltonredis.get_list_value("mods")]
        self.banned = [int(x) for x in miltonredis.get_list_value("banned")]

    def add_mod(self,uid):
        if uid not in self.mods:
            miltonredis.add_to_list("mods", uid)
            self.mods.append(uid)

    def del_mod(self, uid):
        miltonredis.rem_from_list("mods", uid)
        try:
            self.mods.remove(uid)
        except ValueError:
            pass

    def add_banned(self, uid):
        if uid not in self.banned:
            miltonredis.rem_from_list("mods", uid)
            miltonredis.add_to_list("banned", uid)
            self.banned.append(uid)
            try:
                self.mods.remove(uid) # banning also strips mod privileges
            except ValueError:
                pass

    def rem_banned(self, uid):
        miltonredis.rem_from_list("banned", uid)
        try:
            self.banned.remove(uid)
        except ValueError:
            pass

class spamState: # Rate limiting class
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

creds = CheckCreds()
spam = spamState()

def is_owner_check(ctx):
    return ctx.author.id == creds.overlord

def is_owner(): # see master_check comments
    return commands.check(is_owner_check)

def is_mod_check(ctx):
    return is_owner_check(ctx) or ctx.author.id in creds.mods

def is_mod(): # see master_check comments
    return commands.check(is_mod_check)

def _master_check(ctx): #see discord bot.py and commands files, plus Red-Bot for remembering how you figured this out
    if is_owner_check(ctx): #It had to do with a lot of decorators and callables
        return True
    elif ctx.author.id in creds.banned:
        return False
    elif ctx.author.bot:
        return False
    elif ctx.author.id in spam.spam_dict:
        if spam.spam_dict[ctx.author.id] == 5:
            return False
        else:
            return True
    else:
        return True

def master_check(bot): # add master check to bot
    bot.check(_master_check)
