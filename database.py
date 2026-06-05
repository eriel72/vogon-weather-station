import sqlite3
import config

DB_PATH = config.DB_PATH

conn = sqlite3.connect(
    config.DB_PATH,
    check_same_thread=False
)

conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA busy_timeout=3000;")

cursor = conn.cursor()


def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather (
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        temp REAL,
        humidity REAL,
        pressure REAL,
        pressure_slp REAL,
        dewpoint REAL,
        wind_avg REAL,
        wind_gust REAL,
        wind_dir REAL,
        rain_tip REAL,
        rain_interval_mm REAL,
        rain_total_mm
    )
    """)
    conn.commit()

def insert_weather(
    temp,
    hum,
    press,
    pressure_slp,
    dp,
    wind_avg,
    wind_gust,
    wind_dir,
    rain_tip,
    rain_interval_mm,
    rain_total_mm
):
    cursor.execute("""
        INSERT INTO weather (
            temp,
            humidity,
            pressure,
            pressure_slp,
            dewpoint,
            wind_avg,
            wind_gust,
            wind_dir,
            rain_tip,
            rain_interval_mm,
            rain_total_mm
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        temp,
        hum,
        press,
        pressure_slp,
        dp,
        wind_avg,
        wind_gust,
        wind_dir,
        rain_tip,
        rain_interval_mm,
        rain_total_mm
    ))

    conn.commit()
