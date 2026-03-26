from .base import TouchBase


class FT6236(TouchBase):
    """
    FT6236/FT6336 capacitive touch controller (I2C).
    """

    _REG_TD_STATUS = 0x02
    _REG_P1_XH = 0x03

    def __init__(self, i2c, *, addr=0x38, width=None, height=None, invert_x=False, invert_y=False, swap_xy=False):
        super().__init__()
        self.i2c = i2c
        self.addr = int(addr)
        self.width = width
        self.height = height
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)
        self.swap_xy = bool(swap_xy)

    def touched(self):
        n = self.i2c.readfrom_mem(self.addr, self._REG_TD_STATUS, 1)[0] & 0x0F
        return n > 0

    def get_point(self):
        n = self.i2c.readfrom_mem(self.addr, self._REG_TD_STATUS, 1)[0] & 0x0F
        if n == 0:
            return None
        d = self.i2c.readfrom_mem(self.addr, self._REG_P1_XH, 4)
        x = ((d[0] & 0x0F) << 8) | d[1]
        y = ((d[2] & 0x0F) << 8) | d[3]
        if self.swap_xy:
            x, y = y, x
        if self.invert_x and self.width is not None:
            x = (self.width - 1) - x
        if self.invert_y and self.height is not None:
            y = (self.height - 1) - y
        return x, y, 1

