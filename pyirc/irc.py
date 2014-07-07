from . import net, event, user
from functools import wraps
import string

class IRCConnection:
    def __init__(self, sock, dispatcher):
        self.sock = sock
        self.dispatcher = dispatcher
        self.dispatcher.handlers.append(self._ecallback)
        self.callbacks = {}
        self.servercaps = {}
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
        # TODO hacky way of parsing -- be more general
        ctypes = [i for i in event.args if i.startswith("CHANTYPES=")]
        if len(ctypes) != 1:
            return
        self.servercaps["chantypes"] = ctypes[0][10:]

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
        self.sock.send(bytes("%s\n" % line, 'utf-8'))

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

    def say(self, target, message):
        """
        Send a message to a channel.
        """
        self.writeln("PRIVMSG %s :%s" % (target, message))

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
    as chanmessage or pm depending on the message type.
    """
    target, message = e.info["args"]
    source = user.User(e.info["prefix"]) 
    info = {"to": target, "message": message, "from": source}
    conn.dispatcher.dispatch(event.Event("message", **info))
    if "chantypes" in conn.servercaps
       and target[0] in conn.servercaps["chantypes"]
       or target[0] in "#":
        conn.dispatcher.dispatch(event.Event("chanmessage", **info))
    else:
        conn.dispatcher.dispatch(event.Event("pm", **info))

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
    reason = None if len(e.args < 2) else e.args[1]
    conn.dispatcher.dispatch(event.Event("part", user=u, channel=chan, reason=reason))

def do_irc_connect(host, port=6667):
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
    conn.register_callback("irc-join", do_parse_join)
    conn.register_callback("irc-part", do_parse_part)

    return conn
