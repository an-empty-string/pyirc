from . import net, event, user
import string

class IRCConnection:
    def __init__(self, sock, dispatcher):
        self.sock = sock
        self.dispatcher = dispatcher
        self.dispatcher.handlers.append(self._ecallback)
        self.callbacks = {}
        self.servercaps = {}
        self.connected = False
        self.on("irc-001", self._set_connect_flag)
        self.on("irc-005", self.parse_005)

    def parse_005(self, conn, event):
        """
        Parse server 005 messages to gather server capabilities, i.e. channel
        types. Currently we only use this to figure out channel types for
        message parsing.
        """
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
        self.on("irc-001", join_channels)

    def writeln(self, line):
        """
        Convert the line to a bytestring and add a newline. Then, send it to
        the IRC server.
        """
        self.sock.send(bytes("%s\n" % line, 'utf-8'))

    def register(self, nick, user, name, password=None):
        """
        Sends the server password, if any, followed by the NICK and USER
        commands with the given arguments.
        """
        self.nick = nick
        self.user = user
        if password:
            self.writeln("PASS %s" % password)
        self.writeln("USER %s . . :%s" % (user, name))
        self.writeln("NICK %s" % nick)

    def on(self, type, func):
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
    # TODO use servercaps
    if target[0] in conn.servercaps["chantypes"]:
        conn.dispatcher.dispatch(event.Event("chanmessage", **info))
    else:
        conn.dispatcher.dispatch(event.Event("pm", **info))

def do_irc_connect(host, port):
    """
    Create a new IRCConnection given a host and port. Attach the needed event
    listeners.
    """
    sock = net.do_connect(host, port)
    dispatcher = net.do_dispatch_messages(sock)
    dispatcher.handlers.append(parse_irc)

    conn = IRCConnection(sock, dispatcher)
    conn.on("irc-ping", do_ping)
    conn.on("irc-privmsg", do_parse_privmsg)

    return conn
