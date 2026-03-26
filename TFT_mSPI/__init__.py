"""
TFT_mSPI: pure MicroPython TFT display + touch library.

This is the package installed by `mip` (from `package.json`).
"""

from .core.colors import color565
from .core.bus_spi import SPIBus
from .core.tft import TFT

from .panels.gc9a01 import GC9A01
from .panels.ili9341 import ILI9341
from .panels.ili9486 import ILI9486
from .panels.ili9488 import ILI9488
from .panels.st7735 import ST7735
from .panels.st7789 import ST7789
from .panels.st7796 import ST7796

from .touch.xpt2046 import XPT2046
from .touch.stmpe610 import STMPE610
from .touch.ft6236 import FT6236
from .touch.gt911 import GT911
from .touch.cst816 import CST816

try:
    from .compat.tft_espi import TFT_eSPI, TFT_eSprite
except ImportError as _compat_exc:
    class _CompatMissing:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "TFT_eSPI compatibility layer unavailable. "
                "Reinstall/update TFT_mSPI with mip. Cause: %s" % _compat_exc
            )

    TFT_eSPI = _CompatMissing
    TFT_eSprite = _CompatMissing

__all__ = [
    "TFT",
    "TFT_eSPI",
    "TFT_eSprite",
    "SPIBus",
    "GC9A01",
    "ILI9341",
    "ILI9486",
    "ILI9488",
    "ST7735",
    "ST7789",
    "ST7796",
    "XPT2046",
    "STMPE610",
    "FT6236",
    "GT911",
    "CST816",
    "color565",
]

