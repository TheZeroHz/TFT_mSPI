try:
    import time
except ImportError:  # pragma: no cover
    time = None


class Panel:
    """
    Base class for panel controllers.

    Subclasses must define:
      - width, height (native, unrotated)
      - init_sequence(): iterable of (cmd, data_bytes_or_int_or_None, delay_ms_int)
      - set_rotation(tft, rotation): write MADCTL etc.
    """

    width = 0
    height = 0

    def __init__(self, bus, *, bgr=False, x_offset=0, y_offset=0):
        self.bus = bus
        self.bgr = bool(bgr)
        self.x_offset = int(x_offset)
        self.y_offset = int(y_offset)

    def hardware_reset(self):
        self.bus.reset()

    def init(self):
        for item in self.init_sequence():
            if item is None:
                continue
            cmd, data, delay_ms = item
            self.bus.write_cmd(cmd)
            if data is not None:
                if isinstance(data, int):
                    self.bus.write_data(bytearray([data & 0xFF]))
                else:
                    self.bus.write_data(data)
            if delay_ms and time is not None:
                time.sleep_ms(int(delay_ms))

    def init_sequence(self):  # pragma: no cover
        return ()

    def set_rotation(self, tft, rotation):  # pragma: no cover
        raise NotImplementedError

