"""
rep.py - willie/sopel-compatible clone of a mIRC script
Copyright 2015 dgw
"""

from willie import module
import time

TIMEOUT = 3600


@module.commands('luv')
@module.example(".luv johnnytwothumbs")
def luv(bot, trigger):
    if not trigger.group(3):
        bot.reply("No user specified.")
        return
    target = trigger.group(3)
    if target == trigger.nick:
        bot.reply("No narcissism allowed!")
        return
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.reply("You can only luv someone who is here.")
        return
    if rep_too_soon(bot, trigger.nick):
        return
    rep = mod_rep(bot, trigger.nick, target, 1)
    bot.say("%s has increased %s's reputation score to %d." % (trigger.nick, target, rep))


@module.commands('h8')
@module.example(".h8 johnnytwothumbs")
def h8(bot, trigger):
    if not trigger.group(3):
        bot.reply("No user specified.")
        return
    target = trigger.group(3)
    if target == trigger.nick:
        bot.reply("Go to 4chan if you really hate yourself!")
        return
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.reply("You can only h8 someone who is here.")
        return
    if rep_too_soon(bot, trigger.nick):
        return
    rep = mod_rep(bot, trigger.nick, target, -1)
    bot.say("%s has decreased %s's reputation score to %d." % (trigger.nick, target, rep))


@module.commands('rep')
@module.example(".rep johnnytwothumbs")
def rep(bot, trigger):
    target = trigger.group(3) or trigger.nick
    rep = get_rep(bot, target)
    if not rep:
        bot.say("%s has no reputation score yet." % target)
        return
    bot.say("%s's current reputation score is %d." % (target, rep))


# helpers
def get_rep(bot, target):
    return bot.db.get_nick_value(target, 'rep_score') or 0


def set_rep(bot, caller, target, newrep):
    bot.db.set_nick_value(target, 'rep_score', newrep)
    bot.db.set_nick_value(caller, 'rep_used', time.time())


def mod_rep(bot, caller, target, change):
    rep = get_rep(bot, target)
    rep += change
    set_rep(bot, caller, target, rep)
    return rep


def get_rep_used(bot, nick):
    return bot.db.get_nick_value(nick, 'rep_used') or 0


def set_rep_used(bot, nick):
    bot.db.set_nick_value(nick, 'rep_used', time.time())


def rep_used_since(bot, nick):
    now = time.time()
    last = get_rep_used(bot, nick)
    return abs(last - now)


def rep_too_soon(bot, nick):
    since = rep_used_since(bot, nick)
    if since < TIMEOUT:
        bot.notice("You must wait %d more seconds before changing someone's rep again." % (TIMEOUT - since), nick)
        return True
    else:
        return False
