from ..core.panel import Panel


class ILI9486(Panel):
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

    def __init__(self, bus, *, width=None, height=None, bgr=True, x_offset=0, y_offset=0, invert=True):
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
            (self.SLPOUT, None, 120),
            (self.COLMOD, bytes([0x66]), 0),  # 18-bit
            (0xC0, bytes([0x0E, 0x0E]), 0),
            (0xC1, bytes([0x41, 0x00]), 0),
            (0xC2, bytes([0x55]), 0),
            (0xC5, bytes([0x00, 0x00, 0x00, 0x00]), 0),
            (0xE0, bytes([0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00]), 0),
            (0xE1, bytes([0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00]), 0),
            ((self.INVON if self.invert else self.INVOFF), None, 0),
            (self.MADCTL, bytes([self.TFT_MAD_MX | co]), 0),
            (self.NORON, None, 10),
            (self.DISPON, None, 150),
        )

    def set_rotation(self, tft, rotation):
        rot = int(rotation) & 3
        co = self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB
        if rot == 0:
            mad = co | self.TFT_MAD_MX
        elif rot == 1:
            mad = co | self.TFT_MAD_MV
        elif rot == 2:
            mad = co | self.TFT_MAD_MY
        else:
            mad = co | self.TFT_MAD_MV | self.TFT_MAD_MX | self.TFT_MAD_MY
        self.bus.write_cmd(self.MADCTL)
        self.bus.write_data(bytearray([mad & 0xFF]))

