class pos_edge(object):
    def __init__(self):
        """ gurke """
        self.lastStateRising = False
        self.lastStateFalling = False
        self.returnValueRising = False
        self.returnValueFalling = False

    def GetPosEdge(self, value):
        """
        gurke
        :param value: gurke
        :return: gurke
        """
        if value & (not self.lastStateRising):
            self.returnValueRising = True
        else:
            self.returnValueRising = False
        self.lastStateRising = value
        return self.returnValueRising

    def GetNegEdge(self, value):
        """
        gurke
        :param value: gurke
        :return: gurke
        """
        if (not value) & self.lastStateFalling:
            self.returnValueFalling = True
        else:
            self.returnValueFalling = False
        self.lastStateFalling = value
        return self.returnValueFalling


