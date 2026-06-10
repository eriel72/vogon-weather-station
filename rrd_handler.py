
import subprocess
import threading
import time
import config

rrd_lock = threading.Lock()
_last_rrd_time = {}

RRD_MIN_INTERVAL = config.RRD_MIN_INTERVAL


def update_rrd(rrd_file, values, label):
    global _last_rrd_time

    # ---------------- THROTTLE ----------------
    now = time.time()
    last = _last_rrd_time.get(rrd_file, 0)
    if now - last < RRD_MIN_INTERVAL:
        return

    _last_rrd_time[rrd_file] = now

    rrd_string = "N:" + ":".join(str(v) for v in values)

    # ---------------- RETRY ----------------
    for i in range(3):
        result = subprocess.run(
            ["rrdtool", "update", rrd_file, rrd_string],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return

        if "could not lock" in result.stderr:
            time.sleep(0.3)
            continue

        print(f"[RRD ERROR {label}] {result.stderr}")
        return