class Channel:
    def __init__(self, conn, name):
        self.name = name
        self.users = {}
        self.ops = []
        self.voices = []
        conn.register_callback("names", self.names_hook, "nameshook_channel_%s" % name)

    def names_hook(self, conn, event):
        self.users = event.nicks
        # TODO use ISUPPORT for ops/voice prefix
        self.ops = [i[0] for i in filter(lambda a: a[1] == "@", self.users.items())]
        self.voices = [i[0] for i in filter(lambda a: a[1] == "+", self.users.items())]
