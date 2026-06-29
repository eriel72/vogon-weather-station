import sqlite3
import config
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DB_FILE = config.DB_PATH

# Connect SQLite
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
SELECT
    strftime('%H', timestamp),
    SUM(rain_interval_mm)
FROM weather
WHERE timestamp > datetime('now','-24 hours')
GROUP BY strftime('%Y-%m-%d %H', timestamp)
""")
 