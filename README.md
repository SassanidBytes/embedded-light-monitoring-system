# Embedded Light Monitoring System

## Overview

Small project to measure and display light intensity in real time using an RP2040 and an OPT4048 sensor.

The microcontroller sends the data to a Python (PyQt6) desktop app where it is shown in a simple GUI.

## Technologies

* RP2040 (Feather)
* OPT4048
* C / Arduino
* Python (PyQt6)

## Features

* Reads sensor data
* Sends data via serial
* Displays values in real time

## Setup

```bash
pip install pyqt6
python opt4048_gui.py
```

## Notes

Built to learn embedded systems and basic GUI development.
