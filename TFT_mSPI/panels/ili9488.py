from ..core.panel import Panel


class ILI9488(Panel):
    width = 320
    height = 480

    SWRESET = 0x01
    SLPOUT = 0x11
    DISPON = 0x29
    NORON = 0x13
    MADCTL = 0x36
    COLMOD = 0x3A
    INVOFF = 0x20
    INVON = 0x21

    TFT_MAD_MY = 0x80
    TFT_MAD_MX = 0x40
    TFT_MAD_MV = 0x20
    TFT_MAD_BGR = 0x08
    TFT_MAD_RGB = 0x00

    pixel_format = 18

    def __init__(self, bus, *, width=None, height=None, bgr=True, x_offset=0, y_offset=0, invert=False):
        if width is not None:
            self.width = int(width)
        if height is not None:
            self.height = int(height)
        self.invert = bool(invert)
        super().__init__(bus, bgr=bgr, x_offset=x_offset, y_offset=y_offset)

    def init_sequence(self):
        co = self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB
        return (
            (self.SWRESET, None, 120),
            (0xE0, bytes([0x00, 0x03, 0x09, 0x08, 0x16, 0x0A, 0x3F, 0x78, 0x4C, 0x09, 0x0A, 0x08, 0x16, 0x1A, 0x0F]), 0),
            (0xE1, bytes([0x00, 0x16, 0x19, 0x03, 0x0F, 0x05, 0x32, 0x45, 0x46, 0x04, 0x0E, 0x0D, 0x35, 0x37, 0x0F]), 0),
            (0xC0, bytes([0x17, 0x15]), 0),
            (0xC1, bytes([0x41]), 0),
            (0xC5, bytes([0x00, 0x12, 0x80]), 0),
            (self.MADCTL, bytes([self.TFT_MAD_MX | co]), 0),
            (self.COLMOD, bytes([0x66]), 0),  # 18-bit
            (0xB0, bytes([0x00]), 0),
            (0xB1, bytes([0xA0]), 0),
            (0xB4, bytes([0x02]), 0),
            (0xB6, bytes([0x02, 0x02, 0x3B]), 0),
            (0xB7, bytes([0xC6]), 0),
            (0xF7, bytes([0xA9, 0x51, 0x2C, 0x82]), 0),
            ((self.INVON if self.invert else self.INVOFF), None, 0),
            (self.SLPOUT, None, 120),
            (self.NORON, None, 10),
            (self.DISPON, None, 25),
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

