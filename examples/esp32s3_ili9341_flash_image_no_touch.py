from machine import SPI, Pin

from TFT_mSPI import SPIBus, TFT, ILI9341, TFT_eSPI

# Same ESP32-S3 pin config (no touch)
led = Pin(45, Pin.OUT)
led.value(1)

spi = SPI(
    1,
    baudrate=10_000_000,  # stability-first for noisy wiring
    polarity=0,
    phase=0,
    sck=Pin(21),
    mosi=Pin(47),
)

dc = Pin(2, Pin.OUT)
rst = Pin(1, Pin.OUT)
cs = Pin(14, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
# Tune these two flags for your module:
BGR_ORDER = True
INVERT_COLORS = True
panel = ILI9341(bus, bgr=BGR_ORDER, invert=INVERT_COLORS, init_variant=2)
tft = TFT_eSPI(TFT(panel, rotation=1))  # landscape: 320x240
tft.begin()

print("ILI9341 rotation=1 size:", tft.width(), "x", tft.height(), "bgr=", BGR_ORDER, "invert=", INVERT_COLORS)


# ILI9341 full-screen raw RGB565 image
# rotation=1 => 320x240
IMAGE_PATH = "/flash/image_320x240.rgb565"
IMG_W = 320
IMG_H = 240

# Convert JPG on desktop first:
# python tools/jpg_to_rgb565.py my.jpg image_320x240.rgb565 --width 320 --height 240


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
        draw_rgb565_from_flash(IMAGE_PATH)
    except Exception as exc:
        tft.fillScreen(0x0000)
        tft.drawRect(0, 0, tft.width(), tft.height(), 0xF800)
        print("ILI9341 image load failed:", exc)


main()

