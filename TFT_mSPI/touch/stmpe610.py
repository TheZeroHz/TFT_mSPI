try:
    import time
except ImportError:  # pragma: no cover
    time = None

from .base import TouchBase


class STMPE610(TouchBase):
    """
    STMPE610 resistive touch controller (SPI).

    Minimal FIFO-based implementation for typical STMPE610 modules.
    """

    _SYS_CTRL1 = 0x03
    _SYS_CTRL2 = 0x04
    _TSC_CTRL = 0x40
    _TSC_CFG = 0x41
    _FIFO_TH = 0x4A
    _FIFO_STA = 0x4B
    _FIFO_SIZE = 0x4C
    _TSC_DATA_XYZ = 0xD7
    _INT_STA = 0x0B

    def __init__(
        self,
        spi,
        cs,
        *,
        width=None,
        height=None,
        invert_x=False,
        invert_y=False,
        swap_xy=False,
        z_threshold=1,
        freq_hz=None,
    ):
        super().__init__()
        self.spi = spi
        self.cs = cs
        self.width = width
        self.height = height
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)
        self.swap_xy = bool(swap_xy)
        self.z_threshold = int(z_threshold)
        self.freq_hz = freq_hz
        self.cs(1)
        self._init()

    def _begin(self):
        if self.freq_hz is not None and hasattr(self.spi, "init"):
            try:
                self.spi.init(baudrate=self.freq_hz)
            except TypeError:
                pass
        self.cs(0)

    def _end(self):
        self.cs(1)

    def _read_reg(self, reg, n=1):
        self._begin()
        try:
            self.spi.write(bytearray([0x80 | (reg & 0x7F)]))
            b = bytearray(n)
            self.spi.readinto(b, 0x00)
            return b
        finally:
            self._end()

    def _write_reg(self, reg, data):
        self._begin()
        try:
            self.spi.write(bytearray([reg & 0x7F]))
            if isinstance(data, int):
                self.spi.write(bytearray([data & 0xFF]))
            else:
                self.spi.write(data)
        finally:
            self._end()

    def _init(self):
        self._write_reg(self._SYS_CTRL1, 0x02)
        if time is not None:
            time.sleep_ms(10)
        self._write_reg(self._SYS_CTRL1, 0x00)
        self._write_reg(self._SYS_CTRL2, 0x00)
        self._write_reg(self._TSC_CFG, bytes([0x9A, 0x00]))
        self._write_reg(self._FIFO_TH, 0x01)
        self._write_reg(self._FIFO_STA, 0x01)
        self._write_reg(self._FIFO_STA, 0x00)
        self._write_reg(self._TSC_CTRL, 0x01)

    def touched(self):
        return self._read_reg(self._FIFO_SIZE, 1)[0] > 0

    def get_point(self):
        if not self.touched():
            return None
        d = self._read_reg(self._TSC_DATA_XYZ, 4)
        x = (d[0] << 4) | (d[1] >> 4)
        y = ((d[1] & 0x0F) << 8) | d[2]
        z = d[3]

        self._write_reg(self._INT_STA, 0xFF)

        if z <= self.z_threshold:
            return None
        if self.swap_xy:
            x, y = y, x
        if self.invert_x and self.width is not None:
            x = (self.width - 1) - x
        if self.invert_y and self.height is not None:
            y = (self.height - 1) - y
        return x, y, z

