# Sensor Network - Multi-Agent Sensor Simulation

A dynamic sensor network simulation with multiple types of agents communicating via MQTT.

## Architecture

### Topic Structure

Sensors publish on: `sensors/<zone>/<measurement_type>/<sensor_id>`
- Example: `sensors/living_room/temperature/sensor_001`

Averages published on: `averages/<zone>/<measurement_type>`
- Example: `averages/living_room/temperature`

## Agents

### 1. Sensor Agent (`sensor_agent.py`)

Emits sensor readings at regular intervals following a sinusoidal pattern.

```bash
python sensor_agent.py --id sensor_001 --zone living_room --type temperature --interval 2
```

**Arguments:**
- `--id`: Unique sensor identifier
- `--zone`: Zone/room where sensor is located
- `--type`: Measurement type (temperature, humidity, pressure)
- `--interval`: Publishing interval in seconds (default: 2)
- `--base-value`: Base value for measurements (default: varies by type)
- `--amplitude`: Amplitude of variation (default: 5)
- `--broker`: MQTT broker (default: localhost)
- `--port`: MQTT port (default: 1883)

### 2. Averaging Agent (`averaging_agent.py`)

Collects readings from sensors and computes moving averages.

```bash
python averaging_agent.py --zone living_room --type temperature --window 10 --interval 5
```

**Arguments:**
- `--zone`: Zone to monitor
- `--type`: Measurement type to average
- `--window`: Time window in seconds for averaging (default: 10)
- `--interval`: Publishing interval for averages (default: 5)
- `--broker`: MQTT broker (default: localhost)
- `--port`: MQTT port (default: 1883)

### 3. Interface Agent (`interface_agent.py`)

Displays averages and sensor data in real-time.

```bash
python interface_agent.py
```

**Arguments:**
- `--broker`: MQTT broker (default: localhost)
- `--port`: MQTT port (default: 1883)

## Automated Startup

Run the complete simulation with dynamic agent spawning:

```bash
python start_network.py
```

This will start:
- Multiple sensors in different zones
- Averaging agents for each zone/type combination
- One interface agent
- Dynamic spawning/removal of agents over time


