try:
    from micropython import const  # type: ignore
except Exception:  # pragma: no cover
    def const(x):  # type: ignore
        return x


def _swap565_inplace(buf):
    mv = memoryview(buf)
    ln = len(mv)
    if ln & 1:
        raise ValueError("RGB565 buffer length must be even")
    for i in range(0, ln, 2):
        b0 = mv[i]
        mv[i] = mv[i + 1]
        mv[i + 1] = b0


class TFT_eSprite:
    """
    Minimal TFT_eSPI-like sprite for MicroPython.

    Stores pixels as RGB565 big-endian in a contiguous bytearray.
    """

    def __init__(self, tft):
        self._tft = tft
        self._w = 0
        self._h = 0
        self._buf = None
        self._bpp = 16
        self._bitmap_fg = 0xFFFF
        self._bitmap_bg = 0x0000

    def createSprite(self, w, h):
        self._w = int(w)
        self._h = int(h)
        if self._w <= 0 or self._h <= 0:
            self._buf = bytearray()
        else:
            self._buf = bytearray(2 * self._w * self._h)
        return self._buf

    def deleteSprite(self):
        self._w = 0
        self._h = 0
        self._buf = None

    def width(self):
        return self._w

    def height(self):
        return self._h

    def getPointer(self):
        return self._buf

    def created(self):
        return self._buf is not None and self._w > 0 and self._h > 0

    def setColorDepth(self, b):
        # Compatibility: current implementation supports 16bpp sprites only.
        self._bpp = 16 if int(b) >= 16 else int(b)
        return self._buf

    def getColorDepth(self):
        return self._bpp

    def fillSprite(self, color):
        if self._buf is None:
            return
        c = int(color) & 0xFFFF
        hi = (c >> 8) & 0xFF
        lo = c & 0xFF
        self._buf[:] = bytes([hi, lo]) * (self._w * self._h)

    def drawPixel(self, x, y, color):
        if self._buf is None:
            return
        x = int(x)
        y = int(y)
        if x < 0 or y < 0 or x >= self._w or y >= self._h:
            return
        c = int(color) & 0xFFFF
        p = 2 * (y * self._w + x)
        self._buf[p] = (c >> 8) & 0xFF
        self._buf[p + 1] = c & 0xFF

    def readPixel(self, x, y):
        if self._buf is None:
            return 0
        x = int(x)
        y = int(y)
        if x < 0 or y < 0 or x >= self._w or y >= self._h:
            return 0
        p = 2 * (y * self._w + x)
        return (self._buf[p] << 8) | self._buf[p + 1]

    def setBitmapColor(self, fg, bg):
        self._bitmap_fg = int(fg) & 0xFFFF
        self._bitmap_bg = int(bg) & 0xFFFF

    def drawFastHLine(self, x, y, w, color):
        self.fillRect(x, y, w, 1, color)

    def drawFastVLine(self, x, y, h, color):
        self.fillRect(x, y, 1, h, color)

    def drawLine(self, x0, y0, x1, y1, color):
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.drawPixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = err << 1
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fillRect(self, x, y, w, h, color):
        if self._buf is None:
            return
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        if w <= 0 or h <= 0:
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self._w - 1, x + w - 1)
        y1 = min(self._h - 1, y + h - 1)
        if x1 < x0 or y1 < y0:
            return
        c = int(color) & 0xFFFF
        px = bytes([(c >> 8) & 0xFF, c & 0xFF])
        row = px * (x1 - x0 + 1)
        for yy in range(y0, y1 + 1):
            p = 2 * (yy * self._w + x0)
            self._buf[p : p + len(row)] = row

    def pushImage(self, x, y, w, h, data, sbpp=0):
        # sbpp kept for compatibility.
        if self._buf is None:
            return
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        if w <= 0 or h <= 0:
            return
        mv = memoryview(data)
        for yy in range(h):
            dy = y + yy
            if dy < 0 or dy >= self._h:
                continue
            for xx in range(w):
                dx = x + xx
                if dx < 0 or dx >= self._w:
                    continue
                si = 2 * (yy * w + xx)
                di = 2 * (dy * self._w + dx)
                self._buf[di] = mv[si]
                self._buf[di + 1] = mv[si + 1]

    def pushToSprite(self, dspr, x, y, transparent=None):
        if not self.created() or dspr is None or not hasattr(dspr, "drawPixel"):
            return False
        x = int(x)
        y = int(y)
        trans = None if transparent is None else (int(transparent) & 0xFFFF)
        for yy in range(self._h):
            for xx in range(self._w):
                c = self.readPixel(xx, yy)
                if trans is not None and c == trans:
                    continue
                dspr.drawPixel(x + xx, y + yy, c)
        return True

    def pushSprite(self, x, y, transparent=None):
        if self._buf is None or self._w <= 0 or self._h <= 0:
            return
        if transparent is None:
            self._tft.blit_buffer(int(x), int(y), self._w, self._h, self._buf)
            return

        # Transparency: build a line buffer and only write visible runs.
        # This keeps RAM modest while avoiding per-pixel display writes.
        trans = int(transparent) & 0xFFFF
        hi_t = (trans >> 8) & 0xFF
        lo_t = trans & 0xFF
        mv = memoryview(self._buf)
        for row in range(self._h):
            base = 2 * row * self._w
            col = 0
            while col < self._w:
                # skip transparent pixels
                while col < self._w:
                    i = base + 2 * col
                    if mv[i] != hi_t or mv[i + 1] != lo_t:
                        break
                    col += 1
                if col >= self._w:
                    break
                run_start = col
                # find end of opaque run
                while col < self._w:
                    i = base + 2 * col
                    if mv[i] == hi_t and mv[i + 1] == lo_t:
                        break
                    col += 1
                run_w = col - run_start
                if run_w:
                    start_i = base + 2 * run_start
                    end_i = start_i + 2 * run_w
                    self._tft.blit_buffer(int(x) + run_start, int(y) + row, run_w, 1, mv[start_i:end_i])


class TFT_eSPI:
    """
    Compatibility facade for common Arduino TFT_eSPI APIs.

    This wraps a `tft_mspi.core.tft.TFT` instance. It is intentionally minimal
    but covers the most common porting pain points: naming, pushImage, sprites.
    """

    # Datums (subset)
    TL_DATUM = const(0)
    TC_DATUM = const(1)
    TR_DATUM = const(2)
    ML_DATUM = const(3)
    MC_DATUM = const(4)
    MR_DATUM = const(5)
    BL_DATUM = const(6)
    BC_DATUM = const(7)
    BR_DATUM = const(8)

    def __init__(self, tft):
        self.tft = tft
        self._text_color = getattr(tft, "WHITE", 0xFFFF)
        self._text_bg = None
        self._text_wrap = True
        self._text_font = None
        self._text_size = 1
        self._cursor_x = 0
        self._cursor_y = 0
        self._datum = self.TL_DATUM
        self._pad_x = 0
        self._swap_bytes = False
        self._pivot_x = 0
        self._pivot_y = 0
        self._bitmap_fg = getattr(tft, "WHITE", 0xFFFF)
        self._bitmap_bg = getattr(tft, "BLACK", 0x0000)
        self._origin_x = 0
        self._origin_y = 0
        self._vp = (0, 0, int(getattr(tft, "width", 0)), int(getattr(tft, "height", 0)))
        self._attributes = {1: 0, 2: 1, 3: 0}

    # --- Pass-through helpers / Arduino naming ---
    def init(self):
        return self.tft.init()

    def begin(self, tc=0):
        # tc (tab colour) is for ST7735 setup in C++ and not needed here.
        return self.tft.init()

    def width(self):
        return self.tft.width

    def height(self):
        return self.tft.height

    def setRotation(self, r):
        return self.tft.set_rotation(r)

    def getRotation(self):
        return int(getattr(self.tft, "_rotation", 0))

    def fillScreen(self, color):
        return self.tft.fill_screen(color)

    def drawPixel(self, x, y, color):
        return self.tft.draw_pixel(int(x) + self._origin_x, int(y) + self._origin_y, color)

    def readPixel(self, x, y):
        # Not available on most SPI-only MicroPython drivers.
        return 0

    def drawLine(self, x0, y0, x1, y1, color):
        return self.tft.draw_line(x0, y0, x1, y1, color)

    def drawFastHLine(self, x, y, w, color):
        return self.tft.hline(x, y, w, color)

    def drawFastVLine(self, x, y, h, color):
        return self.tft.vline(x, y, h, color)

    def fillRect(self, x, y, w, h, color):
        return self.tft.fill_rect(x, y, w, h, color)

    def drawRect(self, x, y, w, h, color):
        return self.tft.draw_rect(x, y, w, h, color)

    def drawRoundRect(self, x, y, w, h, radius, color):
        return self.tft.draw_round_rect(x, y, w, h, radius, color)

    def fillRoundRect(self, x, y, w, h, radius, color):
        return self.tft.fill_round_rect(x, y, w, h, radius, color)

    def drawCircle(self, x, y, r, color):
        return self.tft.draw_circle(x, y, r, color)

    def fillCircle(self, x, y, r, color):
        return self.tft.fill_circle(x, y, r, color)

    def drawEllipse(self, x, y, rx, ry, color):
        return self.tft.draw_ellipse(x, y, rx, ry, color)

    def fillEllipse(self, x, y, rx, ry, color):
        return self.tft.fill_ellipse(x, y, rx, ry, color)

    def drawTriangle(self, x1, y1, x2, y2, x3, y3, color):
        return self.tft.draw_triangle(x1, y1, x2, y2, x3, y3, color)

    def fillTriangle(self, x1, y1, x2, y2, x3, y3, color):
        return self.tft.fill_triangle(x1, y1, x2, y2, x3, y3, color)

    def drawArc(self, x, y, r, start_angle, end_angle, color, thickness=1):
        return self.tft.draw_arc(x, y, r, start_angle, end_angle, color, thickness=thickness)

    def fillArc(self, x, y, r, start_angle, end_angle, color, thickness=None):
        return self.tft.fill_arc(x, y, r, start_angle, end_angle, color, thickness=thickness)

    def invertDisplay(self, enable=True):
        return self.tft.invert(enable)

    def startWrite(self):
        return None

    def endWrite(self):
        return None

    def begin_nin_write(self):
        return None

    def end_nin_write(self):
        return None

    def setAddrWindow(self, x, y, w, h):
        x = int(x) + self._origin_x
        y = int(y) + self._origin_y
        self.tft._set_addr_window(x, y, x + int(w) - 1, y + int(h) - 1)

    def setWindow(self, xs, ys, xe, ye):
        self.tft._set_addr_window(
            int(xs) + self._origin_x,
            int(ys) + self._origin_y,
            int(xe) + self._origin_x,
            int(ye) + self._origin_y,
        )

    def setOrigin(self, x, y):
        self._origin_x = int(x)
        self._origin_y = int(y)

    def getOriginX(self):
        return int(self._origin_x)

    def getOriginY(self):
        return int(self._origin_y)

    def setViewport(self, x, y, w, h, vpDatum=True):
        self._vp = (int(x), int(y), int(w), int(h))

    def checkViewport(self, x, y, w, h):
        vx, vy, vw, vh = self._vp
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        return not (x + w <= vx or y + h <= vy or x >= vx + vw or y >= vy + vh)

    def getViewportX(self):
        return self._vp[0]

    def getViewportY(self):
        return self._vp[1]

    def getViewportWidth(self):
        return self._vp[2]

    def getViewportHeight(self):
        return self._vp[3]

    def getViewportDatum(self):
        return True

    def frameViewport(self, color, w):
        vx, vy, vw, vh = self._vp
        self.drawRect(vx, vy, vw, vh, color)

    def resetViewport(self):
        self._vp = (0, 0, self.width(), self.height())

    def clipAddrWindow(self, x, y, w, h):
        return self.checkViewport(x, y, w, h)

    def clipWindow(self, xs, ys, xe, ye):
        return self.checkViewport(xs, ys, int(xe) - int(xs) + 1, int(ye) - int(ys) + 1)

    def sleep(self, enable=True):
        return self.tft.sleep(enable)

    # --- Text state (subset) ---
    def setTextColor(self, fg, bg=None):
        self._text_color = int(fg) & 0xFFFF
        self._text_bg = None if bg is None else (int(bg) & 0xFFFF)

    def setTextWrap(self, wrap=True):
        self._text_wrap = bool(wrap)

    def setTextFont(self, font):
        # For TFT_mSPI this is a dict like sysfont; user can pass that directly.
        self._text_font = font

    def setTextSize(self, s):
        self._text_size = s

    def setCursor(self, x, y):
        self._cursor_x = int(x)
        self._cursor_y = int(y)

    def getCursorX(self):
        return int(self._cursor_x)

    def getCursorY(self):
        return int(self._cursor_y)

    def setTextDatum(self, datum):
        self._datum = int(datum)

    def getTextDatum(self):
        return int(self._datum)

    def setTextPadding(self, x_width):
        self._pad_x = int(x_width)

    def getTextPadding(self):
        return int(self._pad_x)

    def drawString(self, string, x, y, font=None):
        if font is None:
            font = self._text_font
        if font is None:
            return 0
        # Datum alignment is implemented for the most common cases (TL, TC, TR).
        sx = self._text_size
        sy = self._text_size
        if not isinstance(sx, (tuple, list)):
            sx = int(sx)
            sy = int(sy)
        else:
            sx = int(sx[0])
            sy = int(sx[1]) if len(sx) > 1 else int(sx[0])

        w = self.textWidth(string, font)
        h = int(font["Height"]) * sy
        x0 = int(x)
        y0 = int(y)
        if self._datum == self.TC_DATUM:
            x0 = x0 - (w // 2)
        elif self._datum == self.TR_DATUM:
            x0 = x0 - w
        elif self._datum == self.MC_DATUM:
            x0 = x0 - (w // 2)
            y0 = y0 - (h // 2)
        elif self._datum == self.MR_DATUM:
            x0 = x0 - w
            y0 = y0 - (h // 2)
        elif self._datum == self.ML_DATUM:
            y0 = y0 - (h // 2)
        elif self._datum == self.BL_DATUM:
            y0 = y0 - h
        elif self._datum == self.BC_DATUM:
            x0 = x0 - (w // 2)
            y0 = y0 - h
        elif self._datum == self.BR_DATUM:
            x0 = x0 - w
            y0 = y0 - h

        # Optional padding to overdraw previous content (TFT_eSPI-style)
        pad_w = w
        if self._pad_x and self._pad_x > pad_w:
            pad_w = self._pad_x

        if self._text_bg is not None:
            self.tft.fill_rect(x0, y0, pad_w, h, self._text_bg)
        self.tft.text((x0, y0), str(string), self._text_color, font, (sx, sy), nowrap=not self._text_wrap)
        return w

    def print(self, s):
        # Very small subset: draw at cursor and advance horizontally.
        w = self.drawString(str(s), self._cursor_x, self._cursor_y, self._text_font)
        self._cursor_x += w

    def drawNumber(self, number, x, y, font=None):
        return self.drawString(str(int(number)), x, y, font=font)

    def drawFloat(self, value, decimal, x, y, font=None):
        fmt = "{:." + str(int(decimal)) + "f}"
        return self.drawString(fmt.format(float(value)), x, y, font=font)

    def drawCentreString(self, string, x, y, font=None):
        prev = self._datum
        self._datum = self.TC_DATUM
        w = self.drawString(string, x, y, font=font)
        self._datum = prev
        return w

    def drawRightString(self, string, x, y, font=None):
        prev = self._datum
        self._datum = self.TR_DATUM
        w = self.drawString(string, x, y, font=font)
        self._datum = prev
        return w

    def textWidth(self, string, font=None):
        if font is None:
            font = self._text_font
        if font is None:
            return 0
        return len(str(string)) * (int(font["Width"]) * int(self._text_size) + 1)

    def fontHeight(self, font=None):
        if font is None:
            font = self._text_font
        if font is None:
            return 0
        return int(font["Height"]) * int(self._text_size)

    # --- Bitmap / image helpers ---
    def setSwapBytes(self, swap):
        self._swap_bytes = bool(swap)

    def getSwapBytes(self):
        return bool(self._swap_bytes)

    def setBitmapColor(self, fgcolor, bgcolor):
        self._bitmap_fg = int(fgcolor) & 0xFFFF
        self._bitmap_bg = int(bgcolor) & 0xFFFF

    def drawBitmap(self, x, y, bitmap, w, h, fgcolor=None, bgcolor=None):
        # 1bpp bitmap, MSB first per byte (common Adafruit-style).
        if fgcolor is None:
            fgcolor = self._bitmap_fg
        if bgcolor is None:
            bgcolor = None  # transparent background by default
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        mv = memoryview(bitmap)
        byte_width = (w + 7) // 8
        for yy in range(h):
            row = yy * byte_width
            for xx in range(w):
                b = mv[row + (xx >> 3)]
                if b & (0x80 >> (xx & 7)):
                    self.tft.draw_pixel(x + xx, y + yy, fgcolor)
                elif bgcolor is not None:
                    self.tft.draw_pixel(x + xx, y + yy, bgcolor)

    def drawXBitmap(self, x, y, bitmap, w, h, fgcolor=None, bgcolor=None):
        # XBM is LSB first per byte.
        if fgcolor is None:
            fgcolor = self._bitmap_fg
        if bgcolor is None:
            bgcolor = None
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        mv = memoryview(bitmap)
        byte_width = (w + 7) // 8
        for yy in range(h):
            row = yy * byte_width
            for xx in range(w):
                b = mv[row + (xx >> 3)]
                if b & (1 << (xx & 7)):
                    self.tft.draw_pixel(x + xx, y + yy, fgcolor)
                elif bgcolor is not None:
                    self.tft.draw_pixel(x + xx, y + yy, bgcolor)

    # --- Images ---
    def pushImage(self, x, y, w, h, data, swapBytes=False):
        w = int(w)
        h = int(h)
        if w <= 0 or h <= 0:
            return
        mv = memoryview(data)
        need = 2 * w * h
        if len(mv) < need:
            raise ValueError("pushImage data too small")
        if swapBytes or self._swap_bytes:
            tmp = bytearray(mv[:need])
            _swap565_inplace(tmp)
            self.tft.blit_buffer(int(x) + self._origin_x, int(y) + self._origin_y, w, h, tmp)
        else:
            self.tft.blit_buffer(int(x) + self._origin_x, int(y) + self._origin_y, w, h, mv[:need])

    def pushRect(self, x, y, w, h, data):
        return self.pushImage(x, y, w, h, data, swapBytes=False)

    def readRect(self, x, y, w, h, data):
        # Hardware readback is typically unavailable in this MicroPython path.
        # Keep API shape by clearing destination buffer.
        need = int(w) * int(h) * 2
        mv = memoryview(data)
        for i in range(min(need, len(mv))):
            mv[i] = 0

    def readRectRGB(self, x, y, w, h, data):
        need = int(w) * int(h) * 3
        mv = memoryview(data)
        for i in range(min(need, len(mv))):
            mv[i] = 0

    # Aliases used in some ports
    def pushColors(self, data, len_or_count, swapBytes=False):
        # Write a raw sequence of colors to the current address window.
        count = int(len_or_count)
        mv = memoryview(data)
        need = 2 * count
        if len(mv) < need:
            raise ValueError("pushColors data too small")
        if swapBytes or self._swap_bytes:
            tmp = bytearray(mv[:need])
            _swap565_inplace(tmp)
            self.tft.push_pixels(tmp)
        else:
            self.tft.push_pixels(mv[:need])

    def pushColor(self, color, count=1):
        self.tft.push_color(int(color), int(count))

    def pushBlock(self, color, length):
        self.tft.push_color(int(color), int(length))

    def pushPixels(self, data, length=None):
        mv = memoryview(data)
        if length is None:
            self.tft.push_pixels(mv)
        else:
            self.tft.push_pixels(mv[: int(length) * 2])

    def setAttribute(self, id=0, a=0):
        self._attributes[int(id)] = int(a)

    def getAttribute(self, id=0):
        return int(self._attributes.get(int(id), 0))

    def color565(self, r, g, b):
        return self.tft.color(r, g, b)

    def color16to24(self, c):
        c = int(c) & 0xFFFF
        r = ((c >> 11) & 0x1F) << 3
        g = ((c >> 5) & 0x3F) << 2
        b = (c & 0x1F) << 3
        return (r << 16) | (g << 8) | b

    def color24to16(self, c):
        c = int(c) & 0xFFFFFF
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF
        return self.color565(r, g, b)

    def alphaBlend(self, alpha, fgc, bgc, dither=0):
        a = int(alpha)
        if a <= 0:
            return int(bgc) & 0xFFFF
        if a >= 255:
            return int(fgc) & 0xFFFF
        f = int(fgc) & 0xFFFF
        b = int(bgc) & 0xFFFF
        fr = (f >> 11) & 0x1F
        fg = (f >> 5) & 0x3F
        fb = f & 0x1F
        br = (b >> 11) & 0x1F
        bg = (b >> 5) & 0x3F
        bb = b & 0x1F
        r = (br * (255 - a) + fr * a) // 255
        g = (bg * (255 - a) + fg * a) // 255
        bl = (bb * (255 - a) + fb * a) // 255
        return (r << 11) | (g << 5) | bl

    # --- Pivot (used by rotated sprites upstream) ---
    def setPivot(self, x, y):
        self._pivot_x = int(x)
        self._pivot_y = int(y)

    def getPivotX(self):
        return int(self._pivot_x)

    def getPivotY(self):
        return int(self._pivot_y)

    # --- Sprites ---
    def createSprite(self, w, h):
        spr = TFT_eSprite(self.tft)
        spr.createSprite(w, h)
        return spr

    # --- Smooth graphics compatibility (fallbacks, non-antialiased) ---
    def drawSmoothArc(self, x, y, r, ir, startAngle, endAngle, fg_color, bg_color, roundEnds=False):
        thickness = max(1, int(r) - int(ir))
        self.drawArc(x, y, r, startAngle, endAngle, fg_color, thickness=thickness)

    def drawSmoothCircle(self, x, y, r, fg_color, bg_color):
        self.drawCircle(x, y, r, fg_color)

    def fillSmoothCircle(self, x, y, r, color, bg_color=0x00FFFFFF):
        self.fillCircle(x, y, r, color)

    def drawSmoothRoundRect(self, x, y, r, ir, w, h, fg_color, bg_color=0x00FFFFFF, quadrants=0xF):
        self.drawRoundRect(x, y, w, h, r, fg_color)

    def fillSmoothRoundRect(self, x, y, w, h, radius, color, bg_color=0x00FFFFFF):
        self.fillRoundRect(x, y, w, h, radius, color)

    def drawSpot(self, ax, ay, r, fg_color, bg_color=0x00FFFFFF):
        self.fillCircle(int(ax), int(ay), int(r), fg_color)

    def drawWideLine(self, ax, ay, bx, by, wd, fg_color, bg_color=0x00FFFFFF):
        self.drawLine(int(ax), int(ay), int(bx), int(by), fg_color)

    def drawWedgeLine(self, ax, ay, bx, by, aw, bw, fg_color, bg_color=0x00FFFFFF):
        self.drawLine(int(ax), int(ay), int(bx), int(by), fg_color)

