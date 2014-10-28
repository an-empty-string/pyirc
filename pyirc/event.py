class Event:
    def __init__(self, etype, **kwargs):
        self.etype = etype
        self.info = kwargs

    def __getattr__(self, thing):
        if thing not in self.__dict__:
            return self.__dict__["info"][thing]
        return self.__dict__[thing]

    def __repr__(self):
        return "<Event<%s>, %s>" % (self.etype, repr(self.info))

class EventDispatcher:
    def __init__(self):
        self.handlers = []

    def dispatch(self, event):
        """
        Dispatch an Event to registered handlers.
        """
        for i in self.handlers:
            i(self, event)
