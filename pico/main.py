# VOGON BUREAU OF METROLOGY
# WEATHER STATION CORE v2 (RRD READY)

import machine
import time
import ujson
import network
import secrets
import utime


from bme280 import BME280
from SSD1306 import SSD1306_I2C
from ads1115 import ADS1115
from ds18x20 import DS18X20
from OneWireTemp import ONEWIRETEMP
from state import RainState
from umqtt.simple import MQTTClient

#--------------------------
# LOAD RAIN COUNT
#

RAIN_FILE = "rain.json"


try:
    with open(RAIN_FILE, "r") as f:
        data = ujson.loads(f.read())

    if isinstance(data, dict):
        rain_total = data.get("rain_count", 0)
    else:
        rain_total = data

except:
    rain_total = 0
    
# -----------------------------
# FUNCTIONS
# -----------------------------

def wifi_reconnect():
    if wlan.isconnected():
        return True

    print("WiFi lost - reconnecting...")

    wlan.disconnect()
    time.sleep(1)
    wlan.connect(secrets.ssid, secrets.password)

    t0 = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), t0) > 10000:
            print("WiFi reconnect timeout")
            return False
        time.sleep(1)

    print("WiFi reconnected:", wlan.ifconfig())
    return True

def mqtt_reconnect():
    global client

    try:
        print("Reconnecting MQTT...")

        client = MQTTClient(
            "pico_weather",
            secrets.MQTT_SERVER
        )

        client.connect()

        print("MQTT reconnected")
        return True

    except Exception as e:
        print("MQTT reconnect failed:", e)
        client = None
        return False

def mqtt_publish_safe(client, topic, payload):
    try:
        client.publish(topic, payload)
    except:
        try:
            client.connect()
            client.publish(topic, payload)
        except Exception as e:
            print("MQTT reconnect failed:", e)


def get_ds_temp(temp1wire):
    global last_temp

    temps = temp1wire.read_all()

    if not temps:
        return last_temp

    valid = [t for t in temps if -35 < t < 50 and t !=85.0 ]
    if not valid:
        return last_temp

    raw = min(valid)

    if last_temp is not None and abs(raw - last_temp) > 5:
        return last_temp

    last_temp = raw
    return raw


def smooth_wind(v):
    wind_history.append(v)
    if len(wind_history) > 5:
        wind_history.pop(0)
    return sum(wind_history) / len(wind_history)

def rain_irq(pin):
    global rain_interval, rain_total, last_rain_irq

    now = time.ticks_ms()

    if time.ticks_diff(now, last_rain_irq) < 150:
        return

    last_rain_irq = now

    rain_interval += 1
    rain_total += 1

def ds_start(temp1wire):
    temp1wire.update()

# -----------------------------
# INIT HARDWARE
# -----------------------------

i2c = machine.I2C(0, scl=machine.Pin(1), sda=machine.Pin(0), freq=100000)

oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
oled.fill(0)
oled.text("Booting...", 0, 0)
oled.show()

temp1wire = ONEWIRETEMP(machine.Pin(13))
rain_pin = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)

#---------------------------
# IRQ
#---------------------------

rain_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=rain_irq)

#---------------------------
# I2C addresses
#---------------------------

sensor = BME280(i2c=i2c, address=0x77)
adc = ADS1115(i2c, address=0x48, gain=ADS1115.GAIN_2_048V)


# -----------------------------
# WIFI
# -----------------------------

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.ssid, secrets.password)

timeout = 30

while timeout > 0:

    if wlan.isconnected():
        break

    status = wlan.status()

    oled.fill(0)
    oled.text("Connecting WiFi", 0, 0)
    oled.text("Status:%d" % status, 0, 16)
    oled.show()

    timeout -= 1
    time.sleep(1)

if not wlan.isconnected():
    oled.fill(0)
    oled.text("WiFi FAILED", 0, 0)
    oled.show()

    machine.reset()

print("WiFi OK:", wlan.ifconfig())


# -----------------------------
# MQTT
# -----------------------------
client = MQTTClient("pico_weather", "192.168.1.160")

try:
    print("Connecting MQTT...")
    client.connect()
    print("MQTT OK")
except Exception as e:
    print("MQTT failed:", e)
    client = None



# -----------------------------
# VARIABLES
# -----------------------------

ds_request_time = 0
ds_ready = False
ds_temp = None

loop_count = 0
minute_counter = 0
history = []
wind_history = []
wind_samples = []

rain_interval = 0
wind_gust = 0

last_temp = None

wind_gust = 0

LOOP_INTERVAL = 60000
last_loop = time.ticks_ms() - LOOP_INTERVAL

WIND_SAMPLE_INTERVAL = 1000
last_wind_sample = 0

last_rain_save = time.ticks_ms()
SAVE_INTERVAL = 10000  # 10 sekunder i ms

last_rain_irq = 0

# --------
# Time start up
# ---------

print("A: start loop")
t0 = utime.ticks_ms()

ds_temp = get_ds_temp(temp1wire)
print("B: temp done", utime.ticks_diff(utime.ticks_ms(), t0))

t1 = utime.ticks_ms()

t, p, h = sensor.read()
print("C: bme done", utime.ticks_diff(utime.ticks_ms(), t1))

client.publish("test/topic", "HELLO FROM PICO")
print("PUBLISHED TEST")



# -----------------------------
# MAIN LOOP
# -----------------------------

while True:

    now = time.ticks_ms()
    loop_count += 1

    # ---------------- WIND SAMPLE ----------------
    if time.ticks_diff(now, last_wind_sample) > WIND_SAMPLE_INTERVAL:

        last_wind_sample = now

        raw_v = adc.read_average(0)

        wind = (raw_v / 2.0) * 32.0
        wind = smooth_wind(wind)

        wind_samples.append(wind)

        if wind > wind_gust:
            wind_gust = wind

    # ---------------- DS18B20 NON-BLOCKING ----------------
    if not ds_ready:
        # vänta ~1000ms efter start
        if time.ticks_diff(now, ds_request_time) > 1000:
            
            ds_temp = get_ds_temp(temp1wire)
            
            ds_ready = True

    # ---------------- MAIN LOOP (60s cycle) ----------------
    if time.ticks_diff(now, last_loop) > LOOP_INTERVAL:

        last_loop = now

        # restart DS conversion direkt (NON-BLOCKING)
        temp1wire.start()
        ds_request_time = now
        ds_ready = False

        # ---------- WIND ----------
        wind_avg = sum(wind_samples) / len(wind_samples) if wind_samples else 0

        # ---------- BME280 ----------
        t, p, h = sensor.read()

        if t is None:
            print("BME read failed")
            continue

        bme_press = float(p) / 100
        bme_hum = float(h)

        wind_dir = 0

        # ---------- RAIN SAVE ----------
        if time.ticks_diff(now, last_rain_save) >= SAVE_INTERVAL:
            last_rain_save = now

            with open(RAIN_FILE, "w") as f:
                f.write(ujson.dumps(rain_total))

        # ---------- DEBUG ----------
        print("Temp:", ds_temp)
        print("Pressure:", bme_press)
        print("Humidity:", bme_hum)
        print("Wind avg:", wind_avg)
        print("Wind gust:", wind_gust)
        print("Loops:", loop_count)
        print("-----")

        # ---------- OLED ----------
        oled.fill(0)
        oled.text("Weather Station", 0, 0)
        oled.text("T: %.1fC" % (ds_temp if ds_temp else 0), 0, 16)
        oled.text("P: %.0fhPa" % bme_press, 0, 28)
        oled.text("H: %.0f%%" % bme_hum, 0, 40)
        oled.text("L:%d" % loop_count, 0, 52)
        oled.show()

        minute_counter += 1

        # ---------- MQTT ----------
        if not wlan.isconnected():
            if not wifi_reconnect():
                continue

        if client is None:
            mqtt_reconnect()

        if client is None:
            continue

        data = {
            "temp": ds_temp,
            "pressure": bme_press,
            "humidity": bme_hum,
            "wind_avg": wind_avg,
            "wind_gust": wind_gust,
            "wind_dir": wind_dir,
            "rain_interval": rain_interval,
            "rain_total": rain_total
        }

        try:
            client.publish("weather/data", ujson.dumps(data))
        except Exception as e:
            print("MQTT publish failed:", e)
            client = None

        # ---------- RESET ----------
        wind_samples = []
        wind_gust = 0
        rain_interval = 0

    time.sleep_ms(10)