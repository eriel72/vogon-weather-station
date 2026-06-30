VOGON Weather Station

A home-built weather station based on a Raspberry Pi server and a Raspberry Pi Pico 2 W sensor node.
Designed to run unattended for years while collecting high-quality weather data using affordable, readily available hardware.

I came up with the project name one day at work. As a young man I read The Hitchhiker's Guide to the Galaxy,
and I thought the Vogons would probably make the worst meteorologists in the universe.


Features
Sensor Node (Raspberry Pi Pico 2 W)
DS18B20 (1-Wire) temperature sensors
Legacy support for the BME280 environmental sensor
ADS1115 16-bit ADC
SSD1306 OLED display (for debugging during development)
SHT41 precision temperature and humidity sensor
MS5637 high-resolution pressure sensor
Rain gauge using interrupt-driven pulse counting
MQTT communication over Wi-Fi
Server (Raspberry Pi)
MQTT data collection
SQLite database for recent weather data
RRDTool for long-term data storage
FastAPI-based REST API
Web dashboard with live weather data and historical graphs
Sea Level Pressure (SLP) calculations
Wind, rain, temperature, humidity, and pressure monitoring

Project Goals

The goal of the project is to build a modular weather station using affordable hardware
while providing long-term weather logging, data visualization, and future expansion
possibilities such as LoRa communication, additional sensor nodes, and advanced weather analysis.
The project is under continuous development. The original BME280 support is still included
for users who prefer a single integrated environmental sensor instead of the SHT41/MS5637 combination.

The data flow


Pico 2 W
  ↓ MQTT
Raspberry Pi 5
  ↓
SQLite + RRD
  ↓
FastAPI
  ↓
Web Dashboard



