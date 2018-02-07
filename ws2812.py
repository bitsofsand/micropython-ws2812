# -*- coding: utf-8 -*-

#TODO: rework to use Class PL9823 & use a base Class LED for both LED types


import gc
import pyb

PL9823_ONE_BIT = 0b11110
PL9823_ZERO_BIT = 0b10000
PL9823_RESETBUF_SIZE = 150   # 150 cycles = 50us = reset pattern

class WS2812:
    """
    Driver for WS2812 RGB LEDs. May be used for controlling single LED or chain
    of LEDs.

    Example of use:

        chain = WS2812(spi_bus=1, led_count=4)
        data = [
            (255, 0, 0),    # red
            (0, 255, 0),    # green
            (0, 0, 255),    # blue
            (85, 85, 85),   # white
        ]
        chain.show(data)

    Version: 1.0
    """
    buf_bytes = (0x11, 0x13, 0x31, 0x33)

    def __init__(self, spi_bus=1, led_count=1, intensity=1, pl9823=False):
        """
        Params:
        * spi_bus = SPI bus ID (1 or 2)
        * led_count = count of LEDs
        * intensity = light intensity (float up to 1)
        """
        self.led_count = led_count
        self.intensity = intensity
        self.pl9823 = pl9823

        # prepare SPI data buffer (4 bytes for each color -- 5 bytes for PL9823)
        self.buf_length = self.led_count * 5 * 3 if pl9823 else self.led_count * 4 * 3
        self.buf = bytearray(self.buf_length)

        # Reset data buffer for PL9823
        if self.pl9823:
            self.resetbuf = bytearray(PL9823_RESETBUF_SIZE)
            for num in range(len(self.resetbuf)):
                self.resetbuf[num] = 0

        # SPI init
        baudrate = 2857000 if self.pl9823 else 3200000
        self.spi = pyb.SPI(spi_bus, pyb.SPI.MASTER, baudrate=baudrate, polarity=0, phase=1)

        # turn LEDs off
        self.show([])

    def show(self, data):
        """
        Show RGB data on LEDs. Expected data = [(R, G, B), ...] where R, G and B
        are intensities of colors in range from 0 to 255. One RGB tuple for each
        LED. Count of tuples may be less than count of connected LEDs.
        """
        self.fill_buf(data)
        self.send_buf()

    def send_buf(self):
        """
        Send buffer over SPI.
        """

        self.spi.send(self.buf)
        # PL9823 need an explicit reset code, or the last LED might not light up
        if self.pl9823:
            self.spi.send(self.resetbuf)
        gc.collect()


    def _update_buf_ws2812(self, data, start): 

        # Order of colors is changed from RGB to GRB as that is what WS2812
        # expects on the wire

        # If you find this function ugly, it's becasue speed optimisation
        # beat purity of code

        buf = self.buf
        buf_bytes = self.buf_bytes
        intensity = self.intensity

        mask = 0x03
        index = start * 12
        for red, green, blue in data:
            red = int(red * intensity)
            green = int(green * intensity)
            blue = int(blue * intensity)

            buf[index] = buf_bytes[green >> 6 & mask]
            buf[index+1] = buf_bytes[green >> 4 & mask]
            buf[index+2] = buf_bytes[green >> 2 & mask]
            buf[index+3] = buf_bytes[green & mask]

            buf[index+4] = buf_bytes[red >> 6 & mask]
            buf[index+5] = buf_bytes[red >> 4 & mask]
            buf[index+6] = buf_bytes[red >> 2 & mask]
            buf[index+7] = buf_bytes[red & mask]

            buf[index+8] = buf_bytes[blue >> 6 & mask]
            buf[index+9] = buf_bytes[blue >> 4 & mask]
            buf[index+10] = buf_bytes[blue >> 2 & mask]
            buf[index+11] = buf_bytes[blue & mask]

            index += 12

        return index // 12

    def _update_buf_pl9823(self, data, start):

        buf = self.buf
        current_buf_index = start * 15
    
        for led in data:

            for color in led:

                color = int(color * self.intensity)

                # Expand data bits to SPI bit values
                color_bits = [ x*0 for x in range(8)]            
                for bit in range(8):
                    if color & (1 << bit):
                        color_bits[bit] = PL9823_ONE_BIT
                    else:
                        color_bits[bit] = PL9823_ZERO_BIT

                # Bit manipulation to put data bits into SPI data buffer
                # This is the fast hack version. TODO: replace with bitfield implementation
                buf[current_buf_index] = ((color_bits[0] << 3)
                                          + ((color_bits[1] & 0b11100) >> 2) )
                buf[current_buf_index + 1] = ((color_bits[1]<<6 & 0xFF)
                                              + (color_bits[2] << 1)
                                              + ((color_bits[3] & 0b10000) >> 4))
                buf[current_buf_index + 2] = ((color_bits[3]<<4 & 0xFF)
                                              + ((color_bits[4] & 0b11110) >> 1))
                buf[current_buf_index + 3] = ((color_bits[4]<<7 & 0xFF)
                                              + (color_bits[5] << 2)
                                              + ((color_bits[6] & 0b10000) >> 4))
                buf[current_buf_index + 4] = ((color_bits[6]<<5 & 0xFF)
                                              + color_bits[7])
                current_buf_index += 5

        return current_buf_index // 15


    def update_buf(self, data, start=0):
        """
        Fill a part of the buffer with RGB data.

        Returns the index of the first unfilled LED
        """

        if self.pl9823:
            return self._update_buf_pl9823(data, start)
        else:
            return self._update_buf_ws2812(data, start)



    def fill_buf(self, data):
        """
        Fill buffer with RGB data.

        All LEDs after the data are turned off.
        """
        end = self.update_buf(data)

        # turn off the rest of the LEDs
        buf = self.buf
        off = self.buf_bytes[0]
        factor = 15 if self.pl9823 else 12
        for index in range(end * factor, self.buf_length):
            buf[index] = off
            index += 1
