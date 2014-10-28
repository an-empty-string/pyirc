class Channel:
    def __init__(self, conn, name):
        self.name = name
        self.users = {}
        self.ops = []
        self.voices = []
        self.conn = conn
        self._callbacks = []
        conn.register_callback("names", self.names_hook, "nameshook_channel_%s" % name)

    def names_hook(self, conn, event):
        self.users = event.nicks
        # TODO use ISUPPORT for ops/voice prefix
        self.ops = [i[0] for i in filter(lambda a: a[1] == "@", self.users.items())]
        self.voices = [i[0] for i in filter(lambda a: a[1] == "+", self.users.items())]
        for i in self._callbacks:
            i(self.users)
        self._callbacks = []

    def update_names(self, notify_callback=None):
        """
        Update the names cache for this channel. Opionally takes a
        notify_callback for notification of update completion. The callback
        will be passed the updated nicks dict.
        """
        self._callbacks.append(notify_callback)
        self.conn.names(self.name)

    def __repr__(self):
        return "<Channel %s: %d users (%d ops, %d voices)>" % (self.name, len(self.users), len(self.ops), len(self.voices))
