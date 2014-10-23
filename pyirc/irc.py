from . import net, event, user
from functools import wraps
import string
import sys

class IRCConnection:
    def __init__(self, sock, dispatcher):
        self.version = "pyIRC framework"
        self.sock = sock
        self.dispatcher = dispatcher
        self.dispatcher.handlers.append(self._ecallback)
        self.callbacks = {}
        self.servercaps = {}
        self.data = {"nicks": {}}
        self.connected = False
        self.register_callback("irc-001", self._set_connect_flag)
        self.register_callback("irc-005", self.parse_005)

    def on(self, event_type, filter=None):
        """
        Decorator form of register_callback. A filter can be passed to remove
        undesired events before receiving them:

            @conn.on("chanmessage", filter=lambda e: e.message[0] == "!")

        would only allow messages starting with ! (perhaps a bot's command
        character).
        """
        def wrap(f):
            @wraps(f)
            def wrapped_f(conn, event):
                if (not filter) or filter(event):
                    f(conn, event)
            self.register_callback(event_type, wrapped_f)
            return f
        return wrap

    def parse_005(self, conn, event):
        """
        Parse server 005 messages to gather server capabilities, i.e. channel
        types. Currently we only use this to figure out channel types for
        message parsing.
        """
        for i in event.args:
            if "=" in i: # i.e. not a boolean true or false
                key, value = i.split("=")
                self.servercaps[key.lower()] = value
            else:
                self.servercaps[i.lower()] = True

    def _set_connect_flag(self, conn, event):
        """
        This is mostly for setting the connected flag when we receive a 001
        from the server (registered numeric).
        """
        self.connected = True

    def autojoin(self, *channels):
        """
        Create a function which joins all the given channels, and tell the
        client to run it as soon as it is connected to the server.
        """
        def join_channels(conn, event):
            for i in channels:
                conn.join(i)
        self.register_callback("irc-001", join_channels)

    def writeln(self, line):
        """
        Convert the line to a bytestring and add a newline. Then, send it to
        the IRC server.
        """
        if sys.version_info.major > 2:
            self.sock.send(bytes("%s\n" % line, 'utf-8'))
        else:
            self.sock.send("%s\n" % line)

    def register(self, nick, user, realname, password=None):
        """
        Sends the server password, if any, followed by the NICK and USER
        commands with the given arguments.
        """
        self.nick = nick
        self.user = user
        if password:
            self.writeln("PASS %s" % password)
        self.writeln("USER %s . . :%s" % (user, realname))
        self.writeln("NICK %s" % nick)

    def register_callback(self, type, func):
        """
        Attaches a callback function with the signature (connection, event) for
        any events with the given type.
        """
        if type not in self.callbacks:
            self.callbacks[type] = []
        self.callbacks[type].append(func)

    def _ecallback(self, dispatcher, event):
        """
        Call connection callbacks on received events.
        """
        if event.etype in self.callbacks:
            for callback in self.callbacks[event.etype]:
                callback(self, event)

    def join(self, channel):
        """
        Join a channel.
        """
        self.writeln("JOIN %s" % channel)

    def part(self, channel):
        """
        Leave a channel.
        """
        self.writeln("PART %s" % channel)

    def _say(self, target, message):
        self.writeln("PRIVMSG %s :%s" % (target, message))

    def say(self, target, message):
        """
        Sends a message to a channel or user.
        """
        message = str(message)
        if len(message) < 450:
            self._say(target, message)
        else:
            for i in range(int(len(message) / 400) + 1):
                self._say(target, message[(400*i):(400*i+400)])

    def action(self, target, message):
        """
        Send an action (i.e. /me) to a channel or user.
        """
        self.writeln("PRIVMSG %s :\x01ACTION %s\x01" % (target, message))

    def notice(self, target, message):
        """
        Send a notice to a channel or user.
        """
        self.writeln("NOTICE %s :%s" % (target, message))

    def ctcp(self, target, message):
        """
        Send a CTCP to a channel or user.
        """
        self.writeln("PRIVMSG %s :\x01%s\x01" % (target, message))

    def ctcp_reply(self, target, message):
        """
        Send a CTCP reply to a channel or user.
        """
        self.writeln("NOTICE %s :\x01%s\x01" % (target, message))

    def mode(self, target, modes, *args):
        """
        Set modes on an IRC channel.
        """
        self.writeln("MODE %s %s %s" % (target, modes, " ".join(args)))

    def names(self, target):
        """
        Call NAMES on a channel to get the nick list.
        """
        self.writeln("NAMES %s" % target)

    def whois(self, target):
        """
        Call WHOIS on a nickname to get the user and host.
        """
        self.writeln("WHOIS %s" % target)

def parse_irc(dispatcher, e):
    """
    Parses IRC messages from raw events and dispatches the parsed message as
    irc and irc-{command} type events.
    """
    if e.etype != "raw":
        return
    line = e.info["line"]

    if line[0] == ":":
        prefix = line[1:line.index(" ")]
        line = line[line.index(" "):].strip()
    else:
        prefix = ""

    if " :" in line:
        line, trailing = line.split(" :", 1)
    else:
        trailing = ""

    line = line.strip()
    command = line.split(" ")[0]
    args = line.split(" ")[1:]
    if trailing:
        args.append(trailing)
    args = [i.strip() for i in args]

    dispatcher.dispatch(event.Event("irc", prefix=prefix, command=command, args=args))
    dispatcher.dispatch(event.Event("irc-%s" % command.lower(), prefix=prefix, args=args))

def do_ping(cli, e):
    """
    Respond to server PINGs.
    """
    cli.writeln("PONG :%s" % e.info["args"][0])

def do_parse_privmsg(conn, e):
    """
    Handle irc-privmsg events and redispatch them as message events, as well
    as pubmessage or privmessage depending on the message type. Handle CTCP.
    """
    target, message = e.info["args"]
    source = user.User(e.info["prefix"]) 
    if message.startswith("\x01") and message.endswith("\x01"): # CTCP
        message = message[1:-1].split()
        command, args = message[0], message[1:]
        info = {"to": target, "command": command, "args": args, "user": source}
        conn.dispatcher.dispatch(event.Event("ctcp", **info))
        return

    info = {"to": target, "message": message, "user": source}
    conn.dispatcher.dispatch(event.Event("message", **info))
    if "chantypes" in conn.servercaps and target[0] in conn.servercaps["chantypes"]:
        conn.dispatcher.dispatch(event.Event("pubmessage", **info))
    elif "chantypes" not in conn.servercaps and target[0] in "#":
        conn.dispatcher.dispatch(event.Event("pubmessage", **info))
    elif "statusmsg" in conn.servercaps and target[0] in conn.servercaps["statusmsg"]:
        conn.dispatcher.dispatch(event.Event("pubmessage", **info))
    else:
        conn.dispatcher.dispatch(event.Event("privmessage", **info))

def do_parse_notice(conn, e):
    """
    Handle irc-notice events and redispatch them as notice events, as well
    as pubnotice or privnotice depending on the message type. Handle CTCP
    replies.
    """
    target, message = e.info["args"]
    source = user.User(e.info["prefix"])
    if message.startswith("\x01") and message.endswith("\x01"): # CTCP reply
        message = message[1:-1].split()
        command, args = message[0], message[1:]
        info = {"to": target, "command": command, "args": args, "user": source}
        conn.dispatcher.dispatch(event.Event("ctcp-reply", **info))
        return

    info = {"to": target, "message": message, "user": source}
    conn.dispatcher.dispatch(event.Event("notice", **info))
    if "chantypes" in conn.servercaps and target[0] in conn.servercaps["chantypes"]:
        conn.dispatcher.dispatch(event.Event("pubnotice", **info))
    elif "chantypes" not in conn.servercaps and target[0] in "#":
        conn.dispatcher.dispatch(event.Event("pubnotice", **info))
    elif "statusmsg" in conn.servercaps and target[0] in conn.servercaps["statusmsg"]:
        conn.dispatcher.dispatch(event.Event("pubnotice", **info))
    else:
        conn.dispatcher.dispatch(event.Event("privnotice", **info))

def do_parse_join(conn, e):
    """
    Handle irc-join events and redispatch them as join events.
    """
    u = user.User(e.prefix)
    chan = e.args[0]
    conn.dispatcher.dispatch(event.Event("join", user=u, channel=chan))

def do_parse_part(conn, e):
    """
    Handle irc-part events and redispatch them as part events.
    """
    u = user.User(e.prefix)
    chan = e.args[0]
    reason = None if len(e.args) < 2 else e.args[1]
    conn.dispatcher.dispatch(event.Event("part", user=u, channel=chan, reason=reason))

def do_parse_quit(conn, e):
    """
    Handle irc-quit events and redispatch them as quit events.
    """
    u = user.User(e.prefix)
    chan = e.args[0]
    reason = None if len(e.args) < 2 else e.args[1]
    conn.dispatcher.dispatch(event.Event("quit", user=u, channel=chan, reason=reason))

def do_ctcp_version(conn, e):
    """
    Handle CTCP VERSION requests.
    """
    if e.command.lower() != "version":
        return
    conn.ctcp_reply(e.user.nick, "VERSION %s" % conn.version)

def do_whois_result(conn, e):
    conn.dispatcher.dispatch(event.Event("whois-result", **dict(zip(["nick", "user", "host"], e.args[1:4]))))

def do_names_list(conn, e):
    chan = e.args[2]
    users = e.args[3].split()
    if chan not in conn.data["nicks"]:
        conn.data["nicks"][chan] = {}

    for i in users:
        # TODO use the ISUPPORT message
        if i[0] in string.punctuation:
            conn.data["nicks"][chan][i[1:]] = i[0]
        else:
            conn.data["nicks"][chan][i] = ""

def do_names_end(conn, e):
    chan = e.args[1]
    if chan not in conn.data["nicks"]:
        conn.data["nicks"][chan] = []
    conn.dispatcher.dispatch(event.Event("names", chan=chan, nicks=conn.data["nicks"][chan]))
    conn.data["nicks"][chan] = 0

def do_irc_connect(host="chat.freenode.net", port=6667):
    """
    Create a new IRCConnection given a host and port. Attach the needed event
    listeners.
    """
    sock = net.do_connect(host, port)
    dispatcher = net.do_dispatch_messages(sock)
    dispatcher.handlers.append(parse_irc)

    conn = IRCConnection(sock, dispatcher)
    conn.register_callback("irc-ping", do_ping)
    conn.register_callback("irc-privmsg", do_parse_privmsg)
    conn.register_callback("irc-notice", do_parse_notice)
    conn.register_callback("irc-join", do_parse_join)
    conn.register_callback("irc-part", do_parse_part)
    conn.register_callback("irc-quit", do_parse_quit)
    conn.register_callback("irc-311", do_whois_result)
    conn.register_callback("irc-353", do_names_list) # Names list addition
    conn.register_callback("irc-366", do_names_end) # End of names list
    conn.register_callback("ctcp", do_ctcp_version)

    return conn
