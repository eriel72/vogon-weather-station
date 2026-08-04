# VOGON Weather Station

A home-built weather station built around a Raspberry Pi 5 server and a Raspberry Pi Pico 2 W sensor node.
The project is designed to run unattended for years, collecting high-quality weather data
using affordable and readily available hardware.

The name **VOGON** was inspired by *The Hitchhiker's Guide to the Galaxy*.
One day at work I realized that the Vogons would probably make the worst
meteorologists in the universe — so it seemed like the perfect name for a weather station.

---

# Features

## Sensor Node (Raspberry Pi Pico 2 W)

* DS18B20 1-Wire temperature sensor network
* SHT41 high-precision temperature and humidity sensor
* MS5637 high-resolution barometric pressure sensor
* Industrial RS-485 Modbus wind sensor (XS-WSDS01)

  * Wind speed
  * Gust speed
  * Wind direction
* Tipping bucket rain gauge with interrupt-driven pulse counting
* SSD1306 OLED display for diagnostics and development
* MQTT communication over Wi-Fi
* Legacy support for the BME280 environmental sensor

---

## Server (Raspberry Pi 5)

* MQTT data collection
* SQLite database for recent weather observations
* RRDTool for long-term weather archives
* FastAPI REST API
* Responsive web dashboard
* Historical graphs
* Sea Level Pressure (SLP) calculations
* Wind, rain, temperature, humidity and pressure analysis

---

# Current Hardware

| Component                 | Purpose                              |
| ------------------------- | ------------------------------------ |
| Raspberry Pi Pico 2 W     | Sensor node                          |
| Raspberry Pi 5            | Weather server                       |
| SHT41                     | Air temperature & humidity           |
| MS5637                    | Barometric pressure                  |
| DS18B20                   | Multiple ambient temperature sensors |
| XS-WSDS01 RS-485          | Wind speed & direction               |
| Tipping bucket rain gauge | Rainfall measurement                 |

---

# Project Goals

The goal of the project is to create a modular, reliable, and affordableweather station capable of operating continuously for many years with minimal maintenance.

The project focuses on:

* Accurate environmental measurements
* Long-term weather logging
* Clean and modular software architecture
* Open hardware using widely available components
* Easy expansion with additional sensors
* Educational value for anyone interested in electronics, Python and meteorology

Future ideas include:

* LoRa-connected remote sensor nodes
* Solar radiation and UV measurements
* Air quality monitoring
* "Feels Like" and additional derived weather parameters
* Weather forecasting based on local observations

---

# Data Flow

```text
          Raspberry Pi Pico 2 W
                  │
                  │ MQTT
                  ▼
           Raspberry Pi 5
        ┌───────────────────┐
        │ SQLite            │
        │ RRDTool           │
        │ Weather Processing│
        └───────────────────┘
                  │
               FastAPI
                  │
                  ▼
          Web Dashboard
```

---

# Project Status

🚧 The project is actively developed and continuously improved.

The software is designed to be modular so new sensors and functionality can be added with minimal changes.
While the current focus is on creating a reliable personal weather station, the architecture is intended
to support future expansion and experimentation.




