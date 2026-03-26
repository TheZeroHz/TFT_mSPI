from ..core.panel import Panel


class ILI9341(Panel):
    width = 240
    height = 320

    SLPOUT = 0x11
    DISPON = 0x29
    MADCTL = 0x36
    PIXFMT = 0x3A
    SWRESET = 0x01
    NORON = 0x13
    INVOFF = 0x20
    CASET = 0x2A
    RASET = 0x2B

    TFT_MAD_MY = 0x80
    TFT_MAD_MX = 0x40
    TFT_MAD_MV = 0x20
    TFT_MAD_BGR = 0x08
    TFT_MAD_RGB = 0x00

    pixel_format = 16  # RGB565

    def __init__(self, bus, *, bgr=True, x_offset=0, y_offset=0, invert=False, init_variant=1):
        self.invert = bool(invert)
        self.init_variant = 2 if int(init_variant) == 2 else 1
        super().__init__(bus, bgr=bgr, x_offset=x_offset, y_offset=y_offset)

    def init_sequence(self):
        x0 = self.x_offset
        y0 = self.y_offset
        x1 = self.x_offset + self.width - 1
        y1 = self.y_offset + self.height - 1
        if self.init_variant == 2:
            # Matches TFT_eSPI ILI9341_2_DRIVER alternative sequence.
            return (
                (0xCF, bytes([0x00, 0xC1, 0x30]), 0),
                (0xED, bytes([0x64, 0x03, 0x12, 0x81]), 0),
                (0xE8, bytes([0x85, 0x00, 0x78]), 0),
                (0xCB, bytes([0x39, 0x2C, 0x00, 0x34, 0x02]), 0),
                (0xF7, bytes([0x20]), 0),
                (0xEA, bytes([0x00, 0x00]), 0),
                (0xC0, bytes([0x10]), 0),  # PWCTR1
                (0xC1, bytes([0x00]), 0),  # PWCTR2
                (0xC5, bytes([0x30, 0x30]), 0),  # VMCTR1
                (0xC7, bytes([0xB7]), 0),  # VMCTR2
                (self.PIXFMT, bytes([0x55]), 0),
                (self.MADCTL, bytes([(self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB)]), 0),
                (0xB1, bytes([0x00, 0x1A]), 0),  # FRMCTR1
                (0xB6, bytes([0x08, 0x82, 0x27]), 0),  # DFUNCTR
                (0xF2, bytes([0x00]), 0),
                (0x26, bytes([0x01]), 0),  # GAMMASET
                (0xE0, bytes([0x0F, 0x2A, 0x28, 0x08, 0x0E, 0x08, 0x54, 0xA9, 0x43, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00]), 0),
                (0xE1, bytes([0x00, 0x15, 0x17, 0x07, 0x11, 0x06, 0x2B, 0x56, 0x3C, 0x05, 0x10, 0x0F, 0x3F, 0x3F, 0x0F]), 0),
                (self.INVOFF if not self.invert else 0x21, None, 0),
                (self.RASET, bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]), 0),
                (self.CASET, bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]), 0),
                (self.SLPOUT, None, 120),
                (self.DISPON, None, 120),
            )
        return (
            (self.SWRESET, None, 150),
            (0xEF, bytes([0x03, 0x80, 0x02]), 0),
            (0xCF, bytes([0x00, 0xC1, 0x30]), 0),
            (0xED, bytes([0x64, 0x03, 0x12, 0x81]), 0),
            (0xE8, bytes([0x85, 0x00, 0x78]), 0),
            (0xCB, bytes([0x39, 0x2C, 0x00, 0x34, 0x02]), 0),
            (0xF7, bytes([0x20]), 0),
            (0xEA, bytes([0x00, 0x00]), 0),
            (0xC0, bytes([0x23]), 0),  # PWCTR1
            (0xC1, bytes([0x10]), 0),  # PWCTR2
            (0xC5, bytes([0x3E, 0x28]), 0),  # VMCTR1
            (0xC7, bytes([0x86]), 0),  # VMCTR2
            (self.MADCTL, bytes([self.TFT_MAD_MX | (self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB)]), 0),
            (self.PIXFMT, bytes([0x55]), 10),  # 16-bit
            (0xB1, bytes([0x00, 0x13]), 0),  # FRMCTR1 (TFT_eSPI default)
            (0xB6, bytes([0x08, 0x82, 0x27]), 0),  # DFUNCTR
            (0xF2, bytes([0x00]), 0),
            (0x26, bytes([0x01]), 0),  # GAMMASET
            (0xE0, bytes([0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E, 0xF1, 0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00]), 0),
            (0xE1, bytes([0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31, 0xC1, 0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F]), 0),
            (self.INVOFF if not self.invert else 0x21, None, 0),
            (self.CASET, bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]), 0),
            (self.RASET, bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]), 0),
            (self.SLPOUT, None, 120),
            (self.NORON, None, 10),
            (self.DISPON, None, 120),
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

