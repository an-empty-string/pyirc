# PyIRC
## Introduction
PyIRC is a simple evented IRC framework.

## How to PyIRC
```python
import pyirc.irc as irc
connection = irc.do_irc_connect("chat.freenode.net", 6667)
connection.on("irc-001", lambda connection, event: connection.join("#bots"))
```
