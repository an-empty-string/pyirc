from pyirc import irc
from time import time
conn = irc.do_irc_connect("chat.freenode.net")
conn.register("hugbot9001", "hug", "HUGBOT <3")
conn.autojoin("##erry")
global lasthug
lasthug = 0

@conn.on("ctcp")
def handle_action(conn, event):
 global lasthug
 if "hugs" not in event.args: return
 if event.user.nick not in ["fwilson", "ishanyx", "bcode", "bcode|phone"] and time() - lasthug < 10:
  conn.action(event.to, "murders %s"%event.user.nick)
  return
 lasthug = time()
 args = event.args
 if len(args)-1 == args.index("hugs") or args[args.index("hugs")+1] == "hugbot9001":
  conn.action(event.to, "hugs %s" % event.user.nick)
 else:
  conn.action(event.to, "hugs %s and %s" % (event.user.nick, args[args.index("hugs")+1]))
