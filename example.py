from pyirc import irc
from glob import glob

conn = irc.do_irc_connect("localhost")
conn.register(nick="testbot1", user="fwilson", realname="a PyIRC bot")
conn.autojoin("#")

@conn.on("message", filter=lambda e: e.message.startswith("!caps"))
def say_hello(conn, event):
    conn.say(event.to, repr(conn.servercaps))
    print(repr(conn.servercaps))

@conn.on("message", filter=lambda e: e.message[0] == "!")
def process_command(conn, event):
    t = event.message[1:].split()
    cmd, args = t[0], t[1:]
    conn.say(event.to, "cmd=%s, args=%s" % (cmd, repr(args)))

@conn.on("join")
def greet_users(conn, event):
    conn.say(event.channel, "Hello, %s!" % event.user.nick)

@conn.on("part")
def goodbye(conn, event):
    conn.say(event.channel, "%s left :(" % event.user.nick)
