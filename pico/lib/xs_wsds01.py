import machine
import time


class XS_WSDS01:

    def __init__(self, uart, de_pin):
        self.uart = uart
        self.de = machine.Pin(de_pin, machine.Pin.OUT)
        self.de.value(0)      # mottagningsläge

        # Läs register 0x0000 - 0x0004
        self.request = bytes([
            0x01, 0x03,
            0x00, 0x00,
            0x00, 0x05,
            0x85, 0xC9
        ])

    def read(self):

        # Töm mottagarbufferten
        while self.uart.any():
            self.uart.read()

        # Sänd
        self.de.value(1)
        time.sleep_us(100)

        self.uart.write(self.request)

        # 8 byte @9600 baud
        time.sleep_us(9000)

        self.de.value(0)

        # Vänta på svar
        start = time.ticks_ms()

        while not self.uart.any():
            if time.ticks_diff(time.ticks_ms(), start) > 300:
                return None

        time.sleep_ms(20)

        data = self.uart.read()

        if data is None or len(data) != 15:
            return None

        # Kontrollera adress och funktion
        if data[0] != 1 or data[1] != 3:
            return None

        wind_ms = ((data[3] << 8) | data[4]) / 10.0
        beaufort = (data[5] << 8) | data[6]
        wind_kmh = ((data[7] << 8) | data[8]) / 100.0
        direction = ((data[9] << 8) | data[10]) / 10.0
        bearing = (data[11] << 8) | data[12]

        return {
            "wind_speed": wind_ms,
            "wind_speed_kmh": wind_kmh,
            "beaufort": beaufort,
            "wind_direction": direction,
            "bearing": bearing
        }
    def __init__(self, uart, de_pin, north_offset=0.0):
        self.uart = uart
        self.de = machine.Pin(de_pin, machine.Pin.OUT)
        self.de.value(0)

        self.north_offset = north_offset

        self.request = bytes([
            0x01, 0x03,
            0x00, 0x00,
            0x00, 0x05,
            0x85, 0xC9
        ])