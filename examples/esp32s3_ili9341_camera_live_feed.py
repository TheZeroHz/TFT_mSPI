from machine import SPI, Pin
import time
import gc

from TFT_mSPI import SPIBus, TFT, ILI9341, TFT_eSPI

import camera


# -------------------- Same display wiring (no touch) --------------------
led = Pin(45, Pin.OUT)
led.value(1)

spi = SPI(
    1,
    baudrate=10_000_000,
    polarity=0,
    phase=0,
    sck=Pin(21),
    mosi=Pin(47),
)

dc = Pin(2, Pin.OUT)
rst = Pin(1, Pin.OUT)
cs = Pin(14, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ILI9341(bus, bgr=True, invert=True, init_variant=2)
tft = TFT_eSPI(TFT(panel, rotation=1))  # 320x240
tft.begin()


# -------------------- Camera/display format knobs --------------------
# If colors look swapped or very wrong, flip SWAP_CAMERA_BYTES.
SWAP_CAMERA_BYTES = False

# QVGA => 320x240 (matches ILI9341 landscape in this example)
CAM_W = 320
CAM_H = 240


def camera_init_rgb565_qvga():
    """
    Use the same OV2640 pin mapping style as `EPSS3CAMERA/picoweb_video.py`.
    """
    # Stop any previous camera instance
    try:
        camera.deinit()
    except Exception:
        pass

    # Pin mapping (from picoweb_video.py)
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
        framesize=camera.FRAME_QVGA,
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


def main():
    tft.fillScreen(0x0000)

    camera_init_rgb565_qvga()

    # Warm-up capture (some builds need one to start streaming)
    try:
        frame = camera.capture()
        # Drop to allow GC
        del frame
    except Exception:
        # If RGB565 init failed at runtime, show error and stop.
        tft.fillScreen(0x0000)
        tft.drawRect(0, 0, CAM_W, CAM_H, 0xF800)
        print("Camera RGB565 capture failed. Check firmware/support.")
        raise

    frame_count = 0
    last = time.ticks_ms()

    while True:
        frame = camera.capture()

        # Stream full frame to the TFT origin.
        # RGB565 output must be 320*240*2 bytes.
        # Our TFT pushImage assumes 16-bit RGB565 big-endian unless swapBytes=True.
        # If your camera build returns (frame, meta), take frame[0].
        if isinstance(frame, tuple):
            frame = frame[0]

        if len(frame) != (CAM_W * CAM_H * 2):
            # Common mismatch: camera fell back to JPEG or different resolution.
            # Show a marker and stop rather than spamming random pixels.
            tft.fillRect(0, 0, tft.width(), 12, 0x0000)
            tft.drawRect(0, 0, 160, 60, 0xF800)
            print("Bad frame size:", len(frame), "expected:", CAM_W * CAM_H * 2)
            del frame
            gc.collect()
            time.sleep_ms(3000)
            continue

        tft.pushImage(0, 0, CAM_W, CAM_H, frame, swapBytes=SWAP_CAMERA_BYTES)
        del frame
        gc.collect()

        frame_count += 1
        # Update FPS indicator occasionally
        if frame_count % 10 == 0:
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last)
            last = now
            fps = 0
            if dt > 0:
                fps = (1000 * 10) // dt
            # Draw a small status line in top-left
            # (text rendering uses the current font; if no font set, it will just skip).
            try:
                tft.setTextColor(0xFFE0, 0x0000)
                tft.drawString("FPS:%d" % fps, 2, 2)
            except Exception:
                pass


main()

