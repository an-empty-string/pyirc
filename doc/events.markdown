# Events

## raw
Represents a raw line coming from the server.

- **line**: the raw text of the line

## irc
Represents a parsed IRC message.

- **prefix** - the prefix of the user (nick!user@host)
- **command** - the command being received (PRIVMSG)
- **args** - an argument list (["#channel", "hello world"])

## irc-{command}
Represents a parsed IRC message with a given command.

- **prefix** - the prefix of the user (nick!user@host)
- **args** - an argument list (["#channel", "hello world"])

## message
Represents a PRIVMSG command sent from the server.

- **to** - the target of the message (a channel or nickname)
- **message** - the text of the message being sent
- **user** - a User object representing the sender of the message

## pubmessage
Represents a message sent to an IRC channel.

- **to** - the target of the message (a channel or nickname)
- **message** - the text of the message being sent
- **user** - a User object representing the sender of the message

## privmsg
Represents a private message (one sent to you).

- **to** - the target of the message (a channel or nickname)
- **message** - the text of the message being sent
- **user** - a User object representing the sender of the message

## ctcp
Represents an incoming CTCP request.

- **to** - the target of the message (a channel or nickname)
- **command** - the CTCP command (PING)
- **args** - the arguments
- **user** - a User object representing the sender of the message

## notice
Represents a NOTICE command sent from the server.

- **to** - the target of the message (a channel or nickname)
- **message** - the text of the message being sent
- **user** - a User object representing the sender of the message

## pubnotice
Represents a NOTICE sent to an IRC channel.

- **to** - the target of the message (a channel or nickname)
- **message** - the text of the message being sent
- **user** - a User object representing the sender of the message

## privnotice
Represents a private NOTICE (sent to you).

- **to** - the target of the message (a channel or nickname)
- **message** - the text of the message being sent
- **user** - a User object representing the sender of the message

## ctcp-reply
Represents a reply to a CTCP request.

- **to** - the target of the message (a channel or nickname)
- **command** - the CTCP command (PING)
- **args** - the arguments
- **user** - a User object representing the sender of the message

## join
Represents a user joining a channel.

- **user** - the User object joining the channel
- **channel** - the channel being joined

## part
Represents a user leaving a channel.

- **user** - the User object leaving the channel
- **channel** - the channel being left
- **reason** - the reason for leaving the channel, or None if there isn't one

## quit
Represents a user leaving IRC.

- **user** - the User object leaving the server
- **reason** - the reason for quitting, or None if there isn't one

## whois-result
Represents a response to a /whois request.

- **nick** - the user's nickname
- **user** - the user's ident
- **host** - the user's hostname

## names
Represents a response to a /names request.

- **chan** - the channel
- **nicks** - the nicknames
