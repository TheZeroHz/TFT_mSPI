from ..core.panel import Panel


class ST7789(Panel):
    """
    ST7789 SPI panel.

    Many ST7789 modules use offsets and non-240x320 geometries; override by
    passing width/height/x_offset/y_offset.
    """

    width = 240
    height = 320

    SLPOUT = 0x11
    NORON = 0x13
    INVON = 0x21
    DISPON = 0x29
    CASET = 0x2A
    RASET = 0x2B
    MADCTL = 0x36
    COLMOD = 0x3A

    TFT_MAD_MY = 0x80
    TFT_MAD_MX = 0x40
    TFT_MAD_MV = 0x20
    TFT_MAD_BGR = 0x08
    TFT_MAD_RGB = 0x00

    pixel_format = 16

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
            (self.SLPOUT, None, 120),
            (self.NORON, None, 0),
            (self.MADCTL, bytes([co]), 0),
            (0xB6, bytes([0x0A, 0x82]), 0),
            (0xB0, bytes([0x00, 0xE0]), 0),  # RAMCTRL
            (self.COLMOD, bytes([0x55]), 10),
            (0xB2, bytes([0x0C, 0x0C, 0x00, 0x33, 0x33]), 0),  # PORCTRL
            (0xB7, bytes([0x35]), 0),  # GCTRL
            (0xBB, bytes([0x28]), 0),  # VCOMS
            (0xC0, bytes([0x0C]), 0),  # LCMCTRL
            (0xC2, bytes([0x01, 0xFF]), 0),  # VDVVRHEN
            (0xC3, bytes([0x10]), 0),  # VRHS
            (0xC4, bytes([0x20]), 0),  # VDVSET
            (0xC6, bytes([0x0F]), 0),  # FRCTR2
            (0xD0, bytes([0xA4, 0xA1]), 0),  # PWCTRL1
            (0xE0, bytes([0xD0, 0x00, 0x02, 0x07, 0x0A, 0x28, 0x32, 0x44, 0x42, 0x06, 0x0E, 0x12, 0x14, 0x17]), 0),
            (0xE1, bytes([0xD0, 0x00, 0x02, 0x07, 0x0A, 0x28, 0x31, 0x54, 0x47, 0x0E, 0x1C, 0x17, 0x1B, 0x1E]), 0),
            ((self.INVON if self.invert else 0x20), None, 0),
            (self.CASET, bytes([0x00, self.x_offset & 0xFF, 0x00, (self.x_offset + self.width - 1) & 0xFF]), 0),
            (self.RASET, bytes([0x00, self.y_offset & 0xFF, 0x00, (self.y_offset + self.height - 1) & 0xFF]), 0),
            (self.DISPON, None, 120),
        )

    def set_rotation(self, tft, rotation):
        rot = int(rotation) & 3
        co = self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB
        if rot == 0:
            mad = co
        elif rot == 1:
            mad = self.TFT_MAD_MX | self.TFT_MAD_MV | co
        elif rot == 2:
            mad = self.TFT_MAD_MX | self.TFT_MAD_MY | co
        else:
            mad = self.TFT_MAD_MV | self.TFT_MAD_MY | co
        self.bus.write_cmd(self.MADCTL)
        self.bus.write_data(bytearray([mad & 0xFF]))

