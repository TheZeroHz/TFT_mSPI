from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, ST7735
from sysfont import sysfont

# ESP32 example pins (adjust to your wiring)
spi = SPI(
    2,
    baudrate=20_000_000,
    polarity=0,
    phase=0,
    sck=Pin(14),
    mosi=Pin(13),
    miso=Pin(12),
)

dc = Pin(16, Pin.OUT)
rst = Pin(17, Pin.OUT)
cs = Pin(18, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ST7735(bus, tab="red", bgr=False)
tft = TFT(panel, rotation=0)
tft.init()

tft.fill(tft.BLACK)
tft.text((0, 0), "TFT_mSPI", tft.YELLOW, sysfont, 2, nowrap=True)
tft.text((0, 20), "ST7735 demo", tft.CYAN, sysfont, 1, nowrap=True)

