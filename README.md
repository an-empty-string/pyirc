# PyIRC
## Introduction
PyIRC is a simple evented IRC framework.

## How to PyIRC
```python
from pyirc import irc
connection = irc.do_irc_connect("chat.freenode.net", 6667)
connection.autojoin("#bots", "#mychannel")
```

## How to Message Handling
```python
def say_hello(conn, event):
    if "hi" in event.message or "hello" in event.message:
        conn.say(event.to, "Hi!")

connection.on("message#", say_hello)
```
