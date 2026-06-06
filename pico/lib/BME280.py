from machine import I2C
import time

class BME280:
    def __init__(self, i2c: I2C, address=0x77):
        self.i2c = i2c
        self.address = address
        self.t_fine = 0

        time.sleep(0.5)

    # soft reset
        self._write(0xE0, 0xB6)
        time.sleep(0.5)

    # IMPORTANT: liten stabilisering innan read
        time.sleep(0.2)

        self._load_calibration()

        self._write(0xF2, 0x01)
        self._write(0xF4, 0x27)
        self._write(0xF5, 0xA0)
    # ---------- Low level I2C ----------
    def _read(self, reg, n=1):
        for _ in range(5):
            try:
                return self.i2c.readfrom_mem(self.address, reg, n)
            except OSError:
                time.sleep_ms(20)
        raise OSError("BME280 read failed")

    def _write(self, reg, val):
        for _ in range(5):
            try:
                self.i2c.writeto_mem(self.address, reg, bytes([val]))
                return
            except OSError:
                time.sleep_ms(20)
        raise OSError("BME280 write failed")

    def _read_u16(self, reg):
        d = self._read(reg, 2)
        return d[0] | (d[1] << 8)

    def _read_s16(self, reg):
        result = self._read_u16(reg)
        if result > 32767:
            result -= 65536
        return result

    def _read_u8(self, reg):
        return self._read(reg, 1)[0]

    def _read_s8(self, reg):
        result = self._read_u8(reg)
        if result > 127:
            result -= 256
        return result

    # ---------- Calibration ----------
    def _load_calibration(self):
        self.dig_T1 = self._read_u16(0x88)
        self.dig_T2 = self._read_s16(0x8A)
        self.dig_T3 = self._read_s16(0x8C)

        self.dig_P1 = self._read_u16(0x8E)
        self.dig_P2 = self._read_s16(0x90)
        self.dig_P3 = self._read_s16(0x92)
        self.dig_P4 = self._read_s16(0x94)
        self.dig_P5 = self._read_s16(0x96)
        self.dig_P6 = self._read_s16(0x98)
        self.dig_P7 = self._read_s16(0x9A)
        self.dig_P8 = self._read_s16(0x9C)
        self.dig_P9 = self._read_s16(0x9E)

        self.dig_H1 = self._read_u8(0xA1)
        self.dig_H2 = self._read_s16(0xE1)
        self.dig_H3 = self._read_u8(0xE3)

        e4 = self._read_u8(0xE4)
        e5 = self._read_u8(0xE5)
        e6 = self._read_s8(0xE6)

        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = self._read_s8(0xE7)

    # ---------- Raw read ----------
    def _read_raw(self):
        data = self._read(0xF7, 8)

        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7]

        return adc_t, adc_p, adc_h

    # ---------- Compensated ----------
    def read(self):
        try:
            adc_t, adc_p, adc_h = self._read_raw()
        except OSError:
            return None, None, None  # fail-safe

        # Temperature
        var1 = (adc_t / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((adc_t / 131072.0 - self.dig_T1 / 8192.0) ** 2) * self.dig_T3
        self.t_fine = var1 + var2
        temp = self.t_fine / 5120.0

        # Pressure
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1

        if var1 == 0:
            pressure = 0
        else:
            p = 1048576.0 - adc_p
            p = (p - var2 / 4096.0) * 6250.0 / var1
            var1 = self.dig_P9 * p * p / 2147483648.0
            var2 = p * self.dig_P8 / 32768.0
            pressure = p + (var1 + var2 + self.dig_P7) / 16.0

        # Humidity
        h = self.t_fine - 76800.0
        h = (adc_h - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * h)) * (
            self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * h *
            (1.0 + self.dig_H3 / 67108864.0 * h))
        )
        h = h * (1.0 - self.dig_H1 * h / 524288.0)

        if h > 100:
            h = 100
        elif h < 0:
            h = 0

        return temp, pressure, h