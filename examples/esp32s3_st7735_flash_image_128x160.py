from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, ST7735, TFT_eSPI

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
tft.begin()


# Expected image format:
# - Raw RGB565 (16-bit), size = 128 * 160 * 2 bytes = 40960 bytes
# - Stored in flash filesystem (example path below)
#
# If you have a JPG, convert it on desktop first:
#   python tools/jpg_to_rgb565.py my_photo.jpg image_128x160.rgb565 --width 128 --height 160
# Then copy image_128x160.rgb565 to /flash on the device.
IMAGE_PATH = "/flash/image_128x160.rgb565"
IMG_W = 128
IMG_H = 160


def draw_rgb565_from_flash(path, x=0, y=0, w=IMG_W, h=IMG_H, swap_bytes=False):
    row_bytes = w * 2
    with open(path, "rb") as f:
        for row in range(h):
            buf = f.read(row_bytes)
            if len(buf) != row_bytes:
                raise ValueError("Image file too small or truncated")
            tft.pushImage(x, y + row, w, 1, buf, swapBytes=swap_bytes)


def main():
    tft.fillScreen(0x0000)
    try:
        draw_rgb565_from_flash(IMAGE_PATH, x=0, y=0, w=IMG_W, h=IMG_H, swap_bytes=False)
    except Exception as exc:
        # Simple on-screen error marker
        tft.fillScreen(0x0000)
        tft.drawRect(0, 0, tft.width(), tft.height(), 0xF800)
        print("Image load failed:", exc)


main()

