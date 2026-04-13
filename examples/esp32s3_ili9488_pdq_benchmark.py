from machine import SPI, Pin
import time

from TFT_mSPI import SPIBus, TFT, ILI9488, TFT_eSPI
from sysfont import sysfont

# ================= PINS =================
# Your wiring (ESP32-S3 style example):
# LED=16, SCK=15, MOSI=7, DC=6, RST=5, CS=4
led = Pin(16, Pin.OUT)
led.value(1)

spi = SPI(
    1,
    baudrate=40_000_000,  # safer start (you can try 60MHz later)
    polarity=0,
    phase=0,
    sck=Pin(15),
    mosi=Pin(7),
)

dc = Pin(6, Pin.OUT)
rst = Pin(5, Pin.OUT)
cs = Pin(4, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)

# ================= DISPLAY =================
# Tune these two flags for your module:
# - BGR_ORDER swaps red/blue channel order
# - INVERT_COLORS toggles panel inversion mode (often fixes "negative" looking colors)
#
# For many ILI9488 modules, keeping INVERT_COLORS=False is important.
BGR_ORDER = True
INVERT_COLORS = False

panel = ILI9488(bus, bgr=BGR_ORDER, invert=INVERT_COLORS)
tft = TFT_eSPI(TFT(panel, rotation=1))  # try 1 or 3 if rotated wrong
tft.setTextFont(sysfont)
tft.begin()

print(
    "ILI9488 rotation=%d size: %d x %d  bgr=%s invert=%s"
    % (tft.getRotation(), tft.width(), tft.height(), BGR_ORDER, INVERT_COLORS)
)

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
MAGENTA = 0xF81F
YELLOW = 0xFFE0


def micros():
    return time.ticks_us()


def elapsed_us(start):
    return time.ticks_diff(time.ticks_us(), start)


def test_fill_screen():
    s = micros()
    for _ in range(3):
        tft.fillScreen(WHITE)
        tft.fillScreen(RED)
        tft.fillScreen(GREEN)
        tft.fillScreen(BLUE)
        tft.fillScreen(BLACK)
    return elapsed_us(s)


def test_text():
    tft.fillScreen(BLACK)
    s = micros()
    tft.setTextColor(WHITE, BLACK)
    tft.drawString("ILI9488 PDQ benchmark", 0, 0)
    tft.setTextColor(YELLOW, BLACK)
    tft.drawString("Hello World!", 0, 12)
    tft.setTextColor(RED, BLACK)
    tft.drawString("RED", 0, 24)
    tft.setTextColor(GREEN, BLACK)
    tft.drawString("GREEN", 36, 24)
    tft.setTextColor(BLUE, BLACK)
    tft.drawString("BLUE", 92, 24)
    return elapsed_us(s)


def test_pixels(step=2):
    # Full 320x480 per-pixel writes can take a long time; step=2 is a good PDQ compromise.
    w = tft.width()
    h = tft.height()
    s = micros()
    for y in range(0, h, step):
        for x in range(0, w, step):
            tft.drawPixel(
                x,
                y,
                tft.color565((x << 3) & 0xFF, (y << 2) & 0xFF, (x * y) & 0xFF),
            )
    return elapsed_us(s)


def test_lines(color):
    w = tft.width()
    h = tft.height()
    tft.fillScreen(BLACK)
    s = micros()
    for x in range(0, w, 8):
        tft.drawLine(0, 0, x, h - 1, color)
    for y in range(0, h, 8):
        tft.drawLine(0, 0, w - 1, y, color)
    return elapsed_us(s)


def test_fast_lines(c1, c2):
    w = tft.width()
    h = tft.height()
    tft.fillScreen(BLACK)
    s = micros()
    for y in range(0, h, 6):
        tft.drawFastHLine(0, y, w, c1)
    for x in range(0, w, 6):
        tft.drawFastVLine(x, 0, h, c2)
    return elapsed_us(s)


def test_rects(color):
    tft.fillScreen(BLACK)
    n = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    s = micros()
    for i in range(2, n, 8):
        i2 = i // 2
        tft.drawRect(cx - i2, cy - i2, i, i, color)
    return elapsed_us(s)


def test_filled_rects(c1, c2):
    tft.fillScreen(BLACK)
    n = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    total = 0
    for i in range(n, 0, -10):
        i2 = i // 2
        s = micros()
        tft.fillRect(cx - i2, cy - i2, i, i, c1)
        total += elapsed_us(s)
        tft.drawRect(cx - i2, cy - i2, i, i, c2)
    return total


def test_filled_circles(radius, color):
    tft.fillScreen(BLACK)
    w = tft.width()
    h = tft.height()
    step = radius * 2
    s = micros()
    for x in range(radius, w, step):
        for y in range(radius, h, step):
            tft.fillCircle(x, y, radius, color)
    return elapsed_us(s)


def test_circles(radius, color):
    w = tft.width() + radius
    h = tft.height() + radius
    step = radius * 2
    s = micros()
    for x in range(0, w, step):
        for y in range(0, h, step):
            tft.drawCircle(x, y, radius, color)
    return elapsed_us(s)


def test_triangles():
    tft.fillScreen(BLACK)
    cx = tft.width() // 2
    cy = tft.height() // 2
    n = min(cx, cy)
    s = micros()
    for i in range(0, n, 8):
        tft.drawTriangle(
            cx,
            cy - i,
            cx - i,
            cy + i,
            cx + i,
            cy + i,
            tft.color565(0, 0, i & 0xFF),
        )
    return elapsed_us(s)


def test_filled_triangles():
    tft.fillScreen(BLACK)
    cx = tft.width() // 2
    cy = tft.height() // 2
    total = 0
    for i in range(min(cx, cy), 10, -10):
        s = micros()
        tft.fillTriangle(
            cx,
            cy - i,
            cx - i,
            cy + i,
            cx + i,
            cy + i,
            tft.color565(0, i & 0xFF, i & 0xFF),
        )
        total += elapsed_us(s)
        tft.drawTriangle(
            cx,
            cy - i,
            cx - i,
            cy + i,
            cx + i,
            cy + i,
            tft.color565(i & 0xFF, i & 0xFF, 0),
        )
    return total


def test_round_rects():
    tft.fillScreen(BLACK)
    n = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    s = micros()
    for i in range(0, n, 10):
        i2 = i // 2
        tft.drawRoundRect(cx - i2, cy - i2, i, i, i // 8, tft.color565(i & 0xFF, 0, 0))
    return elapsed_us(s)


def test_filled_round_rects():
    tft.fillScreen(BLACK)
    n = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    s = micros()
    for i in range(n, 30, -10):
        i2 = i // 2
        tft.fillRoundRect(cx - i2, cy - i2, i, i, i // 8, tft.color565(0, i & 0xFF, 0))
    return elapsed_us(s)


def show_results(results):
    tft.fillScreen(BLACK)
    tft.setTextColor(MAGENTA, BLACK)
    tft.drawString("ILI9488 PDQ Benchmark", 0, 0)
    tft.setTextColor(WHITE, BLACK)
    y = 14
    for name, val in results:
        tft.drawString("%-12s %10d" % (name, val), 0, y)
        y += 12
        if y > (tft.height() - 10):
            break


while True:
    print("Benchmark                Time (microseconds)")
    results = []
    tests = (
        ("Fill", test_fill_screen),
        ("Text", test_text),
        ("Pixels2", lambda: test_pixels(step=2)),
        ("Lines", lambda: test_lines(BLUE)),
        ("HV Lines", lambda: test_fast_lines(RED, BLUE)),
        ("Rects", lambda: test_rects(GREEN)),
        ("RectsFill", lambda: test_filled_rects(YELLOW, MAGENTA)),
        ("CircFill", lambda: test_filled_circles(12, MAGENTA)),
        ("Circles", lambda: test_circles(12, WHITE)),
        ("Triangles", test_triangles),
        ("TriFill", test_filled_triangles),
        ("RndRects", test_round_rects),
        ("RndFill", test_filled_round_rects),
    )

    for name, fn in tests:
        us = fn()
        results.append((name, us))
        print("{:<24}{}".format(name, us))
        time.sleep_ms(80)

    show_results(results)
    print("Done!")
    time.sleep_ms(8000)

