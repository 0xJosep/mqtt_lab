# First Client - Basic MQTT Pub/Sub

A simple MQTT client that connects to a broker, subscribes to a topic, and publishes messages.

## Usage

```bash
python first_client.py [--broker BROKER] [--port PORT] [--topic TOPIC]
```

### Arguments

- `--broker`: MQTT broker address (default: `localhost`)
- `--port`: MQTT broker port (default: `1883`)
- `--topic`: Topic to subscribe/publish to (default: `hello`)

## Example

```bash
# Run with defaults (localhost:1883, topic: hello)
python first_client.py

# Connect to a different broker
python first_client.py --broker test.mosquitto.org --port 1883 --topic mytopic
```

## Behavior

1. Connects to the MQTT broker
2. Subscribes to the specified topic
3. Publishes 5 messages with 2-second intervals
4. Prints all received messages to console


