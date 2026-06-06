import time
import machine

class ONEWIRE:
    CMD_SEARCHROM = 0xf0
    CMD_READROM = 0x33
    CMD_MATCHROM = 0x55
    CMD_SKIPROM = 0xcc
    CMD_ALARMSEARCH = 0xec

    def __init__(self, pin):
        self.pin = pin
        self.pin.init(pin.OPEN_DRAIN, pin.PULL_UP)

    def reset(self):
        self.pin(0)
        time.sleep_us(480)
        self.pin(1)
        time.sleep_us(70)
        presence = not self.pin()
        time.sleep_us(410)
        return presence

    def write_bit(self, value):
        self.pin(0)
        time.sleep_us(2)
        self.pin(value)
        time.sleep_us(60)
        self.pin(1)

    def read_bit(self):
        self.pin(0)
        time.sleep_us(2)
        self.pin(1)
        time.sleep_us(10)
        value = self.pin()
        time.sleep_us(50)
        return value

    def write_byte(self, value):
        for i in range(8):
            self.write_bit(value & 1)
            value >>= 1

    def read_byte(self):
        value = 0
        for i in range(8):
            value >>= 1
            if self.read_bit():
                value |= 0x80
        return value