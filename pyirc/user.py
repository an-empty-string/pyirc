class User:
    def __init__(self, hostmask):
        try:
            self.nick, hostmask = hostmask.split("!")
            self.user, self.host = hostmask.split("@")
        except:
            # if something has no user or host, it is likely the ircd
            self.nick = self.user = self.host = "ircd"
