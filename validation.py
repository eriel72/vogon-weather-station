import math
import config

ALTITUDE_M = 141

def dewpoint(temp, humidity):

    if temp is None or humidity is None:
        return None

    if humidity <= 0:
        return None

    a = 17.27
    b = 237.7

    gamma = ((a * temp) / (b + temp)) + math.log(humidity / 100.0)

    return round((b * gamma) / (a - gamma), 2)


def valid(data):

    try:

        t = data.get("temp")
        h = data.get("humidity")
        p = data.get("pressure")

        if t is not None:

            if t == 85.0:
                print("BAD TEMP: DS18B20 startup value")
                return False

            if not (config.TEMP_MIN <= t <= config.TEMP_MAX):
                return False

        if h is not None and not (
            config.HUM_MIN <= h <= config.HUM_MAX
        ):
            return False

        if p is not None and not (
            config.PRESSURE_MIN <= p <= config.PRESSURE_MAX
        ):
            return False

        return True

    except:
        return False
    
def sea_level_pressure(p_hpa, temp_c):
    if p_hpa is None or temp_c is None:
        return None

    slp = p_hpa * (
        1 - (0.0065 * ALTITUDE_M)
        / (temp_c + 273.15 + 0.0065 * ALTITUDE_M)
    ) ** -5.257

    return round(slp, 1)