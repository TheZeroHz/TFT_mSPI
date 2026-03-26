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
YELLOW = 0xFFE0


def show_datum(datum, label, x, y, color):
    tft.fillScreen(BLACK)
    tft.drawPixel(x, y, RED)
    tft.setTextColor(color, BLACK)
    tft.setTextDatum(datum)
    tft.drawString(label, x, y)
    tft.setTextColor(WHITE, BLACK)
    tft.setTextDatum(tft.TL_DATUM)
    tft.drawString("datum=%d" % datum, 2, tft.height() - 10)
    time.sleep_ms(900)


while True:
    w2 = tft.width() // 2
    h2 = tft.height() // 2
    show_datum(tft.TL_DATUM, "TL", 8, 8, YELLOW)
    show_datum(tft.TC_DATUM, "TC", w2, 8, GREEN)
    show_datum(tft.TR_DATUM, "TR", tft.width() - 8, 8, BLUE)
    show_datum(tft.MC_DATUM, "MC", w2, h2, YELLOW)
    show_datum(tft.BC_DATUM, "BC", w2, tft.height() - 8, GREEN)

