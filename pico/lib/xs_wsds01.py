import machine
import time


class XS_WSDS01:
    REQUEST = bytes((0x01, 0x03, 0x00, 0x00, 0x00, 0x05, 0x85, 0xC9))

    def __init__(self, uart, de_pin, north_offset=0.0):
        self.uart = uart
        self.de = machine.Pin(de_pin, machine.Pin.OUT)
        self.de.value(0)
        self.north_offset = north_offset  # Kalibrering sker i WindMinute, inte här.
        self.last_error = None

    @staticmethod
    def _crc16(data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def read(self, timeout_ms=350):
        self.last_error = None
        self.de.value(0)
        try:
            # Töm gammal data utan att fastna om nya byte fortsätter komma.
            self.uart.read()
            self.de.value(1)
            time.sleep_us(150)
            written = self.uart.write(self.REQUEST)
            if written != len(self.REQUEST):
                self.last_error = 'UART write incomplete'
                return None
            # Vänta tills UART har sänt hela meddelandet innan DE sänks.
            self.uart.flush()
            time.sleep_us(150)
            self.de.value(0)

            response = bytearray()
            start = time.ticks_ms()
            expected = 15
            while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
                available = self.uart.any()
                if available:
                    chunk = self.uart.read(min(available, expected - len(response)))
                    if chunk:
                        response.extend(chunk)
                        if len(response) >= 3 and response[1] == 0x83:
                            expected = 5  # Modbus exception frame
                        if len(response) >= expected:
                            break
                time.sleep_ms(2)

            if len(response) != expected:
                self.last_error = 'Short/timeout response: %d/%d bytes' % (len(response), expected)
                return None
            if response[0] != 1:
                self.last_error = 'Unexpected slave address'
                return None
            crc = self._crc16(response[:-2])
            if response[-2] != (crc & 0xFF) or response[-1] != (crc >> 8):
                self.last_error = 'CRC mismatch'
                return None
            if response[1] == 0x83:
                self.last_error = 'Modbus exception %d' % response[2]
                return None
            if response[1] != 3 or response[2] != 10:
                self.last_error = 'Unexpected function/byte count'
                return None

            def reg(i):
                return (response[i] << 8) | response[i + 1]

            wind_ms = reg(3) / 10.0
            direction = reg(9) / 10.0
            if not (0 <= wind_ms <= 75 and 0 <= direction <= 360):
                self.last_error = 'Out-of-range measurement'
                return None
            return {
                'wind_speed': wind_ms,
                'wind_speed_kmh': reg(7) / 100.0,
                'beaufort': reg(5),
                'wind_direction': direction,
                'bearing': reg(11),
            }
        except Exception as exc:
            self.last_error = repr(exc)
            return None
        finally:
            self.de.value(0)