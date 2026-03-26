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


def make_tft(bgr, invert):
    bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
    panel = ILI9341(bus, bgr=bgr, invert=invert, init_variant=2)
    dev = TFT_eSPI(TFT(panel, rotation=1))
    dev.setTextFont(sysfont)
    dev.begin()
    return dev


def paint_test(dev, bgr, invert):
    dev.fillScreen(0x0000)
    dev.fillRect(0, 0, dev.width() // 3, 80, 0xF800)          # red bar
    dev.fillRect(dev.width() // 3, 0, dev.width() // 3, 80, 0x07E0)  # green bar
    dev.fillRect((dev.width() * 2) // 3, 0, dev.width() // 3, 80, 0x001F)  # blue bar
    dev.setTextColor(0xFFFF, 0x0000)
    dev.drawString("bgr=%s invert=%s" % (bgr, invert), 4, 92)
    dev.drawString("R/G/B bars should look true", 4, 104)
    dev.drawString("switch after 2 sec", 4, 116)


for bgr in (True, False):
    for invert in (False, True):
        tft = make_tft(bgr, invert)
        paint_test(tft, bgr, invert)
        print("Testing bgr=%s invert=%s" % (bgr, invert))
        time.sleep_ms(2000)

# Keep final setting visible (typical good default)
tft = make_tft(True, True)
paint_test(tft, True, True)

