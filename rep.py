"""
rep.py - sopel-compatible clone of a mIRC script
Copyright 2015-2019 dgw
"""

from sopel import module
from sopel.tools import Identifier, time as time_tools
import time
import re

TIMEOUT = 3600


@module.rule('^(?P<command></?3)\s+([a-zA-Z0-9\[\]\\\\`_\^\{\|\}-]{1,32})\s*$')
@module.intent('ACTION')
@module.require_chanmsg("You may only modify someone's rep in a channel.")
def heart_cmd(bot, trigger):
    luv_h8(bot, trigger, trigger.group(2), 'h8' if '/' in trigger.group(1) else 'luv')


@module.rule('.*?(?:([a-zA-Z0-9\[\]\\\\`_\^\{\|\}-]{1,32})(\+{2}|-{2})).*?')
@module.require_chanmsg("You may only modify someone's rep in a channel.")
def karma_cmd(bot, trigger):
    if re.match('^({prefix})({cmds})'.format(prefix=bot.config.core.prefix, cmds='|'.join(luv_h8_cmd.commands)),
                trigger.group(0)):
        return  # avoid processing commands if people try to be tricky
    for (nick, act) in re.findall('(?:([a-zA-Z0-9\[\]\\\\`_\^\{\|\}-]{1,32})(\+{2}|-{2}))', trigger.raw):
        if luv_h8(bot, trigger, nick, 'luv' if act == '++' else 'h8', warn_nonexistent=False):
            break


@module.commands('luv', 'h8')
@module.example(".luv johnnytwothumbs")
@module.example(".h8 d-bag")
@module.require_chanmsg("You may only modify someone's rep in a channel.")
def luv_h8_cmd(bot, trigger):
    if not trigger.group(3):
        bot.reply("No user specified.")
        return
    target = Identifier(trigger.group(3))
    luv_h8(bot, trigger, target, trigger.group(1))


def luv_h8(bot, trigger, target, which, warn_nonexistent=True):
    target = verified_nick(bot, target, trigger.sender)
    which = which.lower()  # issue #18
    pfx = change = selfreply = None  # keep PyCharm & other linters happy
    if not target:
        if warn_nonexistent:
            command = which
            try:  # because a simple "trigger.group('command') or which" doesn't work
                command = trigger.group('command')
            except IndexError:  # why can't you just return None, re.group()?
                pass
            bot.reply("You can only %s someone who is here." % command)
        return False
    if rep_too_soon(bot, trigger.nick):
        return False
    if which == 'luv':
        selfreply = "No narcissism allowed!"
        pfx, change = 'in', 1
    if which == 'h8':
        selfreply = "Go to 4chan if you really hate yourself!"
        pfx, change = 'de', -1
    if not (pfx and change and selfreply):  # safeguard against leaving something in the above mass-None assignment
        bot.say("Logic error! Please report this to %s." % bot.config.core.owner)
        return
    if is_self(bot, trigger.nick, target):
        bot.reply(selfreply)
        return False
    if bot.db.get_nick_value(target, 'rep_locked'):
        bot.reply("Sorry, %s's reputation has been locked by an admin." % target)
        return False
    rep = mod_rep(bot, trigger.nick, target, change)
    bot.say("%s has %screased %s's reputation score to %d" % (trigger.nick, pfx, target, rep))
    return True


@module.commands('rep')
@module.example(".rep johnnytwothumbs")
def show_rep(bot, trigger):
    target = trigger.group(3) or trigger.nick
    rep = get_rep(bot, target)
    if rep is None:
        bot.say("%s has no reputation score yet." % target)
        return
    bot.say("%s's current reputation score is %d." % (target, rep))


@module.commands('replock', 'repunlock')
@module.example('.replock BullyingVictim')
@module.require_admin('Only bot admins may manage reputation locks')
def manage_locks(bot, trigger):
    target = trigger.group(3)
    if not target:
        bot.reply("I need a nickname!")
        return
    if 'un' in trigger.group(1):  # .repunlock command used
        bot.db.set_nick_value(Identifier(target), 'rep_locked', False)
        bot.say("Unlocked rep for %s." % target)
    else:  # .replock command used
        bot.db.set_nick_value(Identifier(target), 'rep_locked', True)
        bot.say("Locked rep for %s." % target)


# helpers
def get_rep(bot, target):
    return bot.db.get_nick_value(Identifier(target), 'rep_score')


def set_rep(bot, caller, target, newrep):
    bot.db.set_nick_value(Identifier(target), 'rep_score', newrep)
    bot.db.set_nick_value(Identifier(caller), 'rep_used', time.time())


def mod_rep(bot, caller, target, change):
    rep = get_rep(bot, target) or 0
    rep += change
    set_rep(bot, caller, target, rep)
    return rep


def get_rep_used(bot, nick):
    return bot.db.get_nick_value(Identifier(nick), 'rep_used') or 0


def set_rep_used(bot, nick):
    bot.db.set_nick_value(Identifier(nick), 'rep_used', time.time())


def rep_used_since(bot, nick):
    now = time.time()
    last = get_rep_used(bot, nick)
    return abs(last - now)


def rep_too_soon(bot, nick):
    since = rep_used_since(bot, nick)
    if since < TIMEOUT:
        bot.notice("You can change someone's rep again %s." % time_tools.seconds_to_human(-(TIMEOUT - since)), nick)
        return True
    else:
        return False


def is_self(bot, nick, target):
    nick = Identifier(nick)
    target = Identifier(target)
    if nick == target:
        return True  # shortcut to catch common goofballs
    try:
        nick_id = bot.db.get_nick_id(nick, False)
        target_id = bot.db.get_nick_id(target, False)
    except ValueError:
        return False  # if either nick doesn't have an ID, they can't be in a group
    return nick_id == target_id


def verified_nick(bot, nick, channel):
    nick = re.search('([a-zA-Z0-9\[\]\\\\`_\^\{\|\}-]{1,32})', nick).group(1)
    if not nick:
        return ''  # returning None would mean the returned value can't be compared with ==
    nick = Identifier(nick)
    if nick.lower() not in bot.privileges[channel.lower()]:
        if nick.endswith('--'):
            if Identifier(nick[:-2]).lower() in bot.privileges[channel.lower()]:
                return Identifier(nick[:-2])
        return ''  # see above
    return nick
