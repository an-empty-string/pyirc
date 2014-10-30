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
            while len(cbuf) == 0 or ('\n' not in cbuf and '\r' not in cbuf):
                try:
                    cbuf += str(socket.recv(1024), "utf-8")
                except:
                    print("Bad: %s" % cbuf)
            if '\r\n' in cbuf:
                cbuf = cbuf.split("\n")
                for i in cbuf:
                    if "\r" in cbuf and len(i.strip()) != 0:
                        print(cbuf)
                        callback(i.strip())
                    elif "\r" not in cbuf:
                        cbuf = i
                        break
            else:
                print(cbuf)
                callback(cbuf)

    threading.Thread(target=loop, args=(socket, callback)).start()

def do_dispatch_messages(socket):
    dispatcher = event.EventDispatcher()
    def dispatch(line):
        dispatcher.dispatch(event.Event("raw", line=line))

    do_incoming_listen(socket, dispatch)
    return dispatcher
