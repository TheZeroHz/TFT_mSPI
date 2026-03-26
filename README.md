# TFT_mSPI (MicroPython)

Pure MicroPython TFT display + touch library with a **TFT_eSPI-like API**. It is designed to be **modular** and to cover the common ST/GC/ILI display controller families, plus popular touch controllers.

## Supported targets (v1)

- **ESP32** (ESP32 / S2 / S3)
- **RP2040** (Raspberry Pi Pico / Pico W)

## Supported display controllers (v1)

- **ST77xx**: `ST7735`, `ST7789`, `ST7796`
- **ILI**: `ILI9341`, `ILI9486`, `ILI9488`
- **GC**: `GC9A01`

## Supported touch controllers (v1)

- **SPI resistive**: `XPT2046/ADS7846`, `STMPE610`
- **I2C capacitive**: `FT6236/FT6336`, `GT911`, `CST816`

## Install on MicroPython

If you do not use `mip`, copy these folders to your device filesystem:

- `TFT_mSPI/` (created by the `mip` install mapping in `package.json`)
- `sysfont.py` (optional, for text rendering with the included bitmap font)

### Install with `mip` (MicroPython)

If you host this repo on GitHub, you can install it directly:

```python
import mip
mip.install("github:TheZeroHz/TFT_mSPI")
```

If you want TFT_eSPI-style imports, use:

```python
from TFT_mSPI import TFT, TFT_eSPI
```

## Quick start (ST7735)

```python
from machine import SPI, Pin
from TFT_mSPI import SPIBus, TFT, ST7735

spi = SPI(2, baudrate=20_000_000, polarity=0, phase=0,
          sck=Pin(14), mosi=Pin(13), miso=Pin(12))
dc  = Pin(16, Pin.OUT)
rst = Pin(17, Pin.OUT)
cs  = Pin(18, Pin.OUT)

bus = SPIBus(spi, dc=dc, cs=cs, rst=rst)
panel = ST7735(bus, tab="red", bgr=False)  # try tab="green"/"blue" if offsets differ
tft = TFT(panel, rotation=0)
tft.init()

tft.fill(tft.BLACK)
tft.draw_rect(0, 0, tft.width, tft.height, tft.YELLOW)
```

## Examples

- Core/legacy:
  - `examples/st7735_graphicstest_legacy_api.py`
  - `examples/esp32s3_st7735_pinout_example.py`
- ST7735 (ESP32-S3, same pin config):
  - `examples/esp32s3_st7735_tftespi_graphicstest.py`
  - `examples/tft_espi_compat_esp32s3_st7735.py`
  - `examples/esp32s3_st7735_sprite_demo.py`
  - `examples/esp32s3_st7735_text_datums_demo.py`
  - `examples/esp32s3_st7735_flash_image_128x160.py`
- ILI9341 (ESP32-S3, same pin config, no touch):
  - `examples/esp32s3_ili9341_tftespi_graphicstest.py`
  - `examples/esp32s3_ili9341_pdq_benchmark.py`
  - `examples/esp32s3_ili9341_flash_image_no_touch.py`
  - `examples/esp32s3_ili9341_color_order_diag.py`
- Touch:
  - `examples/touch_xpt2046_demo.py`

## TFT_eSPI compatibility status

`TFT_mSPI` now includes a `TFT_eSPI` facade (`TFT_mSPI.compat.tft_espi`) to ease C++ sketch porting.

### Implemented (usable)

- Core draw API: `fillScreen`, `drawPixel`, `drawLine`, `drawFastHLine`, `drawFastVLine`, `fillRect`, `drawRect`
- Shapes: `drawRoundRect`, `fillRoundRect`, `drawCircle`, `fillCircle`, `drawEllipse`, `fillEllipse`, `drawTriangle`, `fillTriangle`
- Arc helpers: `drawArc`, `fillArc` (line-segment approximation)
- Bitmap/image: `setSwapBytes`, `getSwapBytes`, `setBitmapColor`, `drawBitmap`, `drawXBitmap`, `pushImage`, `pushColors`, `pushRect`
- Text state and drawing: `setTextColor`, `setTextWrap`, `setTextFont`, `setTextSize`, `setCursor`, `getCursorX`, `getCursorY`, `setTextDatum`, `getTextDatum`, `setTextPadding`, `getTextPadding`, `drawString`, `drawCentreString`, `drawRightString`, `drawNumber`, `drawFloat`, `print`, `textWidth`, `fontHeight`
- Display control: `begin`, `init`, `setRotation`, `getRotation`, `invertDisplay`, `sleep`
- Sprite basics: `createSprite`, `deleteSprite`, `fillSprite`, `drawPixel`, `readPixel`, `drawLine`, `drawFastHLine`, `drawFastVLine`, `fillRect`, `pushImage`, `pushSprite`, `pushToSprite`

### Implemented as compatibility fallbacks (not anti-aliased)

- `drawSmoothArc`, `drawSmoothCircle`, `fillSmoothCircle`, `drawSmoothRoundRect`, `fillSmoothRoundRect`, `drawSpot`, `drawWideLine`, `drawWedgeLine`

These map to non-AA primitives so ports run, but visual output is not identical to C++ smooth graphics.

### Not supported yet (or hardware-dependent in MicroPython)

- DMA API: `initDMA`, `pushImageDMA`, `pushPixelsDMA`, `dmaBusy`, `dmaWait`
- Full viewport/origin pipeline from C++ (`setViewport`, clipping helpers, frameViewport, resetViewport)
- Readback-heavy API on write-only panels (`readRect`, `readRectRGB`, true `readPixel` from TFT panel)
- Smooth font file pipeline (`loadFont`/file-backed glyph rendering)
- Advanced sprite features from C++ (`pushRotated`, `getRotatedBounds`, 1/4/8bpp palette sprites, scroll rect)

## Porting tip

For most Arduino sketches, keep your panel/bus setup in `TFT_mSPI` style and only wrap the display:

```python
from TFT_mSPI import SPIBus, TFT, ST7789, TFT_eSPI

tft_core = TFT(ST7789(bus), rotation=1)
tft = TFT_eSPI(tft_core)
tft.begin()
tft.fillScreen(0x0000)
```

## Notes and known constraints

- **Speed**: this is pure Python; prefer `fill_rect()`/`blit_buffer()` over per-pixel calls.
- **ILI9486/ILI9488 over SPI**: these are typically **18-bit** panels; `tft_mspi` accepts RGB565 buffers and converts to RGB666 when `panel.pixel_format = 18` (already set for `ILI9486`/`ILI9488`).
