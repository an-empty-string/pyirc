class Event:
    def __init__(self, etype, **kwargs):
        self.etype = etype
        self.info = kwargs

    def __repr__(self):
        return "<Event<%s>, %s>" % (self.etype, repr(self.info))

class EventDispatcher:
    def __init__(self):
        self.handlers = [] # handlers should be callable

    def dispatch(self, event):
        for i in self.handlers:
            i(self, event)
