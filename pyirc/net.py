from . import event
import socket
import threading
import select
import time

def do_connect(host, port):
    s = socket.socket()
    s.connect((host, port))
    return s

def do_incoming_listen(socket, callback):
    def loop(socket, callback):
        while True:
            select.select([socket], [], [])
            cbuf = ""
            while len(cbuf) == 0 or ('\n' not in cbuf and '\r' not in cbuf):
                select.select([socket], [], [])
                old_buf_len = len(cbuf)
                try:
                    cbuf += str(socket.recv(1024), "utf-8")
                    if old_buf_len == len(cbuf):
                        time.sleep(1)
                except:
                    print("Bad: %s" % cbuf)
            if '\r\n' in cbuf:
                cbuf = cbuf.split("\n")
                for i in cbuf:
                    if "\r" in i and len(i.strip()) != 0:
                        callback(i.strip())
                    elif "\r" not in i:
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
