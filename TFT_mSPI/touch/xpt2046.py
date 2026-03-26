try:
    import time
except ImportError:  # pragma: no cover
    time = None

from .base import TouchBase


class XPT2046(TouchBase):
    """
    XPT2046 / ADS7846 resistive touch controller (SPI).

    - Provide `cal` as (xmin, xmax, ymin, ymax) in raw 12-bit-ish units.
    - Set invert/swap to match your wiring/orientation.
    """

    CMD_X = 0xD0
    CMD_Y = 0x90
    CMD_Z1 = 0xB0
    CMD_Z2 = 0xC0

    def __init__(
        self,
        spi,
        cs,
        *,
        cal=None,
        width=None,
        height=None,
        invert_x=False,
        invert_y=False,
        swap_xy=False,
        z_threshold=350,
        samples=3,
        freq_hz=None,
    ):
        super().__init__()
        self.spi = spi
        self.cs = cs
        self.cal = cal
        self.width = width
        self.height = height
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)
        self.swap_xy = bool(swap_xy)
        self.z_threshold = int(z_threshold)
        self.samples = int(samples)
        self.freq_hz = freq_hz
        self.cs(1)

    def _begin(self):
        if self.freq_hz is not None and hasattr(self.spi, "init"):
            try:
                self.spi.init(baudrate=self.freq_hz)
            except TypeError:
                pass
        self.cs(0)

    def _end(self):
        self.cs(1)

    def _read12(self, cmd):
        self.spi.write(bytearray([cmd & 0xFF]))
        b = bytearray(2)
        self.spi.readinto(b, 0x00)
        return ((b[0] << 8) | b[1]) >> 3

    def _read_raw_once(self):
        self._begin()
        try:
            z = 0xFFF
            z += self._read12(self.CMD_Z1)
            z -= self._read12(self.CMD_Z2)
            if z == 4095:
                z = 0
            x = self._read12(self.CMD_X)
            y = self._read12(self.CMD_Y)
        finally:
            self._end()
        return x, y, z

    def touched(self):
        _, _, z = self._read_raw_once()
        return z > self.z_threshold

    def get_raw(self):
        xs = 0
        ys = 0
        zs = 0
        n = max(1, self.samples)
        for _ in range(n):
            x, y, z = self._read_raw_once()
            xs += x
            ys += y
            zs += z
            if time is not None:
                time.sleep_ms(1)
        return xs // n, ys // n, zs // n

    def _apply_cal(self, x, y):
        if not self.cal or self.width is None or self.height is None:
            return x, y
        xmin, xmax, ymin, ymax = self.cal
        if xmax == xmin or ymax == ymin:
            return x, y
        if x < xmin:
            x = xmin
        if x > xmax:
            x = xmax
        if y < ymin:
            y = ymin
        if y > ymax:
            y = ymax
        sx = (x - xmin) * self.width // (xmax - xmin)
        sy = (y - ymin) * self.height // (ymax - ymin)
        return sx, sy

    def get_point(self):
        x, y, z = self.get_raw()
        if z <= self.z_threshold:
            return None
        if self.swap_xy:
            x, y = y, x
        x, y = self._apply_cal(x, y)
        if self.invert_x and self.width is not None:
            x = (self.width - 1) - x
        if self.invert_y and self.height is not None:
            y = (self.height - 1) - y
        return x, y, z

