import requests
from config import (
    TEMPERATUR_NU_ENABLED,
    TEMPERATUR_NU_HASH,
    TEMPERATUR_NU_URL,
)

def send_temperature(temp):
    if not TEMPERATUR_NU_ENABLED:
        return

    try:
        response = requests.get(
            TEMPERATUR_NU_URL,
            params={
                "hash": TEMPERATUR_NU_HASH,
                "t": f"{temp:.1f}"
            },
            timeout=10,
        )

        if response.status_code == 200:
            print("temperatur.nu OK")
        else:
            print(f"temperatur.nu svarade {response.status_code}")

    except Exception as e:
        print(f"temperatur.nu fel: {e}")