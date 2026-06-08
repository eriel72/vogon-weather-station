VOGON Weather Station

A home-built weather station based on a Raspberry Pi server and a Raspberry Pi Pico 2 W sensor node.

Features
Sensor Node (Raspberry Pi Pico 2 W)
DS18B20 (1-Wire) temperature sensors
BME280 temperature, humidity, and pressure sensor
ADS1115 16-bit ADC
SSD1306 OLED display
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
