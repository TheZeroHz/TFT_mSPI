from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, GC9A01
from sysfont import sysfont

spi = SPI(2, baudrate=40_000_000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
dc = Pin(16, Pin.OUT)
rst = Pin(17, Pin.OUT)
cs = Pin(18, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = GC9A01(bus, bgr=True)
tft = TFT(panel, rotation=0)
tft.init()

tft.fill(tft.BLACK)
tft.text((60, 110), "GC9A01", tft.YELLOW, sysfont, 2, nowrap=True)
tft.draw_circle(120, 120, 100, tft.CYAN)

