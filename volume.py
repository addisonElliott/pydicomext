class Volume():
    def __init__(self, data=None, space=None, orientation=None, origin=None, spacing=None):
        self.data = data
        self.space = space
        self.orientation = orientation
        self.origin = origin
        self.spacing = spacing

    def __str__(self):
        return """Volume
    Space: %s
    Orientation: %s
    Origin: %s
    Spacing: %s
    Volume shape: %s""" % (self.space, self.orientation, self.orientation, self.spacing,
                           self.data.shape if self.data else None)

    def __repr__(self):
        return self.__str__()
