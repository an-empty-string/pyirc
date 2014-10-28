import random
class User:
    def __init__(self, hostmask=None):
        if hostmask:
            try:
                self.nick, hostmask = hostmask.split("!")
                self.user, self.host = hostmask.split("@")
            except:
                # if something has no user or host, it is likely the ircd
                # TODO this is hacky
                self.nick = self.user = self.host = "ircd"

    @staticmethod
    def from_nickname(conn, nickname, notify_callback=None):
        """
        Create a new user object (with user and host) based on a nickname.
        This is done by calling whois from conn. A user might pass a function
        to notify_callback, since user and host will not be available right
        away.
        """
        user = User()
        user.nick = nickname
        callback_id = random.randint(1, 100000)
        def whois_callback(conn, event):
            if event.nick == user.nick:
                user.user = event.user
                user.host = event.host
                if notify_callback:
                    notify_callback(user)
                # TODO implement a better way of self-unregistering
                conn.unregister_callbacks("whois_%d" % callback_id)
        conn.register_callback("whois-result", whois_callback, tag="whois_%d" % callback_id)

    def __repr__(self):
        return "%s!%s@%s" % (self.nick, self.user, self.host)
