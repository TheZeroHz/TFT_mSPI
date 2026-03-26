from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, ST7735
from sysfont import sysfont

# Backlight / LED enable
led = Pin(45, Pin.OUT)
led.value(1)

# ── SPI + Display ─────────────────────────────────────────────────────────────
# ESP32-S3: SPI(1) with SCK=21, MOSI=47 (no MISO needed for write-only TFT)
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

# If your module has offsets, try: tab="green" or tab="blue"
panel = ST7735(bus, tab="red", bgr=False)
tft = TFT(panel, rotation=0)
tft.init()

# ── Quick sanity test ─────────────────────────────────────────────────────────
tft.fill(tft.BLACK)
tft.draw_rect(0, 0, tft.width, tft.height, tft.YELLOW)
tft.draw_line(0, 0, tft.width - 1, tft.height - 1, tft.CYAN)
tft.draw_line(0, tft.height - 1, tft.width - 1, 0, tft.MAGENTA)

tft.text((4, 4), "ESP32-S3", tft.WHITE, sysfont, 2, nowrap=True)
tft.text((4, 24), "ST7735", tft.GREEN, sysfont, 2, nowrap=True)
tft.text((4, 44), "TFT_mSPI", tft.YELLOW, sysfont, 2, nowrap=True)

