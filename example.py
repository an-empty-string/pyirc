from pyirc import irc

conn = irc.do_irc_connect("chat.freenode.net")
conn.register(nick="testbot1", user="fwilson", realname="a PyIRC bot")
conn.autojoin("##fwilson")

@conn.on("chanmessage", filter=lambda e: e.message.startswith("!caps"))
def say_hello(conn, event):
    conn.say(event.to, repr(conn.servercaps))

@conn.on("join")
def greet_users(conn, event):
    conn.say(event.channel, "Hello, %s!" % event.user.nick)

@conn.on("part")
def goodbye(conn, event):
    conn.say(event.channel, "%s left :(" % event.user.nick)
