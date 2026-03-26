from machine import SPI, Pin
import time
import gc

from TFT_mSPI import SPIBus, TFT, ST7735, TFT_eSPI

import camera

# -------------------- Same current ESP32-S3 config (ST7735) --------------------
led = Pin(45, Pin.OUT)
led.value(1)

spi = SPI(1, baudrate=20_000_000, polarity=0, phase=0, sck=Pin(21), mosi=Pin(47))
dc = Pin(2, Pin.OUT)
rst = Pin(1, Pin.OUT)
cs = Pin(14, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ST7735(bus, tab="red", bgr=False)
tft = TFT_eSPI(TFT(panel, rotation=0))
tft.begin()

# BOOT button is commonly GPIO0 on ESP32-S3 boards
BOOT_PIN = 0
boot = Pin(BOOT_PIN, Pin.IN, Pin.PULL_UP)

# -------------------- Camera init (same pins as picoweb_video.py) --------------------
def camera_init_rgb565_qvga():
    try:
        camera.deinit()
    except Exception:
        pass

    camera.init(
        0,
        d0=11,
        d1=9,
        d2=8,
        d3=10,
        d4=12,
        d5=18,
        d6=17,
        d7=16,
        format=camera.RGB565,
        framesize=camera.FRAME_QVGA,  # 320x240
        xclk_freq=camera.XCLK_10MHz,
        href=7,
        vsync=6,
        reset=-1,
        pwdn=-1,
        sioc=5,
        siod=4,
        xclk=15,
        pclk=13,
        fb_location=camera.PSRAM,
    )


# -------------------- Crop settings: QVGA -> ST7735 (128x160) --------------------
SRC_W = 320
SRC_H = 240
DST_W = 128
DST_H = 160

X0 = (SRC_W - DST_W) // 2  # 96
Y0 = (SRC_H - DST_H) // 2  # 40

# If colors look wrong, flip this.
SWAP_CAMERA_BYTES = False


def push_cropped_frame_to_st7735(frame):
    mv = memoryview(frame)
    for dy in range(DST_H):
        sy = Y0 + dy
        start = 2 * (sy * SRC_W + X0)
        end = start + DST_W * 2
        tft.pushImage(0, dy, DST_W, 1, mv[start:end], swapBytes=SWAP_CAMERA_BYTES)


def save_cropped_rgb565_to_flash(frame, path):
    mv = memoryview(frame)
    with open(path, "wb") as f:
        for dy in range(DST_H):
            sy = Y0 + dy
            start = 2 * (sy * SRC_W + X0)
            end = start + DST_W * 2
            f.write(mv[start:end])


def main():
    tft.fillScreen(0x0000)
    camera_init_rgb565_qvga()

    # Simple debounce state
    last_state = boot.value()
    last_save_ms = time.ticks_ms()

    while True:
        frame = camera.capture()
        if isinstance(frame, tuple):
            frame = frame[0]

        if len(frame) != SRC_W * SRC_H * 2:
            print("Bad camera frame size:", len(frame))
            del frame
            gc.collect()
            time.sleep_ms(200)
            continue

        push_cropped_frame_to_st7735(frame)

        # BOOT press to save (active-low)
        st = boot.value()
        if last_state == 1 and st == 0:
            now = time.ticks_ms()
            # basic debounce / rate limit
            if time.ticks_diff(now, last_save_ms) > 800:
                last_save_ms = now
                fn = "/flash/cap_%d.rgb565" % (now // 1000)
                print("Saving", fn)
                try:
                    save_cropped_rgb565_to_flash(frame, fn)
                    # quick visual cue: white border flash
                    tft.drawRect(0, 0, DST_W, DST_H, 0xFFFF)
                except Exception as exc:
                    print("Save failed:", exc)

        last_state = st

        del frame
        gc.collect()


main()

