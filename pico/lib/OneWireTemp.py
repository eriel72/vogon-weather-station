from onewire import OneWire
from ds18x20 import DS18X20
import time

class ONEWIRETEMP:
    def __init__(self, pin):
        self.ow = OneWire(pin)
        self.ds = DS18X20(self.ow)
        self.roms = self.ds.scan()
        self.temps = []

    def start(self):
        self.ds.convert_temp()

    def read_all(self):
        self.temps = [self.ds.read_temp(r) for r in self.roms]
        return self.temps