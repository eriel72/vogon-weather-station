"""
VOGON Weather Station
SHT41 driver for MicroPython

Based on the work by Jose D. Montoya:
https://github.com/jposada202020/MicroPython_SHT4X

The original driver has been simplified and adapted for
the VOGON Weather Station project.

Copyright (c) 2026 Erik Elfsberg
Original concepts and implementation:
Copyright (c) 2023 Jose D. Montoya
"""

import time
import struct

class SHT41:
    def __init__(self, i2c, address=0x44):
        self.i2c = i2c
        self.address = address

    def read(self):
        self.i2c.writeto(self.address, bytes([0xFD]))
        time.sleep(0.02)   # high precision just needs ~10 ms, some marginal

        data = self.i2c.readfrom(self.address, 6)

        raw_t, crc_t, raw_h, crc_h = struct.unpack(">HBHB", data)

        if crc_t != self._crc(data[0:2]) or crc_h != self._crc(data[3:5]):
            raise RuntimeError("SHT41 CRC error")

        temp = -45 + 175 * raw_t / 65535
        rh = -6 + 125 * raw_h / 65535
        rh = max(0, min(100, rh))

        return temp, rh

    def _crc(self, data):
        crc = 0xFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
        return crc & 0xFF