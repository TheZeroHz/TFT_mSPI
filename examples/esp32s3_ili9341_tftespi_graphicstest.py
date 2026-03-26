from machine import SPI, Pin
import time

from TFT_mSPI import SPIBus, TFT, ILI9341, TFT_eSPI
from sysfont import sysfont

# Same current ESP32-S3 config
led = Pin(45, Pin.OUT)
led.value(1)
spi = SPI(1, baudrate=10_000_000, polarity=0, phase=0, sck=Pin(21), mosi=Pin(47))
dc = Pin(2, Pin.OUT)
rst = Pin(1, Pin.OUT)
cs = Pin(14, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ILI9341(bus, bgr=True, invert=True, init_variant=2)
tft = TFT_eSPI(TFT(panel, rotation=1))  # 320x240
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


def run_once():
    tft.fillScreen(BLACK)
    tft.setTextColor(WHITE, BLACK)
    tft.drawString("ILI9341 TFT_eSPI test", 4, 4)
    tft.drawFastHLine(0, 16, tft.width(), YELLOW)

    for i in range(0, tft.width(), 12):
        tft.drawLine(0, 17, i, tft.height() - 1, CYAN)
    for i in range(0, tft.height(), 12):
        tft.drawLine(0, 17, tft.width() - 1, i, MAGENTA)
    time.sleep_ms(500)

    tft.fillScreen(BLACK)
    for i in range(8, min(tft.width(), tft.height()), 14):
        x = (tft.width() - i) // 2
        y = (tft.height() - i) // 2
        tft.drawRoundRect(x, y, i, i, max(2, i // 10), GREEN)
    time.sleep_ms(500)

    tft.fillScreen(BLACK)
    for r in range(8, min(tft.width(), tft.height()) // 2, 12):
        tft.drawCircle(tft.width() // 2, tft.height() // 2, r, WHITE)
    time.sleep_ms(500)

    tft.fillScreen(BLACK)
    for i in range(10, min(tft.width(), tft.height()) // 2, 12):
        cx = tft.width() // 2
        cy = tft.height() // 2
        tft.fillTriangle(cx, cy - i, cx - i, cy + i, cx + i, cy + i, tft.color565(0, i & 0xFF, i & 0xFF))
    time.sleep_ms(500)

    tft.fillScreen(BLACK)
    tft.drawArc(tft.width() // 2, tft.height() // 2, 90, 160, 350, GREEN, thickness=10)
    tft.fillArc(tft.width() // 2, tft.height() // 2, 70, 160, 280, RED, thickness=18)
    tft.drawString("drawArc/fillArc", 92, tft.height() - 14)
    time.sleep_ms(900)


while True:
    run_once()

