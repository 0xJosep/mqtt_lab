# MQTT Lab - Multi-Agent Systems

This repository contains solutions for the MQTT Lab exercises from CS534 Multi-Agent Systems course.

## Setup

1. Create a Python virtual environment:
```bash
python -m venv .venv
```

2. Activate the environment:
- Linux/Mac: `source .venv/bin/activate`
- Windows: `.venv\Scripts\activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start an MQTT broker (shiftr.io or mosquitto) on `localhost:1883`

## Project Structure

```
├── FirstClient/          # Exercise 1: Basic MQTT pub/sub
├── PingPong/             # Exercise 2: Two-client ping-pong game
├── SensorNetwork/        # Exercise 3: Sensor network simulation
├── AnomalyDetection/     # Exercise 4: Anomaly detection system
└── ContractNet/          # Exercise 5: Contract Net protocol
```

## Running Exercises

Each directory contains its own README with specific instructions.


