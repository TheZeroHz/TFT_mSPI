try:
    import time
except ImportError:  # pragma: no cover
    time = None


class SPIBus:
    """
    Minimal SPI bus wrapper for TFT controllers.

    Expects a MicroPython SPI object (machine.SPI or soft SPI) plus Pin objects
    for dc/cs/rst (rst optional).
    """

    def __init__(self, spi, dc, cs=None, rst=None, *, baudrate=None, write_limit=4096):
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.rst = rst
        self.write_limit = int(write_limit) if write_limit else 0

        if baudrate is not None and hasattr(self.spi, "init"):
            try:
                self.spi.init(baudrate=baudrate)
            except TypeError:
                # Some ports require full init args; leave as-is.
                pass

        if self.cs is not None:
            self.cs(1)
        if self.dc is not None:
            self.dc(1)
        if self.rst is not None:
            self.rst(1)

    def reset(self, *, pulse_ms=20, post_ms=120):
        if self.rst is None or time is None:
            return
        self.rst(1)
        time.sleep_ms(1)
        self.rst(0)
        time.sleep_ms(pulse_ms)
        self.rst(1)
        time.sleep_ms(post_ms)

    def _cs(self, level):
        if self.cs is not None:
            self.cs(level)

    def write_cmd(self, cmd):
        self.dc(0)
        self._cs(0)
        self.spi.write(bytearray([cmd & 0xFF]))
        self._cs(1)
        self.dc(1)

    def write_data(self, data):
        if data is None:
            return
        self.dc(1)
        self._cs(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data & 0xFF]))
        else:
            if self.write_limit and hasattr(data, "__len__") and len(data) > self.write_limit:
                mv = memoryview(data)
                for i in range(0, len(mv), self.write_limit):
                    self.spi.write(mv[i : i + self.write_limit])
            else:
                self.spi.write(data)
        self._cs(1)

    def write_cmd_data(self, cmd, data=None):
        self.write_cmd(cmd)
        if data:
            self.write_data(data)

