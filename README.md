MicroPython WS2812
==================

MicroPython driver for WS2812, WS2812B, and compatible RGB LEDs. These are
popular RGB LEDs used for example in AdaFruit NeoPixels rings, stripes, boards,
etc.

You can check more about the microPython project here: http://micropython.org

Installation
------------

Copy `ws2812.py` file to your pyboard.

Wiring
------

WS2812 driver is using SPI bus. Connect your LED's input wire to the SPI bus 1
MOSI (pin X8 on pyboard) or SPI bus 2 MOSI (pin Y8 on pyboard). Connect LED's
power and ground wires to VIN and GND on pyboard. The same applies for LED
rings, stripes, etc. (they have always one input wire).

Note: USB may be insufficient for powering lots of RGB LEDs. You may need to
youse additional power source.

Usage
-----

```
from ws2812 import WS2812
chain = WS2812(spi_bus=1, led_count=4)
data = [
    (255, 0, 0),    # red
    (0, 255, 0),    # green
    (0, 0, 255),    # blue
    (85, 85, 85),   # white
]
chain.show(data)
```

There are files `example_simple.py` and `example_advanced.py` prepared for
NeoPixels ring (or similar) with 16 RGB LEDs. If you have it connected to SPI
bus 1 then just copy `example_simple.py` or `example_advanced.py` as `main.py`
to your pyboard and reset your pyboard.

Here is a video of `example_advanced.py` in action: http://youtu.be/ADYxiG40UJ0