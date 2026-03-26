class TouchBase:
    """
    Common interface:
      - touched() -> bool
      - get_point() -> (x, y, z) where x,y are screen coords if calibrated, else raw
      - set_rotation(0..3)
    """

    def __init__(self):
        self._rotation = 0

    def set_rotation(self, rotation):
        self._rotation = int(rotation) & 3

    def touched(self):  # pragma: no cover
        raise NotImplementedError

    def get_point(self):  # pragma: no cover
        raise NotImplementedError

    @staticmethod
    def transform(x, y, w, h, rotation):
        rot = int(rotation) & 3
        if rot == 0:
            return x, y
        if rot == 1:
            return (w - 1 - y), x
        if rot == 2:
            return (w - 1 - x), (h - 1 - y)
        return y, (h - 1 - x)

