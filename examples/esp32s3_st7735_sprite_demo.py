from machine import SPI, Pin
import time

from TFT_mSPI import SPIBus, TFT, ST7735, TFT_eSPI
from sysfont import sysfont

# Same pin config as esp32s3_st7735_pinout_example.py
led = Pin(45, Pin.OUT)
led.value(1)

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
YELLOW = 0xFFE0
MAGENTA = 0xF81F


def make_ship_sprite():
    spr = tft.createSprite(24, 16)
    spr.fillSprite(BLACK)  # transparent key
    spr.fillRect(2, 6, 20, 6, CYAN)     # hull
    spr.fillRect(8, 2, 8, 4, WHITE)     # cabin
    spr.drawLine(0, 15, 12, 0, YELLOW)  # mast left
    spr.drawLine(12, 0, 23, 15, YELLOW) # mast right
    spr.drawLine(0, 15, 23, 15, MAGENTA)
    return spr


def make_cloud_sprite():
    spr = tft.createSprite(40, 20)
    spr.fillSprite(BLACK)  # transparent key
    for i in range(8):
        spr.drawLine(2 + i, 10, 38 - i, 10, BLUE)
    spr.fillRect(8, 6, 24, 8, BLUE)
    spr.drawLine(8, 6, 32, 6, WHITE)
    spr.drawLine(8, 13, 32, 13, WHITE)
    return spr


def main():
    tft.fillScreen(BLACK)
    tft.setTextColor(WHITE, BLACK)
    tft.drawString("Sprite demo", 2, 2)
    tft.drawString("pushSprite + transparency", 2, 12)

    ship = make_ship_sprite()
    cloud = make_cloud_sprite()

    # Pre-draw a static background
    tft.drawRect(0, 24, tft.width(), tft.height() - 24, GREEN)
    for y in range(26, tft.height(), 8):
        tft.drawFastHLine(1, y, tft.width() - 2, tft.color565(0, min(255, y * 2), 80))

    x = 2
    dx = 2
    frame = 0
    while True:
        # Repaint only the animation band
        tft.fillRect(1, 40, tft.width() - 2, 80, BLACK)

        # Draw moving cloud and ship with transparent color key
        cx = (frame * 3) % (tft.width() + 40) - 40
        cloud.pushSprite(cx, 46, transparent=BLACK)
        ship.pushSprite(x, 78, transparent=BLACK)

        # Show a tiny HUD
        tft.setTextColor(YELLOW, BLACK)
        tft.drawString("x=%d" % x, 2, 28)

        # Bounce ship
        x += dx
        if x <= 0 or x >= tft.width() - 24:
            dx = -dx

        frame += 1
        time.sleep_ms(40)


main()

