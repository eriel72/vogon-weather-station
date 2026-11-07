# VOGON BUREAU OF METROLOGY
# WEATHER STATION CORE v2 - VERBOSE STARTUP DEBUG

import machine
import time
import ujson
import network
import secrets
import onewire
import ubinascii
import config

from SSD1306 import SSD1306_I2C
from ds18x20 import DS18X20
from state import RainState
from umqtt.simple import MQTTClient
from piicodev_ms5637 import PiicoDev_MS5637
from sht41 import SHT41
from xs_wsds01 import XS_WSDS01
from wind_minute import WindMinute

# ============================================================
# CONFIGURATION
# ============================================================

ONEWIRE_PIN = 15
RAIN_PIN = 16
MQTT_TOPIC = "weather/data"
MQTT_TEST_TOPIC = "test/topic"
MQTT_SERVER = getattr(secrets, "MQTT_SERVER", "192.168.1.160")
RAIN_DEBOUNCE_MS = 500
SAVE_INTERVAL = 10000

DEBUG = True

DS18B20_SENSORS = {
    "green_nw": {
        "rom": ubinascii.unhexlify("2887B92F040000B9"),
        "min": -35,
        "max": 50,
    },
    "red_wnw": {
        "rom": ubinascii.unhexlify("286B003E0E00008C"),
        "min": -35,
        "max": 50,
    },
    "blue_ne": {
        "rom": ubinascii.unhexlify("28BD3DDE040000B1"),
        "min": -35,
        "max": 50,
    },
    "purple_ese": {
        "rom": ubinascii.unhexlify("2832863E0E000063"),
        "min": -35,
        "max": 50,
    },
    "box": {
        "rom": ubinascii.unhexlify("286FC32F040000E1"),
        "min": -35,
        "max": 80,
    },
}

OUTDOOR_NAMES = (
    "green_nw",
    "red_wnw",
    "blue_ne",
    "purple_ese",
)


# ============================================================
# UART SET UP
# ============================================================
uart = machine.UART(0, baudrate=9600, bits=8, parity=None, stop=1, tx=machine.Pin(12), rx=machine.Pin(13), timeout=200)

wind_sensor = XS_WSDS01(uart=uart, de_pin=14)

wind_minute = WindMinute(north_offset=76.0)

WIND_SAMPLE_INTERVAL_MS = 1000
REPORT_INTERVAL_MS = 60_000


# ============================================================
# DEBUG HELPERS
# ============================================================

def section(title):
    if not DEBUG:
        return
    print("\n" + "=" * 58)
    print(title)
    print("=" * 58)


def rom_text(rom):
    return ubinascii.hexlify(rom).decode().upper()


def sensor_name_from_rom(rom):
    for name, sensor in DS18B20_SENSORS.items():
        if sensor["rom"] == rom:
            return name
    return "UNKNOWN"


def oled_message(line1, line2=None, line3=None, line4=None):
    oled.fill(0)
    oled.text(str(line1)[:16], 0, 0)
    if line2 is not None:
        oled.text(str(line2)[:16], 0, 16)
    if line3 is not None:
        oled.text(str(line3)[:16], 0, 32)
    if line4 is not None:
        oled.text(str(line4)[:16], 0, 48)
    oled.show()


def print_i2c_scan(i2c_bus):
    addresses = i2c_bus.scan()
    print("I2C devices found:", len(addresses))
    for address in addresses:
        print("  0x{:02X}".format(address))
    return addresses


def scan_1wire(ds18):
    print("Scanning 1-Wire bus on GP{}...".format(ONEWIRE_PIN))
    try:
        found = ds18.scan()
    except Exception as error:
        print("1-Wire scan FAILED:", repr(error))
        return []

    print("1-Wire devices found:", len(found))
    for rom in found:
        print("  {}  {}".format(rom_text(rom), sensor_name_from_rom(rom)))

    print("Expected sensor status:")
    for name, sensor in DS18B20_SENSORS.items():
        state = "FOUND" if sensor["rom"] in found else "MISSING"
        print("  {:12s} {}  {}".format(name, rom_text(sensor["rom"]), state))

    return found


def read_ds18b20_sensors(ds18, sensors, found_roms):
    values = {}

    print("Starting DS18B20 conversion...")
    try:
        ds18.convert_temp()
    except Exception as error:
        print("DS18B20 convert_temp FAILED:", repr(error))
        return {name: None for name in sensors}

    time.sleep_ms(800)
    print("Reading DS18B20 sensors:")

    for name, sensor in sensors.items():
        rom = sensor["rom"]
        min_temp = sensor["min"]
        max_temp = sensor["max"]

        if rom not in found_roms:
            print("  {:12s} {}  NOT ON BUS".format(name, rom_text(rom)))
            values[name] = None
            continue

        try:
            temp = ds18.read_temp(rom)

            if temp is None:
                print("  {:12s} {}  None".format(name, rom_text(rom)))
                values[name] = None
            elif temp == 85.0:
                print("  {:12s} {}  85.0 C INVALID".format(name, rom_text(rom)))
                values[name] = None
            elif not (min_temp < temp < max_temp):
                print("  {:12s} {}  {:.3f} C OUT OF RANGE".format(
                    name, rom_text(rom), temp
                ))
                values[name] = None
            else:
                print("  {:12s} {}  {:.3f} C OK".format(
                    name, rom_text(rom), temp
                ))
                values[name] = temp

        except Exception as error:
            print("  {:12s} {}  READ FAILED: {}".format(
                name, rom_text(rom), repr(error)
            ))
            values[name] = None

    return values


def select_outdoor_temperature(ds_temps):
    valid_outdoor = {
        name: ds_temps.get(name)
        for name in OUTDOOR_NAMES
        if ds_temps.get(name) is not None
    }

    print("Valid outdoor sensors:", valid_outdoor)

    if not valid_outdoor:
        print("Selected outdoor sensor: NONE")
        return None, None

    selected = min(valid_outdoor, key=valid_outdoor.get)
    temperature = valid_outdoor[selected]
    print("Selected outdoor sensor: {} = {:.3f} C".format(
        selected, temperature
    ))
    return selected, temperature


def read_sht41_avg(sht_sensor, n=3):
    temps = []
    hums = []

    for sample in range(n):
        try:
            temp, humidity = sht_sensor.read()
            print("  SHT41 sample {}: temp={} humidity={}".format(
                sample + 1, temp, humidity
            ))
            if temp is not None and humidity is not None:
                temps.append(temp)
                hums.append(humidity)
        except Exception as error:
            print("  SHT41 sample {} FAILED: {}".format(
                sample + 1, repr(error)
            ))
        time.sleep_ms(200)

    if not temps:
        return None, None

    return sum(temps) / len(temps), sum(hums) / len(hums)


# ============================================================
# RAIN IRQ
# ============================================================

last_rain_tip_ms = None
rain_tip_interval_ms = None
rain_tips_interval = 0
last_rain_irq = time.ticks_ms() - RAIN_DEBOUNCE_MS


def rain_irq(pin):
    global last_rain_irq
    global last_rain_tip_ms
    global rain_tip_interval_ms
    global rain_tips_interval

    now = time.ticks_ms()

    if time.ticks_diff(now, last_rain_irq) < RAIN_DEBOUNCE_MS:
        return

    last_rain_irq = now
    rain_state.add_tip()
    rain_tips_interval += 1

    if last_rain_tip_ms is not None:
        rain_tip_interval_ms = time.ticks_diff(now, last_rain_tip_ms)

    last_rain_tip_ms = now


# ============================================================
# HARDWARE STARTUP
# ============================================================

section("VOGON STARTUP")
print("Machine frequency:", machine.freq())
print("Reset cause:", machine.reset_cause())

section("I2C AND OLED")
print("Creating I2C0: SDA=GP0 SCL=GP1 freq=400000")
i2c = machine.I2C(
    0,
    scl=machine.Pin(1),
    sda=machine.Pin(0),
    freq=400000,
)

i2c_addresses = print_i2c_scan(i2c)
print("Creating OLED at 0x3C...")
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled_message("VOGON DEBUG", "OLED OK")
print("OLED OK")

section("1-WIRE INITIALIZATION")
print("Creating 1-Wire bus on GP{}".format(ONEWIRE_PIN))
ow = onewire.OneWire(machine.Pin(ONEWIRE_PIN))
ds18 = DS18X20(ow)
found_roms = scan_1wire(ds18)
oled_message("1-Wire scan", "Found: {}".format(len(found_roms)))
time.sleep(1)

section("RAIN GAUGE")
print("Loading rain state...")
rain_state = RainState()
try:
    rain_state.load()
    print("Rain state loaded. Tips:", rain_state.rain_count)
except Exception as error:
    print("Rain state load FAILED:", repr(error))

print("Configuring rain IRQ on GP{}".format(RAIN_PIN))
rain_pin = machine.Pin(RAIN_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
rain_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=rain_irq)
print("Rain IRQ OK. Pin value:", rain_pin.value())

section("SHT41 INITIALIZATION")
try:
    sht = SHT41(i2c)
    print("SHT41 object created OK")
except Exception as error:
    print("SHT41 initialization FAILED:", repr(error))
    raise

section("MS5637 INITIALIZATION")
try:
    MS5637 = PiicoDev_MS5637(
        bus=0,
        sda=machine.Pin(0),
        scl=machine.Pin(1),
        freq=100000,
        addr=0x76,
    )
    print("MS5637 object created OK")
except Exception as error:
    print("MS5637 initialization FAILED:", repr(error))
    raise

def wifi_reconnect():
    print("WiFi reconnecting...")

    if wlan.isconnected():
        return True

    wlan.disconnect()
    time.sleep_ms(500)
    wlan.connect(secrets.ssid, secrets.password)

    for attempt in range(20):
        if wlan.isconnected():
            print("WiFi reconnected:", wlan.ifconfig()[0])
            return True
        time.sleep(1)

    print("WiFi reconnect FAILED")
    return False


def mqtt_reconnect():
    global client

    print("MQTT reconnecting...")

    if not wlan.isconnected():
        if not wifi_reconnect():
            client = None
            return False

    if client is not None:
        try:
            client.disconnect()
        except Exception:
            pass

    client = None

    try:
        new_client = MQTTClient(
            "pico_weather",
            MQTT_SERVER,
            keepalive=120
        )
        new_client.connect()
        client = new_client
        print("MQTT reconnected OK")
        return True

    except Exception as error:
        print("MQTT reconnect FAILED:", repr(error))
        client = None
        return False

# ============================================================
# WIFI STARTUP
# ============================================================

section("WIFI")
print("SSID:", secrets.ssid)
wlan = network.WLAN(network.STA_IF)
wlan.active(False)
time.sleep_ms(500)
wlan.active(True)
time.sleep_ms(500)

try:
    wlan.disconnect()
except Exception:
    pass

print("Connecting WiFi...")
wlan.connect(secrets.ssid, secrets.password)

timeout = 30
while timeout > 0 and not wlan.isconnected():
    status = wlan.status()
    print("  WiFi status={} timeout={}".format(status, timeout))
    oled_message("Connecting WiFi", "Status: {}".format(status), "Time: {}".format(timeout))
    timeout -= 1
    time.sleep(1)

if not wlan.isconnected():
    status = wlan.status()
    print("WiFi FAILED. Final status:", status)
    oled_message("WiFi FAILED", "Status: {}".format(status))
    while True:
        time.sleep(1)

print("WiFi OK")
print("  status:", wlan.status())
print("  ifconfig:", wlan.ifconfig())
print("  RSSI:", wlan.status("rssi"))
oled_message("WiFi OK", wlan.ifconfig()[0])
time.sleep(1)


# ============================================================
# MQTT STARTUP
# ============================================================

section("MQTT")
print("MQTT server:", MQTT_SERVER)
print("Creating MQTT client...")
client = MQTTClient("pico_weather", MQTT_SERVER, keepalive=120)

oled_message("Connecting MQTT", str(MQTT_SERVER))
try:
    client.connect()
    print("MQTT OK")
    oled_message("MQTT OK", str(MQTT_SERVER))
except Exception as error:
    print("MQTT FAILED:", repr(error))
    client = None
    oled_message("MQTT FAILED", str(error)[:16])

time.sleep(1)


# ============================================================
# STARTUP SENSOR TEST
# ============================================================

section("STARTUP DS18B20 TEST")
ds_temps = read_ds18b20_sensors(ds18, DS18B20_SENSORS, found_roms)
selected_sensor, ds_temp = select_outdoor_temperature(ds_temps)
temp_box_ds18b20 = ds_temps.get("box")

section("STARTUP SHT41 TEST")
sht_temp, sht_hum = read_sht41_avg(sht, n=1)
print("SHT41 result: temp={} humidity={}".format(sht_temp, sht_hum))

section("STARTUP MS5637 TEST")
try:
    ms_temp, ms_pressure = MS5637.read_temperature_and_pressure()
    print("MS5637 result: temp={} pressure={}".format(ms_temp, ms_pressure))
except Exception as error:
    print("MS5637 read FAILED:", repr(error))
    ms_temp = None
    ms_pressure = None

section("STARTUP MQTT PUBLISH TEST")
if client is not None:
    try:
        client.publish(MQTT_TEST_TOPIC, "HELLO FROM PICO")
        print("Published test message to", MQTT_TEST_TOPIC)
    except Exception as error:
        print("MQTT startup publish FAILED:", repr(error))
        client = None
else:
    print("Skipped: MQTT client is not connected")

section("STARTUP COMPLETE")
print("Initial selected temperature:", ds_temp)
print("Initial selected sensor:", selected_sensor)
print("Entering main loop...")


# ============================================================
# MAIN LOOP VARIABLES
# ============================================================

loop_count = 0

sht_temp_ema = None
humidity_ema = None

WIND_SAMPLE_INTERVAL_MS = 1000
REPORT_INTERVAL_MS = 60_000
RAIN_SAVE_INTERVAL_MS = 60_000

now = time.ticks_ms()

# Första vindprovet görs direkt.
next_wind_sample = now

# Första kompletta rapporten görs efter en hel minut,
# så att vindackumulatorn hinner få cirka 60 prover.
next_report = time.ticks_add(
    now,
    REPORT_INTERVAL_MS
)

next_rain_save = time.ticks_add(
    now,
    RAIN_SAVE_INTERVAL_MS
)


# ============================================================
# MAIN LOOP
# ============================================================

while True:
    now = time.ticks_ms()

    # --------------------------------------------------------
    # VINDPROV VARJE SEKUND
    # --------------------------------------------------------

    if time.ticks_diff(now, next_wind_sample) >= 0:
        next_wind_sample = time.ticks_add(
            next_wind_sample,
            WIND_SAMPLE_INTERVAL_MS
        )

        try:
            wind_data = wind_sensor.read()

            if wind_minute.add_sample(wind_data):
                if DEBUG and wind_data is not None:
                    pass
                    #print(
                        #"Wind sample:",
                        #wind_data["wind_speed"],
                        #"m/s, raw direction:",
                        #wind_data["wind_direction"])
                else:
                    print("Misslyckad vindavläsning")

        except Exception as error:
            print("Wind read FAILED:", repr(error))

    # --------------------------------------------------------
    # SPARA REGNTOTAL PERIODISKT
    # --------------------------------------------------------

    if time.ticks_diff(now, next_rain_save) >= 0:
        next_rain_save = time.ticks_add(
            next_rain_save,
            RAIN_SAVE_INTERVAL_MS
        )

        try:
            rain_state.save()

            if DEBUG:
                print("Rain state saved")

        except Exception as error:
            print("Rain state save FAILED:", repr(error))

    # --------------------------------------------------------
    # KOMPLETT MÄTCYKEL VARJE MINUT
    # --------------------------------------------------------

    if time.ticks_diff(now, next_report) >= 0:
        next_report = time.ticks_add(
            next_report,
            REPORT_INTERVAL_MS
        )

        loop_count += 1

        section("MEASUREMENT CYCLE {}".format(loop_count))
        print("Uptime ms:", now)

        # ----------------------------------------------------
        # Vindminuten är redan insamlad
        # ----------------------------------------------------

        wind = wind_minute.finish_minute()

        if wind is None:
            wind_avg = None
            wind_gust = None
            wind_dir = None
            wind_samples = 0
        else:
            wind_avg = wind["wind_avg"]
            wind_gust = wind["wind_gust"]
            wind_dir = wind["wind_dir"]
            wind_samples = wind["samples"]

        print("Wind samples:", wind_samples)
        print("Wind average:", wind_avg, "m/s")
        print("Wind gust:", wind_gust, "m/s")
        print("Wind direction:", wind_dir, "degrees")

        # ----------------------------------------------------
        # DS18B20
        # ----------------------------------------------------

        # Behåll omskanning medan systemet testas.
        # När allt är stabilt kan found_roms från uppstarten användas.
        if DEBUG:
            found_roms = scan_1wire(ds18)

        ds_temps = read_ds18b20_sensors(
            ds18,
            DS18B20_SENSORS,
            found_roms
        )

        selected_sensor, ds_temp = select_outdoor_temperature(
            ds_temps
        )

        temp_box_ds18b20 = ds_temps.get("box")

        # ----------------------------------------------------
        # Regn
        # ----------------------------------------------------

        # Ta en lokal kopia före nollställningen.
        tips_per_minute = rain_tips_interval
        rain_tips_interval = 0

        rain_interval_mm = (
            tips_per_minute * config.RAIN_MM_PER_TIP
        )

        if (
            tips_per_minute > 0
            and rain_tip_interval_ms is not None
            and rain_tip_interval_ms > 0
        ):
            rain_intensity = (
                config.RAIN_MM_PER_TIP
                * 3_600_000
                / rain_tip_interval_ms
            )
        else:
            rain_intensity = 0.0

        print("Rain tips this cycle:", tips_per_minute)
        print("Rain interval mm:", rain_interval_mm)
        print("Rain intensity mm/h:", rain_intensity)
        print("Rain total tips:", rain_state.rain_count)

        # ----------------------------------------------------
        # SHT41
        # ----------------------------------------------------

        print("Reading SHT41...")
        temp_1, humidity = read_sht41_avg(sht, n=3)

        if temp_1 is not None and humidity is not None:
            if sht_temp_ema is None:
                sht_temp_ema = temp_1
                humidity_ema = humidity
            else:
                alpha = 0.2

                sht_temp_ema = (
                    alpha * temp_1
                    + (1.0 - alpha) * sht_temp_ema
                )

                humidity_ema = (
                    alpha * humidity
                    + (1.0 - alpha) * humidity_ema
                )

            temp_1 = sht_temp_ema
            humidity = humidity_ema

        else:
            print("SHT41 returned no valid measurement")

        # ----------------------------------------------------
        # MS5637
        # ----------------------------------------------------

        print("Reading MS5637...")

        try:
            temp_2, pressure = (
                MS5637.read_temperature_and_pressure()
            )

            print(
                "MS5637: temp={} pressure={}".format(
                    temp_2,
                    pressure
                )
            )

        except Exception as error:
            print("MS5637 read FAILED:", repr(error))
            temp_2 = None
            pressure = None

        # ----------------------------------------------------
        # Summering
        # ----------------------------------------------------

        print("Cycle summary:")
        print("  temp:", ds_temp)
        print("  selected sensor:", selected_sensor)
        print("  box temp:", temp_box_ds18b20)
        print("  SHT41 temp:", temp_1)
        print("  humidity:", humidity)
        print("  MS5637 temp:", temp_2)
        print("  pressure:", pressure)
        print("  wind average:", wind_avg)
        print("  wind gust:", wind_gust)
        print("  wind direction:", wind_dir)

        # ----------------------------------------------------
        # OLED
        # ----------------------------------------------------

        oled.fill(0)
        oled.text("VOGON DEBUG", 0, 0)

        if ds_temp is None:
            oled.text("T: --.-C", 0, 14)
        else:
            oled.text("T: %.1fC" % ds_temp, 0, 14)

        if pressure is None:
            oled.text("P: ----hPa", 0, 26)
        else:
            oled.text("P: %.0fhPa" % pressure, 0, 26)

        if humidity is None:
            oled.text("H: --%%", 0, 38)
        else:
            oled.text("H: %.0f%%" % humidity, 0, 38)

        if wind_avg is None:
            oled.text("W: --.-m/s", 0, 50)
        else:
            oled.text(
                "W: %.1f/%.1f" % (
                    wind_avg,
                    wind_gust
                ),
                0,
                50
            )

        oled.show()

        # ----------------------------------------------------
        # Nätverkskontroll
        # ----------------------------------------------------

        if not wlan.isconnected():
            print("WiFi disconnected before publish")

    # Den gamla MQTT-anslutningen är inte längre pålitlig
            client = None

            wifi_reconnect()

        if client is None:
            mqtt_reconnect()

        # ----------------------------------------------------
        # MQTT
        # ----------------------------------------------------

        data = {
            "temp": ds_temp,
            "temp_selected_sensor": selected_sensor,

            "temp_green_nw": ds_temps.get("green_nw"),
            "temp_red_wnw": ds_temps.get("red_wnw"),
            "temp_blue_ne": ds_temps.get("blue_ne"),
            "temp_purple_ese": ds_temps.get("purple_ese"),
            "temp_box_ds18b20": temp_box_ds18b20,

            "temp_sht": temp_1,
            "temp_ms5637": temp_2,
            "pressure": pressure,
            "humidity": humidity,

            "rain_total": rain_state.mm(
                config.RAIN_MM_PER_TIP
            ),
            "rain_total_tips": rain_state.rain_count,
            "rain_interval": tips_per_minute,
            "rain_interval_mm": rain_interval_mm,
            "rain_intensity": rain_intensity,

            "wind_avg": wind_avg,
            "wind_gust": wind_gust,
            "wind_dir": wind_dir,
            "wind_samples": wind_samples,
        }

        payload = ujson.dumps(data)

        print("MQTT payload:")
        print(payload)

        if client is not None:
            try:
                client.publish(
                    MQTT_TOPIC,
                    payload
                )

                print(
                    "MQTT publish OK to",
                    MQTT_TOPIC
                )

            except Exception as error:
                print(
                    "MQTT publish FAILED:",
                    repr(error)
                )

                client = None

        else:
            print("MQTT publish skipped: no client")

        print("Cycle complete")

    # Loopen går snabbt, men inte helt utan vila.
    time.sleep_ms(10)