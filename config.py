# ---------------- MQTT ----------------

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "weather/#"

# ---------------- SQLITE ----------------

DB_PATH = "/home/pi/Documents/Development/weather.db"

# ---------------- RRD ----------------

WEATHER_RRD = "/home/pi/Documents/Development/rrd/weather_env.rrd"
RAIN_RRD    = "/home/pi/Documents/Development/rrd/rain.rrd"
WIND_RRD    = "/home/pi/Documents/Development/rrd/wind.rrd"

# ---------------- RRD SETTINGS ----------------

RRD_MIN_INTERVAL = 1.5

# ---------------- VALIDATION ----------------

TEMP_MIN = -40
TEMP_MAX = 60

HUM_MIN = 0
HUM_MAX = 100

PRESSURE_MIN = 800
PRESSURE_MAX = 1200

# ------------- RAIN GAUGE -------------
RAIN_MM_PER_TIP = 0.2794   # CHANGHE THIS DEPENDING ON YOUR RAIN GAUGE
