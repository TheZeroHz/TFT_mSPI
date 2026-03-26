from ..core.panel import Panel


class ST7735(Panel):
    """
    ST7735 (ST7735R/ST7735B) SPI panel.

    `tab` controls the common init variant/offets:
      - "red": 128x160, no offsets (common)
      - "green": typical col/row offsets (often x+1,y+1)
      - "blue": typical col/row offsets (often x+2,y+1)
      - "blue2": same as blue but with explicit offsets
    """

    width = 128
    height = 160

    # ST7735 specific commands (subset)
    SWRESET = 0x01
    SLPOUT = 0x11
    NORON = 0x13
    DISPON = 0x29
    CASET = 0x2A
    RASET = 0x2B
    COLMOD = 0x3A
    MADCTL = 0x36

    FRMCTR1 = 0xB1
    FRMCTR2 = 0xB2
    FRMCTR3 = 0xB3
    INVCTR = 0xB4
    DISSET5 = 0xB6

    PWCTR1 = 0xC0
    PWCTR2 = 0xC1
    PWCTR3 = 0xC2
    PWCTR4 = 0xC3
    PWCTR5 = 0xC4
    VMCTR1 = 0xC5
    PWCTR6 = 0xFC

    GMCTRP1 = 0xE0
    GMCTRN1 = 0xE1

    TFT_MAD_BGR = 0x08
    TFT_MAD_RGB = 0x00

    _ROT_MADCTL = (0x00, 0x60, 0xC0, 0xA0)

    def __init__(self, bus, *, tab="red", bgr=False, x_offset=None, y_offset=None):
        self.tab = str(tab).lower()

        if x_offset is None or y_offset is None:
            if self.tab in ("green", "greentab"):
                x_offset = 1
                y_offset = 1
            elif self.tab in ("blue", "blue2", "initb"):
                x_offset = 2
                y_offset = 1
            else:
                x_offset = 0
                y_offset = 0

        super().__init__(bus, bgr=bgr, x_offset=x_offset, y_offset=y_offset)

    def init_sequence(self):
        if self.tab in ("blue", "blue2", "initb"):
            return (
                (self.SWRESET, None, 50),
                (self.SLPOUT, None, 500),
                (self.COLMOD, bytes([0x05]), 10),
                (self.FRMCTR1, bytes([0x00, 0x06, 0x03]), 10),
                (self.MADCTL, bytes([0x08]), 0),
                (self.DISSET5, bytes([0x15, 0x02]), 0),
                (self.INVCTR, bytes([0x00]), 0),
                (self.PWCTR1, bytes([0x02, 0x70]), 10),
                (self.PWCTR2, bytes([0x05]), 0),
                (self.PWCTR3, bytes([0x01, 0x02]), 0),
                (self.VMCTR1, bytes([0x3C, 0x38]), 10),
                (self.PWCTR6, bytes([0x11, 0x15]), 0),
                (self.GMCTRP1, bytes([0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D, 0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10]), 0),
                (self.GMCTRN1, bytes([0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D, 0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10]), 10),
                (self.CASET, bytes([0x00, self.x_offset & 0xFF, 0x00, (self.x_offset + self.width - 1) & 0xFF]), 0),
                (self.RASET, bytes([0x00, self.y_offset & 0xFF, 0x00, (self.y_offset + self.height - 1) & 0xFF]), 0),
                (self.NORON, None, 10),
                (self.DISPON, None, 500),
            )

        return (
            (self.SWRESET, None, 150),
            (self.SLPOUT, None, 500),
            (self.FRMCTR1, bytes([0x01, 0x2C, 0x2D]), 0),
            (self.FRMCTR2, bytes([0x01, 0x2C, 0x2D]), 0),
            (self.FRMCTR3, bytes([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]), 10),
            (self.INVCTR, bytes([0x07]), 0),
            (self.PWCTR1, bytes([0xA2, 0x02, 0x84]), 0),
            (self.PWCTR2, bytes([0xC5]), 0),
            (self.PWCTR3, bytes([0x0A, 0x00]), 0),
            (self.PWCTR4, bytes([0x8A, 0x2A]), 0),
            (self.PWCTR5, bytes([0x8A, 0xEE]), 0),
            (self.VMCTR1, bytes([0x0E]), 0),
            (0x20, None, 0),  # INVOFF
            (self.MADCTL, bytes([0xC8]), 0),
            (self.COLMOD, bytes([0x05]), 0),
            (self.CASET, bytes([0x00, self.x_offset & 0xFF, 0x00, (self.x_offset + self.width - 1) & 0xFF]), 0),
            (self.RASET, bytes([0x00, self.y_offset & 0xFF, 0x00, (self.y_offset + self.height - 1) & 0xFF]), 0),
            (self.GMCTRP1, bytes([0x0F, 0x1A, 0x0F, 0x18, 0x2F, 0x28, 0x20, 0x22, 0x1F, 0x1B, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10]), 0),
            (self.GMCTRN1, bytes([0x0F, 0x1B, 0x0F, 0x17, 0x33, 0x2C, 0x29, 0x2E, 0x30, 0x30, 0x39, 0x3F, 0x00, 0x07, 0x03, 0x10]), 10),
            (self.DISPON, None, 100),
            (self.NORON, None, 10),
        )

    def set_rotation(self, tft, rotation):
        rgb_bit = self.TFT_MAD_BGR if self.bgr else self.TFT_MAD_RGB
        madctl = self._ROT_MADCTL[int(rotation) & 3] | rgb_bit
        self.bus.write_cmd(self.MADCTL)
        self.bus.write_data(bytearray([madctl & 0xFF]))

