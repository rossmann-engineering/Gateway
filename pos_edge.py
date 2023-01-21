class pos_edge(object):
    def __init__(self):
        self.lastStateRising = False
        self.lastStateFalling = False
        self.returnValueRising = False
        self.returnValueFalling = False

    def GetPosEdge(self, value):
        """
        Get the positive Edge of the value
        :param value: value to detect positive edge
        :return: True if value turns from false to true
        """
        if value & (not self.lastStateRising):
            self.returnValueRising = True
        else:
            self.returnValueRising = False
        self.lastStateRising = value
        return self.returnValueRising

    def GetNegEdge(self, value):
        """
        Get the negative Edge of the value
        :param value: value to detect negative edge
        :return: True if value turns from true to false
        """
        if (not value) & self.lastStateFalling:
            self.returnValueFalling = True
        else:
            self.returnValueFalling = False
        self.lastStateFalling = value
        return self.returnValueFalling


