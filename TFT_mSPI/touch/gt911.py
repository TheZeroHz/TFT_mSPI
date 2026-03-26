from .base import TouchBase


class GT911(TouchBase):
    """
    GT911 capacitive touch controller (I2C).

    Reads a single touch point.
    """

    _REG_STATUS = 0x814E
    _REG_FIRST_POINT = 0x8150  # 7 bytes

    def __init__(self, i2c, *, addr=0x5D, width=None, height=None, invert_x=False, invert_y=False, swap_xy=False):
        super().__init__()
        self.i2c = i2c
        self.addr = int(addr)
        self.width = width
        self.height = height
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)
        self.swap_xy = bool(swap_xy)

    def _read_u8(self, reg):
        b = self.i2c.readfrom_mem(self.addr, reg, 1)
        return b[0]

    def touched(self):
        status = self._read_u8(self._REG_STATUS)
        return (status & 0x80) != 0 and (status & 0x0F) > 0

    def get_point(self):
        status = self._read_u8(self._REG_STATUS)
        count = status & 0x0F
        ready = (status & 0x80) != 0
        if not ready or count == 0:
            return None

        d = self.i2c.readfrom_mem(self.addr, self._REG_FIRST_POINT, 7)
        x = d[0] | (d[1] << 8)
        y = d[2] | (d[3] << 8)
        size = d[4] | (d[5] << 8)

        self.i2c.writeto_mem(self.addr, self._REG_STATUS, b"\x00")

        if self.swap_xy:
            x, y = y, x
        if self.invert_x and self.width is not None:
            x = (self.width - 1) - x
        if self.invert_y and self.height is not None:
            y = (self.height - 1) - y
        return x, y, size

