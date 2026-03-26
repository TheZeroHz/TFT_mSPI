from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, ILI9341
from sysfont import sysfont

spi = SPI(2, baudrate=40_000_000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
dc = Pin(16, Pin.OUT)
rst = Pin(17, Pin.OUT)
cs = Pin(18, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ILI9341(bus, bgr=True)
tft = TFT(panel, rotation=1)
tft.init()

tft.fill(tft.BLACK)
tft.text((10, 10), "ILI9341", tft.WHITE, sysfont, 2, nowrap=True)
tft.draw_line(0, 0, tft.width - 1, tft.height - 1, tft.CYAN)

