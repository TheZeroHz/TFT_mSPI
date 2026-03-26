def color565(r, g, b):
    """Convert 8-bit RGB to RGB565 (integer 0..65535)."""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def swap16(x):
    """Swap endian of a 16-bit int."""
    return ((x & 0xFF) << 8) | ((x >> 8) & 0xFF)

