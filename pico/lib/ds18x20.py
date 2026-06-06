import time

class DS18X20:
    def __init__(self, onewire):
        self.ow = onewire
        self.roms = []

    def scan(self):
        # enkel scan (skip ROM version)
        self.roms = [b for b in self._search_rom()]
        return self.roms

    def _search_rom(self):
        # minimal implementation
        return []

    def convert_temp(self):
        self.ow.reset()
        self.ow.write_byte(0xCC)
        self.ow.write_byte(0x44)

    def read_temp(self, rom):
        self.ow.reset()
        self.ow.write_byte(0x55)
        for b in rom:
            self.ow.write_byte(b)

        self.ow.write_byte(0xBE)

        data = bytearray(9)
        for i in range(9):
            data[i] = self.ow.read_byte()

        temp = data[0] | (data[1] << 8)

        if temp & 0x8000:
            temp = -((temp ^ 0xffff) + 1)

        return temp / 16