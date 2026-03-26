from ..core.panel import Panel


class ST7796(Panel):
    width = 320
    height = 480

    SWRESET = 0x01
    SLPOUT = 0x11
    DISPON = 0x29
    MADCTL = 0x36
    COLMOD = 0x3A

    TFT_MAD_MY = 0x80
    TFT_MAD_MX = 0x40
    TFT_MAD_MV = 0x20
    TFT_MAD_BGR = 0x08
    TFT_MAD_RGB = 0x00

    pixel_format = 16

    def __init__(self, bus, *, width=None, height=None, bgr=True, x_offset=0, y_offset=0):
        if width is not None:
            self.width = int(width)
        if height is not None:
            self.height = int(height)
        super().__init__(bus, bgr=bgr, x_offset=x_offset, y_offset=y_offset)

    def init_sequence(self):
        co = self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB
        return (
            (self.SWRESET, None, 120),
            (self.SLPOUT, None, 120),
            (0xF0, bytes([0xC3]), 0),
            (0xF0, bytes([0x96]), 0),
            (self.MADCTL, bytes([0x48 if co == self.TFT_MAD_BGR else 0x40]), 0),
            (self.COLMOD, bytes([0x55]), 0),
            (0xB4, bytes([0x01]), 0),
            (0xB6, bytes([0x80, 0x02, 0x3B]), 0),
            (0xE8, bytes([0x40, 0x8A, 0x00, 0x00, 0x29, 0x19, 0xA5, 0x33]), 0),
            (0xC1, bytes([0x06]), 0),
            (0xC2, bytes([0xA7]), 0),
            (0xC5, bytes([0x18]), 120),
            (0xE0, bytes([0xF0, 0x09, 0x0B, 0x06, 0x04, 0x15, 0x2F, 0x54, 0x42, 0x3C, 0x17, 0x14, 0x18, 0x1B]), 0),
            (0xE1, bytes([0xE0, 0x09, 0x0B, 0x06, 0x04, 0x03, 0x2B, 0x43, 0x42, 0x3B, 0x16, 0x14, 0x17, 0x1B]), 120),
            (0xF0, bytes([0x3C]), 0),
            (0xF0, bytes([0x69]), 120),
            (self.DISPON, None, 0),
        )

    def set_rotation(self, tft, rotation):
        rot = int(rotation) & 3
        co = self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB
        if rot == 0:
            mad = self.TFT_MAD_MX | co
        elif rot == 1:
            mad = self.TFT_MAD_MV | co
        elif rot == 2:
            mad = self.TFT_MAD_MY | co
        else:
            mad = self.TFT_MAD_MX | self.TFT_MAD_MY | self.TFT_MAD_MV | co
        self.bus.write_cmd(self.MADCTL)
        self.bus.write_data(bytearray([mad & 0xFF]))

