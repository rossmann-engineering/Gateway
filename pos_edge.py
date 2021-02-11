class pos_edge(object):
    def __init__(self):
        self.lastStateRising = False
        self.lastStateFalling = False
        self.returnValueRising = False
        self.returnValueFalling = False

    def GetPosEdge(self, value):
        if ((value) & (not self.lastStateRising)):
            self.returnValueRising = True
        else:
            self.returnValueRising = False
        self.lastStateRising = value
        return self.returnValueRising

    def GetNegEdge(self, value):
        if ((not value) & (self.lastStateFalling)):
            self.returnValueFalling = True
        else:
            self.returnValueFalling = False
        self.lastStateFalling = value
        return self.returnValueFalling


