#!/usr/bin/env python3
"""
Interface Agent - Displays sensor network data

Subscribes to:
- sensors/+/+/+ (all sensor readings)
- averages/+/+ (all averages)

Displays the data grouped by zone and measurement type.
"""

import argparse
import time
import json
import threading
import os
from collections import defaultdict
import paho.mqtt.client as mqtt


class InterfaceAgent:
    """Displays sensor network information in real-time."""
    
    def __init__(self, broker: str, port: int, gui: bool = False):
        self.broker = broker
        self.port = port
        self.gui = gui
        
        # Data storage
        # Structure: {zone: {measurement_type: {sensor_id: (value, timestamp)}}}
        self.sensors = defaultdict(lambda: defaultdict(dict))
        # Structure: {zone: {measurement_type: (average, timestamp)}}
        self.averages = defaultdict(dict)
        self.lock = threading.Lock()
        
        # MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=self)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        self.running = True
    
    @staticmethod
    def _on_connect(client, userdata, flags, reason_code, properties):
        """Callback when connected."""
        self = userdata
        if reason_code == 0:
            print("[INTERFACE] Connected to broker")
            # Subscribe to all sensors and averages
            client.subscribe("sensors/+/+/+")
            client.subscribe("averages/+/+")
            print("[INTERFACE] Subscribed to sensors and averages topics")
        else:
            print(f"[INTERFACE] Connection failed: {reason_code}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Callback when a message is received."""
        self = userdata
        try:
            topic_parts = msg.topic.split('/')
            data = json.loads(msg.payload.decode())
            
            with self.lock:
                if topic_parts[0] == 'sensors' and len(topic_parts) >= 4:
                    # Sensor reading: sensors/zone/type/id
                    zone = topic_parts[1]
                    mtype = topic_parts[2]
                    sensor_id = topic_parts[3]
                    value = data.get('value')
                    timestamp = data.get('timestamp', time.time())
                    self.sensors[zone][mtype][sensor_id] = (value, timestamp)
                    
                elif topic_parts[0] == 'averages' and len(topic_parts) >= 3:
                    # Average: averages/zone/type
                    zone = topic_parts[1]
                    mtype = topic_parts[2]
                    avg = data.get('average')
                    timestamp = data.get('timestamp', time.time())
                    sensor_count = data.get('sensor_count', 0)
                    self.averages[zone][mtype] = (avg, timestamp, sensor_count)
                    
        except json.JSONDecodeError:
            pass
    
    def _display_console(self):
        """Display data on console."""
        # Clear screen (cross-platform)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 70)
        print("                    SENSOR NETWORK MONITOR")
        print("=" * 70)
        print(f"  Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        with self.lock:
            zones = sorted(set(list(self.sensors.keys()) + list(self.averages.keys())))
            
            if not zones:
                print("\n  No data received yet. Waiting for sensors...")
            
            for zone in zones:
                print(f"\n  📍 ZONE: {zone.upper()}")
                print("  " + "-" * 50)
                
                # Collect all measurement types for this zone
                types = sorted(set(
                    list(self.sensors.get(zone, {}).keys()) +
                    list(self.averages.get(zone, {}).keys())
                ))
                
                for mtype in types:
                    print(f"\n    📊 {mtype.capitalize()}")
                    
                    # Show average if available
                    if zone in self.averages and mtype in self.averages[zone]:
                        avg, ts, count = self.averages[zone][mtype]
                        age = int(time.time() - ts)
                        print(f"       ➤ Average: {avg:.2f} ({count} sensors, {age}s ago)")
                    
                    # Show individual sensors
                    if zone in self.sensors and mtype in self.sensors[zone]:
                        for sensor_id, (value, ts) in sorted(self.sensors[zone][mtype].items()):
                            age = int(time.time() - ts)
                            status = "🟢" if age < 10 else "🟡" if age < 30 else "🔴"
                            print(f"       {status} {sensor_id}: {value:.2f} ({age}s ago)")
        
        print("\n" + "=" * 70)
        print("  Press Ctrl+C to exit")
    
    def _display_loop(self):
        """Periodically update the display."""
        while self.running:
            self._display_console()
            time.sleep(2)  # Refresh every 2 seconds
    
    def run(self):
        """Start the interface agent."""
        print("[INTERFACE] Starting...")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Start display loop
            self._display_loop()
                
        except KeyboardInterrupt:
            print("\n[INTERFACE] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
    
    def stop(self):
        """Stop the agent."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Interface Agent')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    agent = InterfaceAgent(broker=args.broker, port=args.port)
    agent.run()


if __name__ == "__main__":
    main()


