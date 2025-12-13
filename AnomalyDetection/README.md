# Anomaly Detection - Sensor Network Extension

Extends the Sensor Network with anomaly detection and faulty sensor identification.

## New Agents

### Detection Agent (`detection_agent.py`)

Monitors sensor readings and averages, publishing alerts when anomalies are detected.
An anomaly is a reading that is more than 2 standard deviations from the average.

**Alert Topic:** `alerts/anomaly`

```bash
python detection_agent.py
```

**Arguments:**
- `--threshold`: Number of standard deviations for anomaly (default: 2.0)
- `--broker`: MQTT broker (default: localhost)
- `--port`: MQTT port (default: 1883)

### Identification Agent (`identification_agent.py`)

Listens for anomaly alerts and sends reset commands to suspected sensors.

**Reset Command Topic:** `commands/reset/<sensor_id>`

```bash
python identification_agent.py
```

### Faulty Sensor (`faulty_sensor.py`)

A sensor that can intentionally send erroneous readings for testing.
Also supports receiving reset commands.

```bash
python faulty_sensor.py --id faulty_001 --zone living_room --type temperature --error-rate 0.3
```

**Arguments:**
- `--error-rate`: Probability of sending erroneous value (0.0-1.0)
- `--error-magnitude`: How far off erroneous values are (in std devs)
- All standard sensor arguments

## Running the Full System

```bash
python start_anomaly_detection.py
```

This starts:
- Multiple normal sensors
- One faulty sensor
- Averaging agents
- Detection agent
- Identification agent
- Interface agent (optional)


