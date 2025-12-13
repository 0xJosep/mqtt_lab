#!/usr/bin/env python3
"""
Ping-Pong MQTT Client

A client that can behave as either a 'ping' or 'pong' player.
- Ping player: responds to "pong" messages with "ping"
- Pong player: responds to "ping" messages with "pong"

Design: Uses a single topic. Each client filters incoming messages
and only responds to the opposite type.
"""

import argparse
import time
import paho.mqtt.client as mqtt


class PingPongClient:
    """MQTT client for the ping-pong game."""
    
    def __init__(self, mode: str, broker: str, port: int, topic: str):
        self.mode = mode  # 'ping' or 'pong'
        self.broker = broker
        self.port = port
        self.topic = topic
        
        # What message I send and what message I respond to
        self.my_message = mode  # 'ping' or 'pong'
        self.listen_for = 'pong' if mode == 'ping' else 'ping'
        
        # Create MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=self)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
    
    @staticmethod
    def _on_connect(client, userdata, flags, reason_code, properties):
        """Callback when connected to broker."""
        self = userdata
        if reason_code == 0:
            print(f"[{self.mode.upper()}] Connected to broker")
            client.subscribe(self.topic)
            print(f"[{self.mode.upper()}] Subscribed to '{self.topic}', listening for '{self.listen_for}'")
        else:
            print(f"[{self.mode.upper()}] Connection failed: {reason_code}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Callback when a message is received."""
        self = userdata
        message = msg.payload.decode()
        
        # Only respond to the message type we're listening for
        if message == self.listen_for:
            print(f"[{self.mode.upper()}] Received: {message}")
            time.sleep(0.5)  # Small delay before responding
            print(f"[{self.mode.upper()}] Sending: {self.my_message}")
            client.publish(self.topic, self.my_message)
    
    def run(self, send_initial: bool = False):
        """Start the client and run the game loop."""
        print(f"[{self.mode.upper()}] Connecting to {self.broker}:{self.port}...")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            time.sleep(1)
            
            # Optionally send initial message to start the game
            if send_initial:
                print(f"[{self.mode.upper()}] Starting game with: {self.my_message}")
                self.client.publish(self.topic, self.my_message)
            
            # Keep running
            print(f"[{self.mode.upper()}] Game running (Ctrl+C to exit)...")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n[{self.mode.upper()}] Shutting down...")
        finally:
            self.client.loop_stop()
            self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Ping-Pong MQTT Client')
    parser.add_argument('mode', choices=['ping', 'pong'], help='Client mode: ping or pong')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='pingpong', help='Topic for communication')
    parser.add_argument('--initial', action='store_true', help='Send initial message to start game')
    args = parser.parse_args()
    
    client = PingPongClient(args.mode, args.broker, args.port, args.topic)
    client.run(send_initial=args.initial)


if __name__ == "__main__":
    main()


