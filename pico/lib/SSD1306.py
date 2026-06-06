# MicroPython SSD1306 driver (I2C only)
import framebuf

class SSD1306_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.buffer = bytearray((height // 8) * width)
        super().__init__(self.buffer, width, height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def write_data(self, buf):
        self.i2c.writeto(self.addr, bytearray([0x40]) + buf)

    def init_display(self):
        for cmd in (
            0xAE, 0x20, 0x00, 0xB0, 0xC8,
            0x00, 0x10, 0x40, 0x81, 0xFF,
            0xA1, 0xA6, 0xA8, 0x3F,
            0xA4, 0xD3, 0x00, 0xD5,
            0xF0, 0xD9, 0x22, 0xDA,
            0x12, 0xDB, 0x20, 0x8D,
            0x14, 0xAF
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def show(self):
        for i in range(0, self.height // 8):
            self.write_cmd(0xB0 + i)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            self.write_data(self.buffer[i*self.width:(i+1)*self.width])