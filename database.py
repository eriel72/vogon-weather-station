import sqlite3
import config

DB_PATH = config.DB_PATH

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
conn.execute("PRAGMA busy_timeout=3000;")

cursor = conn.cursor()


def init_db():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weather (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temp REAL,
            humidity REAL,
            pressure REAL,
            dewpoint REAL,
            wind_avg REAL,
            wind_gust REAL,
            wind_dir REAL,
            rain_tip REAL,
            rain_interval_mm REAL,
            rain_total_mm REAL,
            pressure_slp REAL,
            temp_box_ds18b20 REAL,
            temp_sht REAL,
            temp_ms5637 REAL,
            temp_green_nw REAL,
            temp_red_wnw REAL,
            temp_blue_ne REAL,
            temp_purple_ese REAL,
            temp_selected_sensor TEXT
        )
        """
    )
    conn.commit()


def insert_weather(
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
    rain_total_mm,
    temp_box_ds18b20=None,
    temp_sht=None,
    temp_ms5637=None,
    temp_green_nw=None,
    temp_red_wnw=None,
    temp_blue_ne=None,
    temp_purple_ese=None,
    temp_selected_sensor=None,
):
    cursor.execute(
        """
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
            rain_total_mm,
            temp_box_ds18b20,
            temp_sht,
            temp_ms5637,
            temp_green_nw,
            temp_red_wnw,
            temp_blue_ne,
            temp_purple_ese,
            temp_selected_sensor
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
            rain_total_mm,
            temp_box_ds18b20,
            temp_sht,
            temp_ms5637,
            temp_green_nw,
            temp_red_wnw,
            temp_blue_ne,
            temp_purple_ese,
            temp_selected_sensor,
        ),
    )
    conn.commit()