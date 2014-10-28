from . import event
import socket
import threading

def do_connect(host, port):
    s = socket.socket()
    s.connect((host, port))
    return s

def do_incoming_listen(socket, callback):
    def loop(socket, callback):
        while True:
            cbuf = ""
            while len(cbuf) == 0 or cbuf[-1] != '\n':
                try:
                    cbuf += str(socket.recv(1024), "utf-8")
                except:
                    print("Bad: %s" % cbuf)
            callback(cbuf)

    threading.Thread(target=loop, args=(socket, callback)).start()

def do_dispatch_messages(socket):
    dispatcher = event.EventDispatcher()
    def dispatch(line):
        dispatcher.dispatch(event.Event("raw", line=line))

    do_incoming_listen(socket, dispatch)
    return dispatcher
