try:
    import time
except ImportError:  # pragma: no cover
    time = None

import math

from .colors import color565


class TFT:
    """
    High-level TFT display wrapper with a TFT_eSPI-like surface.

    This class delegates controller-specific init and rotation to `panel`.
    """

    # Common commands (shared by many controllers)
    CASET = 0x2A
    RASET = 0x2B
    RAMWR = 0x2C
    MADCTL = 0x36
    COLMOD = 0x3A
    SLPOUT = 0x11
    SLPIN = 0x10
    DISPON = 0x29
    DISPOFF = 0x28
    INVON = 0x21
    INVOFF = 0x20

    def __init__(self, panel, *, rotation=0):
        self.panel = panel
        self.bus = panel.bus
        self._rotation = int(rotation) & 3

        self._width = int(panel.width)
        self._height = int(panel.height)
        self._x_offset = int(getattr(panel, "x_offset", 0))
        self._y_offset = int(getattr(panel, "y_offset", 0))

        # cached for fill operations
        self._color_buf = bytearray(2)
        self._fill_block = None
        self._pixel_format = int(getattr(panel, "pixel_format", 16))

        # common color constants (RGB565)
        self.BLACK = 0x0000
        self.WHITE = 0xFFFF
        self.RED = color565(255, 0, 0)
        self.GREEN = color565(0, 255, 0)
        self.BLUE = color565(0, 0, 255)
        self.CYAN = color565(0, 255, 255)
        self.MAGENTA = color565(255, 0, 255)
        self.YELLOW = color565(255, 255, 0)
        self.GRAY = color565(128, 128, 128)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def size(self):
        return (self._width, self._height)

    def init(self):
        self.panel.hardware_reset()
        self.panel.init()
        self.set_rotation(self._rotation)
        self.on(True)
        if getattr(self, "touch", None) is not None:
            try:
                self.touch.set_rotation(self._rotation)
            except Exception:
                pass

    def on(self, enable=True):
        self.bus.write_cmd(self.DISPON if enable else self.DISPOFF)

    def sleep(self, enable=True):
        self.bus.write_cmd(self.SLPIN if enable else self.SLPOUT)
        if time is not None:
            time.sleep_ms(120)

    def invert(self, enable=True):
        self.bus.write_cmd(self.INVON if enable else self.INVOFF)

    def set_rotation(self, rotation):
        self._rotation = int(rotation) & 3
        # update width/height swap for odd rotations
        if self._rotation & 1:
            self._width, self._height = int(self.panel.height), int(self.panel.width)
        else:
            self._width, self._height = int(self.panel.width), int(self.panel.height)
        self.panel.set_rotation(self, self._rotation)
        if getattr(self, "touch", None) is not None:
            try:
                self.touch.set_rotation(self._rotation)
            except Exception:
                pass

    def attach_touch(self, touch):
        self.touch = touch
        try:
            self.touch.set_rotation(self._rotation)
        except Exception:
            pass

    def get_touch(self):
        """
        Return a touch point in display coordinates: (x, y, z) or None.

        Requires `tft.attach_touch(...)` or `tft.touch = ...` first.
        """
        touch = getattr(self, "touch", None)
        if touch is None:
            return None
        p = touch.get_point()
        if p is None:
            return None
        x, y, z = p
        try:
            x, y = touch.transform(int(x), int(y), self._width, self._height, self._rotation)
        except Exception:
            x, y = int(x), int(y)
        return x, y, z

    def color(self, r, g, b):
        return color565(r, g, b)

    # --- Low-level pixel pushing ---
    def _set_addr_window(self, x0, y0, x1, y1):
        x0 = int(x0) + self._x_offset
        x1 = int(x1) + self._x_offset
        y0 = int(y0) + self._y_offset
        y1 = int(y1) + self._y_offset

        self.bus.write_cmd(self.CASET)
        self.bus.write_data(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self.bus.write_cmd(self.RASET)
        self.bus.write_data(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self.bus.write_cmd(self.RAMWR)

    def push_pixels(self, buf):
        if self._pixel_format == 16:
            self.bus.write_data(buf)
            return

        # RGB565 -> RGB666 over SPI (3 bytes per pixel)
        mv = memoryview(buf)
        in_step = 512  # bytes (256 px)
        out = bytearray((in_step // 2) * 3)
        for i in range(0, len(mv), in_step):
            chunk = mv[i : i + in_step]
            op = 0
            for j in range(0, len(chunk), 2):
                c = (chunk[j] << 8) | chunk[j + 1]
                r = c & 0xF800
                g = c & 0x07E0
                b = c & 0x001F
                out[op] = r >> 8
                out[op + 1] = g >> 3
                out[op + 2] = b << 3
                op += 3
            self.bus.write_data(memoryview(out)[:op])

    def _set_fill_color(self, color):
        c = int(color) & 0xFFFF
        self._color_buf[0] = (c >> 8) & 0xFF
        self._color_buf[1] = c & 0xFF
        self._fill_block = bytes(self._color_buf) * 64

    def push_color(self, color, count):
        count = int(count)
        if count <= 0:
            return
        if self._pixel_format == 16:
            self._set_fill_color(color)
            block = self._fill_block
            full = count // 64
            rest = count % 64
            self.bus.dc(1)
            if self.bus.cs is not None:
                self.bus.cs(0)
            for _ in range(full):
                self.bus.spi.write(block)
            if rest:
                self.bus.spi.write(bytes(self._color_buf) * rest)
            if self.bus.cs is not None:
                self.bus.cs(1)
            return

        # 18-bit write: expand one RGB565 color to RGB666 (3 bytes)
        c = int(color) & 0xFFFF
        r = (c & 0xF800) >> 8
        g = (c & 0x07E0) >> 3
        b = (c & 0x001F) << 3
        pix = bytes([r & 0xFF, g & 0xFF, b & 0xFF])
        block = pix * 64
        full = count // 64
        rest = count % 64
        self.bus.dc(1)
        if self.bus.cs is not None:
            self.bus.cs(0)
        for _ in range(full):
            self.bus.spi.write(block)
        if rest:
            self.bus.spi.write(pix * rest)
        if self.bus.cs is not None:
            self.bus.cs(1)

    # --- Drawing primitives ---
    def fill_screen(self, color):
        self.fill_rect(0, 0, self._width, self._height, color)

    # Legacy-friendly aliases
    def fill(self, color=0):
        self.fill_screen(color)

    def pixel(self, pos, color):
        self.draw_pixel(pos[0], pos[1], color)

    def rect(self, pos, size, color):
        self.draw_rect(pos[0], pos[1], size[0], size[1], color)

    def fillrect(self, pos, size, color):
        self.fill_rect(pos[0], pos[1], size[0], size[1], color)

    def draw_pixel(self, x, y, color):
        x = int(x)
        y = int(y)
        if x < 0 or y < 0 or x >= self._width or y >= self._height:
            return
        self._set_addr_window(x, y, x, y)
        c = int(color) & 0xFFFF
        self.bus.write_data(bytearray([c >> 8, c & 0xFF]))

    def line(self, start, end, color):
        self.draw_line(start[0], start[1], end[0], end[1], color)

    def draw_line(self, x0, y0, x1, y1, color):
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)

        if x0 == x1:
            if y1 < y0:
                y0, y1 = y1, y0
            self.vline(x0, y0, y1 - y0 + 1, color)
            return
        if y0 == y1:
            if x1 < x0:
                x0, x1 = x1, x0
            self.hline(x0, y0, x1 - x0 + 1, color)
            return

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            self.draw_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = err << 1
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def fill_rect(self, x, y, w, h, color):
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        if w <= 0 or h <= 0:
            return

        x1 = x + w - 1
        y1 = y + h - 1

        if x1 < 0 or y1 < 0 or x >= self._width or y >= self._height:
            return

        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x1 >= self._width:
            x1 = self._width - 1
        if y1 >= self._height:
            y1 = self._height - 1

        self._set_addr_window(x, y, x1, y1)
        self.push_color(color, (x1 - x + 1) * (y1 - y + 1))

    def draw_rect(self, x, y, w, h, color):
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def draw_triangle(self, x1, y1, x2, y2, x3, y3, color):
        self.draw_line(x1, y1, x2, y2, color)
        self.draw_line(x2, y2, x3, y3, color)
        self.draw_line(x3, y3, x1, y1, color)

    def fill_triangle(self, x1, y1, x2, y2, x3, y3, color):
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)
        x3 = int(x3)
        y3 = int(y3)

        # Sort by y
        if y2 < y1:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        if y3 < y1:
            x1, x3 = x3, x1
            y1, y3 = y3, y1
        if y3 < y2:
            x2, x3 = x3, x2
            y2, y3 = y3, y2

        if y1 == y3:
            # All on one line
            xa = min(x1, x2, x3)
            xb = max(x1, x2, x3)
            self.hline(xa, y1, xb - xa + 1, color)
            return

        def _interp_x(y, x0, y0, x1_, y1_):
            if y1_ == y0:
                return x0
            return x0 + (x1_ - x0) * (y - y0) / (y1_ - y0)

        y = y1
        # Upper part y1..y2
        if y2 > y1:
            for y in range(y1, y2 + 1):
                xa = _interp_x(y, x1, y1, x3, y3)
                xb = _interp_x(y, x1, y1, x2, y2)
                if xa > xb:
                    xa, xb = xb, xa
                xa = int(round(xa))
                xb = int(round(xb))
                self.hline(xa, y, xb - xa + 1, color)

        # Lower part y2..y3
        if y3 > y2:
            for y in range(y2, y3 + 1):
                xa = _interp_x(y, x1, y1, x3, y3)
                xb = _interp_x(y, x2, y2, x3, y3)
                if xa > xb:
                    xa, xb = xb, xa
                xa = int(round(xa))
                xb = int(round(xb))
                self.hline(xa, y, xb - xa + 1, color)

    def draw_round_rect(self, x, y, w, h, radius, color):
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        r = int(radius)
        if w <= 0 or h <= 0:
            return
        if r <= 0:
            self.draw_rect(x, y, w, h, color)
            return
        r = min(r, w // 2, h // 2)

        self.hline(x + r, y, w - 2 * r, color)
        self.hline(x + r, y + h - 1, w - 2 * r, color)
        self.vline(x, y + r, h - 2 * r, color)
        self.vline(x + w - 1, y + r, h - 2 * r, color)

        # Corner arcs (quarter circles)
        for dy in range(r + 1):
            dx = int(round(math.sqrt(max(0, r * r - dy * dy))))
            # top-left
            self.draw_pixel(x + r - dx, y + r - dy, color)
            self.draw_pixel(x + r - dy, y + r - dx, color)
            # top-right
            self.draw_pixel(x + w - r - 1 + dx, y + r - dy, color)
            self.draw_pixel(x + w - r - 1 + dy, y + r - dx, color)
            # bottom-left
            self.draw_pixel(x + r - dx, y + h - r - 1 + dy, color)
            self.draw_pixel(x + r - dy, y + h - r - 1 + dx, color)
            # bottom-right
            self.draw_pixel(x + w - r - 1 + dx, y + h - r - 1 + dy, color)
            self.draw_pixel(x + w - r - 1 + dy, y + h - r - 1 + dx, color)

    def fill_round_rect(self, x, y, w, h, radius, color):
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        r = int(radius)
        if w <= 0 or h <= 0:
            return
        if r <= 0:
            self.fill_rect(x, y, w, h, color)
            return
        r = min(r, w // 2, h // 2)

        # Center rectangle
        self.fill_rect(x + r, y, w - 2 * r, h, color)
        # Side rectangles
        self.fill_rect(x, y + r, r, h - 2 * r, color)
        self.fill_rect(x + w - r, y + r, r, h - 2 * r, color)

        # Fill corner quarter-circles
        for dy in range(r + 1):
            dx = int(round(math.sqrt(max(0, r * r - dy * dy))))
            # top
            self.hline(x + r - dx, y + r - dy, 2 * dx + (w - 2 * r), color)
            # bottom
            self.hline(x + r - dx, y + h - r - 1 + dy, 2 * dx + (w - 2 * r), color)

    def draw_ellipse(self, x, y, rx, ry, color):
        x0 = int(x)
        y0 = int(y)
        rx = int(rx)
        ry = int(ry)
        if rx <= 0 or ry <= 0:
            return

        # Midpoint ellipse (integer)
        rx2 = rx * rx
        ry2 = ry * ry
        two_rx2 = 2 * rx2
        two_ry2 = 2 * ry2
        px = 0
        py = two_rx2 * ry

        x1 = 0
        y1 = ry
        # Region 1
        p = int(round(ry2 - rx2 * ry + 0.25 * rx2))
        while px < py:
            self.draw_pixel(x0 + x1, y0 + y1, color)
            self.draw_pixel(x0 - x1, y0 + y1, color)
            self.draw_pixel(x0 + x1, y0 - y1, color)
            self.draw_pixel(x0 - x1, y0 - y1, color)
            x1 += 1
            px += two_ry2
            if p < 0:
                p += ry2 + px
            else:
                y1 -= 1
                py -= two_rx2
                p += ry2 + px - py

        # Region 2
        p = int(round(ry2 * (x1 + 0.5) * (x1 + 0.5) + rx2 * (y1 - 1) * (y1 - 1) - rx2 * ry2))
        while y1 >= 0:
            self.draw_pixel(x0 + x1, y0 + y1, color)
            self.draw_pixel(x0 - x1, y0 + y1, color)
            self.draw_pixel(x0 + x1, y0 - y1, color)
            self.draw_pixel(x0 - x1, y0 - y1, color)
            y1 -= 1
            py -= two_rx2
            if p > 0:
                p += rx2 - py
            else:
                x1 += 1
                px += two_ry2
                p += rx2 - py + px

    def fill_ellipse(self, x, y, rx, ry, color):
        x0 = int(x)
        y0 = int(y)
        rx = int(rx)
        ry = int(ry)
        if rx <= 0 or ry <= 0:
            return

        # Fill by horizontal spans
        for dy in range(-ry, ry + 1):
            yy = y0 + dy
            # x extent from ellipse equation: (x^2/rx^2) + (y^2/ry^2)=1
            t = 1.0 - (dy * dy) / float(ry * ry)
            if t <= 0:
                continue
            dx = int(round(rx * math.sqrt(t)))
            self.hline(x0 - dx, yy, 2 * dx + 1, color)

    def circle(self, pos, radius, color):
        self.draw_circle(pos[0], pos[1], radius, color)

    def draw_circle(self, x0, y0, r, color):
        x0 = int(x0)
        y0 = int(y0)
        r = int(r)
        if r <= 0:
            return
        f = 1 - r
        ddx = 1
        ddy = -2 * r
        x = 0
        y = r

        self.draw_pixel(x0, y0 + r, color)
        self.draw_pixel(x0, y0 - r, color)
        self.draw_pixel(x0 + r, y0, color)
        self.draw_pixel(x0 - r, y0, color)

        while x < y:
            if f >= 0:
                y -= 1
                ddy += 2
                f += ddy
            x += 1
            ddx += 2
            f += ddx

            self.draw_pixel(x0 + x, y0 + y, color)
            self.draw_pixel(x0 - x, y0 + y, color)
            self.draw_pixel(x0 + x, y0 - y, color)
            self.draw_pixel(x0 - x, y0 - y, color)
            self.draw_pixel(x0 + y, y0 + x, color)
            self.draw_pixel(x0 - y, y0 + x, color)
            self.draw_pixel(x0 + y, y0 - x, color)
            self.draw_pixel(x0 - y, y0 - x, color)

    def fillcircle(self, pos, radius, color):
        self.fill_circle(pos[0], pos[1], radius, color)

    def fill_circle(self, x0, y0, r, color):
        x0 = int(x0)
        y0 = int(y0)
        r = int(r)
        if r <= 0:
            return
        self.vline(x0, y0 - r, 2 * r + 1, color)
        f = 1 - r
        ddx = 1
        ddy = -2 * r
        x = 0
        y = r

        while x < y:
            if f >= 0:
                y -= 1
                ddy += 2
                f += ddy
            x += 1
            ddx += 2
            f += ddx
            self.vline(x0 + x, y0 - y, 2 * y + 1, color)
            self.vline(x0 - x, y0 - y, 2 * y + 1, color)
            self.vline(x0 + y, y0 - x, 2 * x + 1, color)
            self.vline(x0 - y, y0 - x, 2 * x + 1, color)

    def text(self, pos, string, color, font, size=1, nowrap=False):
        if font is None:
            return
        if isinstance(size, (int, float)):
            sx = int(size)
            sy = int(size)
        else:
            sx = int(size[0])
            sy = int(size[1])
        x, y = int(pos[0]), int(pos[1])
        cw = font["Width"] * sx + 1
        for ch in string:
            self.char((x, y), ch, color, font, (sx, sy))
            x += cw
            if x + cw > self._width:
                if nowrap:
                    break
                x = int(pos[0])
                y += font["Height"] * sy + 1

    def char(self, pos, ch, color, font, sizes=(1, 1)):
        if font is None:
            return
        sx = int(sizes[0])
        sy = int(sizes[1])
        ci = ord(ch)
        start = int(font["Start"])
        end = int(font["End"])
        if ci < start or ci > end:
            return
        fw = int(font["Width"])
        fh = int(font["Height"])
        idx = (ci - start) * fw
        data = font["Data"][idx : idx + fw]
        x0, y0 = int(pos[0]), int(pos[1])

        if sx == 1 and sy == 1:
            buf = bytearray(2 * fw * fh)
            c_hi = (int(color) >> 8) & 0xFF
            c_lo = int(color) & 0xFF
            for col in range(fw):
                bits = data[col]
                for row in range(fh):
                    if bits & 0x01:
                        p = 2 * (row * fw + col)
                        buf[p] = c_hi
                        buf[p + 1] = c_lo
                    bits >>= 1
            self.blit_buffer(x0, y0, fw, fh, buf)
            return

        x = x0
        for col in range(fw):
            bits = data[col]
            y = y0
            for row in range(fh):
                if bits & 0x01:
                    self.fill_rect(x, y, sx, sy, color)
                bits >>= 1
                y += sy
            x += sx

    def blit_buffer(self, x, y, w, h, buf):
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        if w <= 0 or h <= 0:
            return
        self._set_addr_window(x, y, x + w - 1, y + h - 1)
        self.push_pixels(buf)

    # --- Arcs (approximate with line segments) ---
    def draw_arc(self, x, y, r, start, end, color, thickness=1):
        """
        Draw an arc centered at (x,y) with radius r.

        Angles are in degrees, where 0° is to the right and increases CCW.
        """
        x = int(x)
        y = int(y)
        r = int(r)
        if r <= 0:
            return
        thickness = int(thickness)
        if thickness <= 0:
            thickness = 1

        a0 = float(start)
        a1 = float(end)
        if a1 < a0:
            a0, a1 = a1, a0
        span = a1 - a0
        if span <= 0:
            return

        # Step: ~1px along circumference, clamped to [1°, 12°]
        step = 360.0 / (2.0 * math.pi * r)
        step = max(1.0, min(12.0, step * 57.29577951308232))  # rad->deg factor

        # Outer/inner radii for thickness
        r_outer = r
        r_inner = max(0, r - thickness + 1)

        a = a0
        prev_outer = None
        prev_inner = None
        while a <= a1 + 1e-6:
            rad = a * (math.pi / 180.0)
            ca = math.cos(rad)
            sa = math.sin(rad)
            xo = x + int(round(r_outer * ca))
            yo = y + int(round(r_outer * sa))
            xi = x + int(round(r_inner * ca))
            yi = y + int(round(r_inner * sa))

            if prev_outer is not None:
                self.draw_line(prev_outer[0], prev_outer[1], xo, yo, color)
                if r_inner != r_outer:
                    self.draw_line(prev_inner[0], prev_inner[1], xi, yi, color)
                    # connect inner/outer edges for thick arc appearance
                    self.draw_line(prev_inner[0], prev_inner[1], prev_outer[0], prev_outer[1], color)
                    self.draw_line(xi, yi, xo, yo, color)
            prev_outer = (xo, yo)
            prev_inner = (xi, yi)
            a += step

    def fill_arc(self, x, y, r, start, end, color, thickness=None):
        """
        Fill an arc band. If thickness is None, fills a sector (pie slice).
        """
        x = int(x)
        y = int(y)
        r = int(r)
        if r <= 0:
            return

        a0 = float(start)
        a1 = float(end)
        if a1 < a0:
            a0, a1 = a1, a0
        span = a1 - a0
        if span <= 0:
            return

        if thickness is None:
            r_inner = 0
        else:
            thickness = int(thickness)
            if thickness <= 0:
                return
            r_inner = max(0, r - thickness + 1)

        # Step: ~1px along circumference, clamped to [1°, 8°]
        step = 360.0 / (2.0 * math.pi * r)
        step = max(1.0, min(8.0, step * 57.29577951308232))

        a = a0
        while a <= a1 + 1e-6:
            rad = a * (math.pi / 180.0)
            ca = math.cos(rad)
            sa = math.sin(rad)
            xo = x + int(round(r * ca))
            yo = y + int(round(r * sa))
            xi = x + int(round(r_inner * ca))
            yi = y + int(round(r_inner * sa))
            self.draw_line(xi, yi, xo, yo, color)
            a += step

