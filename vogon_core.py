import json
import paho.mqtt.client as mqtt
import traceback
import config

from validation import dewpoint, valid
from rrd_handler import update_rrd
from database import init_db, insert_weather
from cache import latest_data


WEATHER_RRD = config.WEATHER_RRD
RAIN_RRD    = config.RAIN_RRD
WIND_RRD    = config.WIND_RRD


# ---------------- PIPELINE ----------------
def process_weather(data):
    print("PIPELINE RUNNING")

    temp  = data.get("temp")
    hum   = data.get("humidity")
    press = data.get("pressure")
    

    wind_avg  = data.get("wind_avg")
    wind_gust = data.get("wind_gust")
    wind_dir  = data.get("wind_dir")

    rain_tip   = data.get("rain_interval", 0)
    rain_total = data.get("rain_total", 0)

    dp = dewpoint(temp, hum)
    slp = sea_level_pressure(press, temp)

    rain_mm = round(rain_tip * config.RAIN_MM_PER_TIP, 1)
    rain_total_mm = round(rain_total * config.RAIN_MM_PER_TIP, 1)

    latest_data.clear()
    latest_data.update({
        "temp": temp,
        "humidity": hum,
        "pressure": press,
        "pressure_slp": slp,
        "dewpoint": dp,
        "wind_avg": wind_avg,
        "wind_gust": wind_gust,
        "wind_dir": wind_dir,
        "rain_tip": rain_tip,
        "rain_total": rain_total,
        "rain_interval_mm": rain_mm,
        "rain_total_mm": rain_total_mm
    })

    # ---------------- RRD ----------------
    if temp is not None and hum is not None and press is not None:
        update_rrd(WEATHER_RRD, [temp, hum, press, dp], "WEATHER")

    if rain_mm is not None:
        update_rrd(RAIN_RRD, [rain_mm], "RAIN")

    if wind_avg is not None and wind_gust is not None and wind_dir is not None:
        update_rrd(WIND_RRD, [wind_avg, wind_gust, wind_dir], "WIND")

    # ---------------- SQLITE ----------------
    try:
        insert_weather(
            temp,
            hum,
            press,
            slp,
            dp,
            wind_avg,
            wind_gust,
            wind_dir,
            rain_tip,
            rain_mm,
            rain_total_mm
            )

        print("DB INSERT + COMMIT OK")

    except Exception as e:
        print("DB ERROR:", e)
        traceback.print_exc()


# ---------------- MQTT CALLBACK ----------------
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()

        print("\nMQTT IN")
        print("Topic:", msg.topic)
        print("MQTT RECEIVED:", msg.payload)
        print("CALLBACK ACTIVE")

        data = json.loads(payload)

        if not valid(data):
            print("BAD PACKET (validation failed)")
            return

        print("RAW DATA:", data)

        temp  = data.get("temp")
        hum   = data.get("humidity")
        press = data.get("pressure")
        wind  = data.get("wind_avg")

        if temp is None or hum is None or press is None:
            print("BAD PACKET (missing core values)")
            return

        print(f"T={temp} H={hum} P={press} W={wind}")

        process_weather(data)

    except json.JSONDecodeError:
        print("JSON ERROR:")
        print(msg.payload)

    except Exception:
        print("CALLBACK ERROR TRACE:")
        traceback.print_exc()


# ---------------- MAIN ----------------
print("MQTT ingestion running...")

init_db()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

client.connect(config.MQTT_BROKER, config.MQTT_PORT)
print("MQTT CONNECTED")

client.subscribe(config.MQTT_TOPIC)
print("SUBSCRIBED TO weather/#")

client.loop_forever()