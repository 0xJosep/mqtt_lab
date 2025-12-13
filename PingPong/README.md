# Ping-Pong - Two MQTT Clients

Two clients exchanging ping/pong messages via MQTT.

## Design Decision

**Single Topic Architecture**: Both clients use the same topic (`pingpong`). 
Each client filters messages by content - the ping client responds only to "pong" 
messages and vice versa. This design is simpler than two separate topics and 
demonstrates topic-based filtering.

## Usage

### Individual Clients

```bash
# Start ping client (responds to "pong" with "ping")
python pingpong_client.py ping

# Start pong client (responds to "ping" with "pong")
python pingpong_client.py pong
```

### Automated Startup

```bash
# Windows
python start_game.py

# Linux/Mac
./start_game.sh
# or
python start_game.py
```

### Arguments

- `mode`: Either `ping` or `pong`
- `--broker`: MQTT broker address (default: `localhost`)
- `--port`: MQTT broker port (default: `1883`)
- `--topic`: Topic for communication (default: `pingpong`)
- `--initial`: Send initial message to start the game (optional flag)

## Example

```bash
# Terminal 1: Start ping client that initiates the game
python pingpong_client.py ping --initial

# Terminal 2: Start pong client
python pingpong_client.py pong
```


