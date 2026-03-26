from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, ST7789, XPT2046
from sysfont import sysfont

# Example wiring (adjust):
# Display on SPI2, touch on same or separate SPI. Many boards share SPI.

spi = SPI(
    2,
    baudrate=40_000_000,
    polarity=0,
    phase=0,
    sck=Pin(14),
    mosi=Pin(13),
    miso=Pin(12),
)

dc = Pin(16, Pin.OUT)
rst = Pin(17, Pin.OUT)
cs_tft = Pin(18, Pin.OUT)
cs_touch = Pin(21, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs_tft, rst=rst)
panel = ST7789(bus, width=240, height=320, bgr=True, invert=True)
tft = TFT(panel, rotation=1)
tft.init()

# Example calibration (replace with your own)
cal = (200, 3800, 200, 3800)  # xmin,xmax,ymin,ymax
touch = XPT2046(spi, cs_touch, cal=cal, width=tft.width, height=tft.height, z_threshold=350, samples=3, freq_hz=2_500_000)
tft.attach_touch(touch)

tft.fill(tft.BLACK)
tft.text((10, 10), "Touch demo", tft.WHITE, sysfont, 2, nowrap=True)

while True:
    p = tft.get_touch()
    if p:
        x, y, z = p
        tft.fill_circle(x, y, 2, tft.YELLOW)

