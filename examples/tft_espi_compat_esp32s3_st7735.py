from machine import SPI, Pin
import time

from TFT_mSPI import SPIBus, TFT, ST7735, TFT_eSPI
from sysfont import sysfont


# Backlight / LED enable (same as esp32s3_st7735_pinout_example.py)
led = Pin(45, Pin.OUT)
led.value(1)

# ESP32-S3 SPI pin config (EXACTLY matching esp32s3_st7735_pinout_example.py)
spi = SPI(
    1,
    baudrate=20_000_000,
    polarity=0,
    phase=0,
    sck=Pin(21),
    mosi=Pin(47),
)

dc = Pin(2, Pin.OUT)
rst = Pin(1, Pin.OUT)
cs = Pin(14, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ST7735(bus, tab="red", bgr=False)
tft = TFT_eSPI(TFT(panel, rotation=0))
tft.setTextFont(sysfont)
tft.begin()


BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
CYAN = 0x07FF
MAGENTA = 0xF81F
YELLOW = 0xFFE0


def micros():
    try:
        return time.ticks_us()
    except AttributeError:
        return time.ticks_ms() * 1000


def elapsed_us(start):
    try:
        return time.ticks_diff(micros(), start)
    except AttributeError:
        return micros() - start


def test_fill_screen():
    s = micros()
    for _ in range(4):
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
    tft.drawString("Hello World!", 0, 0)
    tft.setTextColor(RED, BLACK)
    tft.drawString("RED", 0, 10)
    tft.setTextColor(GREEN, BLACK)
    tft.drawString("GREEN", 28, 10)
    tft.setTextColor(BLUE, BLACK)
    tft.drawString("BLUE", 72, 10)
    tft.setTextColor(YELLOW, BLACK)
    tft.drawString("1234.56", 0, 20)
    tft.setTextColor(MAGENTA, BLACK)
    tft.drawString("Woot!", 0, 30)
    return elapsed_us(s)


def test_pixels():
    w = tft.width()
    h = tft.height()
    s = micros()
    for y in range(h):
        for x in range(w):
            tft.drawPixel(x, y, tft.color565((x << 3) & 0xFF, (y << 3) & 0xFF, (x * y) & 0xFF))
    return elapsed_us(s)


def test_lines(color):
    w = tft.width()
    h = tft.height()
    tft.fillScreen(BLACK)
    s = micros()
    for x in range(0, w, 6):
        tft.drawLine(0, 0, x, h - 1, color)
    for y in range(0, h, 6):
        tft.drawLine(0, 0, w - 1, y, color)
    t = elapsed_us(s)

    tft.fillScreen(BLACK)
    s = micros()
    for x in range(0, w, 6):
        tft.drawLine(w - 1, 0, x, h - 1, color)
    for y in range(0, h, 6):
        tft.drawLine(w - 1, 0, 0, y, color)
    t += elapsed_us(s)
    return t


def test_fast_lines(c1, c2):
    w = tft.width()
    h = tft.height()
    tft.fillScreen(BLACK)
    s = micros()
    for y in range(0, h, 5):
        tft.drawFastHLine(0, y, w, c1)
    for x in range(0, w, 5):
        tft.drawFastVLine(x, 0, h, c2)
    return elapsed_us(s)


def test_rects(color):
    tft.fillScreen(BLACK)
    w = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    s = micros()
    for i in range(2, w, 6):
        i2 = i // 2
        tft.drawRect(cx - i2, cy - i2, i, i, color)
    return elapsed_us(s)


def test_filled_rects(c1, c2):
    tft.fillScreen(BLACK)
    w = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    total = 0
    for i in range(w, 0, -6):
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
    r2 = radius * 2
    s = micros()
    for x in range(radius, w, r2):
        for y in range(radius, h, r2):
            tft.fillCircle(x, y, radius, color)
    return elapsed_us(s)


def test_circles(radius, color):
    w = tft.width() + radius
    h = tft.height() + radius
    r2 = radius * 2
    s = micros()
    for x in range(0, w, r2):
        for y in range(0, h, r2):
            tft.drawCircle(x, y, radius, color)
    return elapsed_us(s)


def test_triangles():
    tft.fillScreen(BLACK)
    cx = tft.width() // 2
    cy = tft.height() // 2
    n = min(cx, cy)
    s = micros()
    for i in range(0, n, 5):
        tft.drawTriangle(cx, cy - i, cx - i, cy + i, cx + i, cy + i, tft.color565(0, 0, i & 0xFF))
    return elapsed_us(s)


def test_filled_triangles():
    tft.fillScreen(BLACK)
    cx = tft.width() // 2
    cy = tft.height() // 2
    total = 0
    for i in range(min(cx, cy), 10, -5):
        s = micros()
        tft.fillTriangle(cx, cy - i, cx - i, cy + i, cx + i, cy + i, tft.color565(0, i & 0xFF, i & 0xFF))
        total += elapsed_us(s)
        tft.drawTriangle(cx, cy - i, cx - i, cy + i, cx + i, cy + i, tft.color565(i & 0xFF, i & 0xFF, 0))
    return total


def test_round_rects():
    tft.fillScreen(BLACK)
    w = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    s = micros()
    for i in range(0, w, 6):
        i2 = i // 2
        r = i // 8
        tft.drawRoundRect(cx - i2, cy - i2, i, i, r, tft.color565(i & 0xFF, 0, 0))
    return elapsed_us(s)


def test_filled_round_rects():
    tft.fillScreen(BLACK)
    w = min(tft.width(), tft.height())
    cx = tft.width() // 2
    cy = tft.height() // 2
    s = micros()
    for i in range(w, 20, -6):
        i2 = i // 2
        r = i // 8
        tft.fillRoundRect(cx - i2, cy - i2, i, i, r, tft.color565(0, i & 0xFF, 0))
    return elapsed_us(s)


def show_results(results):
    tft.fillScreen(BLACK)
    tft.setTextColor(MAGENTA, BLACK)
    tft.drawString("TFT_graphicstest_PDQ3", 0, 0)
    tft.setTextColor(WHITE, BLACK)
    y = 10
    for name, val in results:
        tft.drawString("%-12s %8d" % (name, val), 0, y)
        y += 10
        if y > 150:
            break


while True:
    print("Benchmark                Time (microseconds)")
    results = []
    for name, fn in (
        ("Fill", test_fill_screen),
        ("Text", test_text),
        ("Pixels", test_pixels),
        ("Lines", lambda: test_lines(BLUE)),
        ("HV Lines", lambda: test_fast_lines(RED, BLUE)),
        ("Rects", lambda: test_rects(GREEN)),
        ("RectsFill", lambda: test_filled_rects(YELLOW, MAGENTA)),
        ("CircFill", lambda: test_filled_circles(10, MAGENTA)),
        ("Circles", lambda: test_circles(10, WHITE)),
        ("Triangles", test_triangles),
        ("TriFill", test_filled_triangles),
        ("RndRects", test_round_rects),
        ("RndFill", test_filled_round_rects),
    ):
        us = fn()
        results.append((name, us))
        print("{:<24}{}".format(name, us))
        time.sleep_ms(80)

    show_results(results)
    print("Done!")
    time.sleep_ms(8000)

