from machine import SPI, Pin
import time

from TFT_mSPI import SPIBus, TFT, ST7735, TFT_eSPI
from sysfont import sysfont

# Same current ESP32-S3 config
led = Pin(45, Pin.OUT)
led.value(1)
spi = SPI(1, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(21), mosi=Pin(47))
dc = Pin(2, Pin.OUT)
rst = Pin(1, Pin.OUT)
cs = Pin(14, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
tft = TFT_eSPI(TFT(ST7735(bus, tab="red", bgr=False), rotation=0))
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
    tft.drawString("ST7735 TFT_eSPI test", 2, 2)
    tft.drawFastHLine(0, 12, tft.width(), YELLOW)

    for i in range(0, tft.width(), 8):
        tft.drawLine(0, 13, i, tft.height() - 1, CYAN)
    for i in range(0, tft.height(), 8):
        tft.drawLine(0, 13, tft.width() - 1, i, MAGENTA)
    time.sleep_ms(700)

    tft.fillScreen(BLACK)
    for i in range(2, min(tft.width(), tft.height()), 8):
        x = (tft.width() - i) // 2
        y = (tft.height() - i) // 2
        tft.drawRect(x, y, i, i, GREEN)
    time.sleep_ms(700)

    tft.fillScreen(BLACK)
    for r in range(4, min(tft.width(), tft.height()) // 2, 6):
        tft.drawCircle(tft.width() // 2, tft.height() // 2, r, WHITE)
    time.sleep_ms(700)

    tft.fillScreen(BLACK)
    for i in range(6, min(tft.width(), tft.height()) // 2, 6):
        cx = tft.width() // 2
        cy = tft.height() // 2
        tft.drawTriangle(cx, cy - i, cx - i, cy + i, cx + i, cy + i, tft.color565(0, 0, i * 6))
    time.sleep_ms(700)

    tft.fillScreen(BLACK)
    tft.drawArc(tft.width() // 2, tft.height() // 2, 40, 200, 340, GREEN, thickness=4)
    tft.fillArc(tft.width() // 2, tft.height() // 2, 30, 200, 300, RED, thickness=6)
    tft.drawString("arc/fillArc", 16, tft.height() - 12)
    time.sleep_ms(900)


while True:
    run_once()

