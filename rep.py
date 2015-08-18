"""
rep.py - willie/sopel-compatible clone of a mIRC script
Copyright 2015 dgw
"""

from willie import module


@module.commands('luv')
@module.rate(3600)
@module.example(".luv johnnytwothumbs")
def luv(bot, trigger):
    if not trigger.group(3):
        bot.reply("No user specified.")
        return
    target = trigger.group(3)
    if target == trigger.nick:
        bot.reply("No narcissism allowed!")
        return
    rep = mod_rep(bot, target, 1)
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.reply("You can only luv someone who is here.")
        return
    bot.say("%s has increased %s's reputation score to %d." % (trigger.nick, target, rep))


@module.commands('h8')
@module.rate(3600)
@module.example(".h8 johnnytwothumbs")
def h8(bot, trigger):
    if not trigger.group(3):
        bot.reply("No user specified.")
        return
    target = trigger.group(3)
    if target == trigger.nick:
        bot.reply("Go to 4chan if you really hate yourself!")
        return
    rep = mod_rep(bot, target, -1)
    if target.lower() not in bot.privileges[trigger.sender.lower()]:
        bot.reply("You can only h8 someone who is here.")
        return
    bot.say("%s has decreased %s's reputation score to %d." % (trigger.nick, target, rep))


@module.commands('rep')
@module.example(".rep johnnytwothumbs")
def rep(bot, trigger):
    if not trigger.group(3):
        bot.reply("No user specified.")
        return
    target = trigger.group(3)
    rep = get_rep(bot, target)
    if not rep:
        bot.say("%s has no reputation score yet." % target)
        return
    bot.say("%s's current reputation score is %d." % (target, rep))


# helpers
def get_rep(bot, nick):
    return bot.db.get_nick_value(nick, 'rep_score') or 0


def set_rep(bot, nick, newrep):
    bot.db.set_nick_value(nick, 'rep_score', newrep)


def mod_rep(bot, nick, change):
    rep = get_rep(bot, nick)
    rep += change
    set_rep(bot, nick, rep)
    return rep
