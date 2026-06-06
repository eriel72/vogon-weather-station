from machine import I2C
import time

class ADS1115:
    # Register
    _REG_CONVERSION = 0x00
    _REG_CONFIG = 0x01

    # Gain settings (PGA)
    GAIN_6_144V = 0x0000
    GAIN_4_096V = 0x0200
    GAIN_2_048V = 0x0400
    GAIN_1_024V = 0x0600
    GAIN_0_512V = 0x0800
    GAIN_0_256V = 0x0A00

    # LSB size per gain
    _LSB = {
        GAIN_6_144V: 0.1875e-3,
        GAIN_4_096V: 0.125e-3,
        GAIN_2_048V: 0.0625e-3,
        GAIN_1_024V: 0.03125e-3,
        GAIN_0_512V: 0.015625e-3,
        GAIN_0_256V: 0.0078125e-3,
    }

    # MUX (single-ended)
    _MUX = {
        0: 0x4000,
        1: 0x5000,
        2: 0x6000,
        3: 0x7000,
    }

    def __init__(self, i2c: I2C, address=0x48, gain=GAIN_4_096V):
        self.i2c = i2c
        self.address = address
        self.gain = gain

    def read_raw(self, channel):
        config = (
            0x8000 |                # Start conversion
            self._MUX[channel] |
            self.gain |
            0x0100 |                # Single-shot mode
            0x0080 |                # 128 SPS
            0x0003                  # Disable comparator
        )

        self.i2c.writeto_mem(self.address, self._REG_CONFIG, config.to_bytes(2, "big"))
        time.sleep(0.01)

        data = self.i2c.readfrom_mem(self.address, self._REG_CONVERSION, 2)
        value = int.from_bytes(data, "big")

        if value > 0x7FFF:
            value -= 0x10000

        return value

    def read_voltage(self, channel):
        raw = self.read_raw(channel)
        return raw * self._LSB[self.gain]

    def read_average(self, channel, samples=5, delay=0.002):
        total = 0
        for _ in range(samples):
            total += self.read_voltage(channel)
            time.sleep(delay)
        return total / samples