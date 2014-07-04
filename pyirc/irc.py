import net
import event

class IRCConnection:
    def __init__(self, sock, dispatcher):
        self.sock = sock
        self.dispatcher = dispatcher
        self.dispatcher.handlers.append(self._ecallback)
        self.callbacks = {}

    def writeln(self, line):
        self.sock.send(bytes("%s\n" % line, 'utf-8'))

    def register(self, nick, user, name, password=None):
        self.nick = nick
        self.user = user
        if password:
            self.writeln("PASS %s" % password)
        self.writeln("USER %s . . :%s" % (user, name))
        self.writeln("NICK %s" % nick)

    def on(self, type, func):
        if type not in self.callbacks:
            self.callbacks[type] = []
        self.callbacks[type].append(func)

    def _ecallback(self, dispatcher, event):
        if event.etype in self.callbacks:
            for callback in self.callbacks[event.etype]:
                callback(self, event)

    def join(self, channel):
        self.writeln("JOIN %s" % channel)

    def say(self, target, message):
        self.writeln("PRIVMSG %s :%s" % (target, message))

def parse_irc(dispatcher, e):
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
    cli.writeln("PONG :%s" % e.info["args"][0])

def do_irc_connect(host, port):
    sock = net.do_connect(host, port)
    dispatcher = net.do_dispatch_messages(sock)
    dispatcher.handlers.append(parse_irc)

    conn = IRCConnection(sock, dispatcher)
    conn.on("irc-ping", do_ping)

    return conn
