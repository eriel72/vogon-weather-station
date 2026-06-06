import time
from machine import Pin
import onewire
import ds18x20

datapin = Pin(2)
ow = onewire.OneWire(datapin)
ds = ds18x20.DS18X20(ow)

roms = ds.scan()
print("Hittade:", roms)

history = []
HISTORY_LEN = 10  # ~10 minuter smoothing

def median(values):
    s = sorted(values)
    return s[len(s)//2]

def read_all():
    ds.convert_temp()
    time.sleep_ms(750)
    temps = [ds.read_temp(rom) for rom in roms]

    # Filtrera bort uppenbara fel
    temps = [t for t in temps if -40 < t < 60]

    return temps


while True:
    temps = read_all()

    if not temps:
        print("Inga giltiga värden")
        time.sleep(60)
        continue

    med = median(temps)
    tmin = min(temps)

    # Tillåt min om den inte avviker för mycket
    if abs(tmin - med) < 2:
        selected = tmin
    else:
        selected = med

    # Glidande medelvärde
    history.append(selected)
    if len(history) > HISTORY_LEN:
        history.pop(0)

    final_temp = sum(history) / len(history)

    print(f"Rapporterar: {final_temp:.2f} C")

    # 👉 Här skickar du till temperatur.nu
    # send_temp(final_temp)

    time.sleep(60)