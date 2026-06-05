import sqlite3
import config

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="VOGON Weather API")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/api/live")
def live_weather():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
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
        FROM weather
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()
    
    if row is None:
        return {"error": "no weather data"}
    
    return dict(row)

@app.get("/api/history/env")
def history_env(hours: int = 24):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            temp,
            humidity,
            pressure,
            pressure_slp,
            dewpoint
        FROM weather
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    """, (f"-{hours} hours",))

    rows = cur.fetchall()
    conn.close()

    return {
        "hours": hours,
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }

@app.get("/api/history/wind")
def history_wind(hours: int = 24):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            wind_avg,
            wind_gust,
            wind_dir
        FROM weather
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    """, (f"-{hours} hours",))

    rows = cur.fetchall()
    conn.close()

    return {
        "hours": hours,
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }


@app.get("/api/history/rain")
def history_rain(hours: int = 24):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            COALESCE(rain_tip, 0) AS rain_tip,
            COALESCE(rain_interval_mm, 0) AS rain_interval_mm,
            COALESCE(rain_total_mm, 0) AS rain_total_mm
        FROM weather
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    """, (f"-{hours} hours",))

    rows = cur.fetchall()
    conn.close()

    return {
        "hours": hours,
        "count": len(rows),
        "data": [dict(row) for row in rows]
    }

@app.get("/api/trend/pressure")
def pressure_trend(hours: int = 6):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT timestamp, COALESCE(pressure_slp, pressure) AS pressure_slp
        FROM weather
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    latest = cur.fetchone()

    cur.execute("""
    SELECT timestamp, COALESCE(pressure_slp, pressure) AS pressure_slp
        FROM weather
        WHERE timestamp <= datetime('now', ?)
        ORDER BY timestamp DESC
        LIMIT 1
    """, (f"-{hours} hours",))
    old = cur.fetchone()

    cur.execute("""
    SELECT
        MAX(COALESCE(pressure_slp, pressure)) as pmax,
        MIN(COALESCE(pressure_slp, pressure)) as pmin
        FROM weather
        WHERE timestamp >= datetime('now','-24 hours')
    """)
    stats = cur.fetchone()
    
    conn.close()

    if latest is None or old is None:
        return {"error": "not enough data"}

    delta = latest["pressure_slp"] - old["pressure_slp"]

    if delta > 2:
        arrow = "↑"
        text = "Rising"
    elif delta > 0.5:
        arrow = "↗"
        text = "Rising slowly"
    elif delta < -2:
        arrow = "↓"
        text = "Falling"
    elif delta < -0.5:
        arrow = "↘"
        text = "Falling slowly"
    else:
        arrow = "→"
        text = "Stable"

    return {
    "hours": hours,
    "latest": latest["pressure_slp"],
    "old": old["pressure_slp"],
    "delta": round(delta, 1),
    "arrow": arrow,
    "text": text,

    "pmax": round(stats["pmax"], 1),
    "pmin": round(stats["pmin"], 1),

    "delta24": round(
        latest["pressure_slp"] - stats["pmax"],
        1
    )
}
@app.get("/api/rain/summary")
def rain_summary():
    conn = get_db()
    cur = conn.cursor()

    # 24h total
    cur.execute("""
        SELECT
            COALESCE(SUM(rain_interval_mm), 0) AS rain_24h
        FROM weather
        WHERE timestamp >= datetime('now', '-24 hours')
    """)

    rain24 = cur.fetchone()["rain_24h"]

    # 1h total
    cur.execute("""
        SELECT
            COALESCE(SUM(rain_interval_mm), 0) AS rain_1h
        FROM weather
        WHERE timestamp >= datetime('now', '-1 hour')
    """)

    rain1h = cur.fetchone()["rain_1h"]

    conn.close()

    return {
        "rain_24h": round(rain24, 1),
        "rain_1h": round(rain1h, 1)
    }
