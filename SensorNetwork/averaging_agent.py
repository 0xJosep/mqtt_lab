#!/usr/bin/env python3
"""
Averaging Agent - Collects sensor readings and computes averages

Subscribes to: sensors/<zone>/<measurement_type>/+
Publishes averages to: averages/<zone>/<measurement_type>
"""

import argparse
import time
import json
import threading
from collections import defaultdict
import paho.mqtt.client as mqtt


class AveragingAgent:
    """Collects sensor readings and computes moving averages."""
    
    def __init__(self, zone: str, measurement_type: str, window: float,
                 interval: float, broker: str, port: int):
        self.zone = zone
        self.measurement_type = measurement_type
        self.window = window  # Time window in seconds
        self.interval = interval  # Publishing interval
        self.broker = broker
        self.port = port
        
        # Topic patterns
        self.subscribe_topic = f"sensors/{zone}/{measurement_type}/+"
        self.publish_topic = f"averages/{zone}/{measurement_type}"
        
        # Storage for readings: {sensor_id: [(timestamp, value), ...]}
        self.readings = defaultdict(list)
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
            print(f"[AVG {self.zone}/{self.measurement_type}] Connected to broker")
            client.subscribe(self.subscribe_topic)
            print(f"[AVG {self.zone}/{self.measurement_type}] Subscribed to: {self.subscribe_topic}")
        else:
            print(f"[AVG {self.zone}/{self.measurement_type}] Connection failed: {reason_code}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Callback when a message is received."""
        self = userdata
        try:
            data = json.loads(msg.payload.decode())
            sensor_id = data.get('sensor_id', 'unknown')
            value = data.get('value')
            timestamp = data.get('timestamp', time.time())
            
            if value is not None:
                with self.lock:
                    self.readings[sensor_id].append((timestamp, value))
                    
        except json.JSONDecodeError as e:
            print(f"[AVG] Failed to parse message: {e}")
    
    def _compute_average(self) -> dict:
        """Compute average over the time window."""
        now = time.time()
        cutoff = now - self.window
        
        all_values = []
        active_sensors = []
        
        with self.lock:
            for sensor_id, readings in self.readings.items():
                # Filter readings within the time window
                valid = [(t, v) for t, v in readings if t >= cutoff]
                self.readings[sensor_id] = valid  # Clean old readings
                
                if valid:
                    sensor_values = [v for _, v in valid]
                    all_values.extend(sensor_values)
                    active_sensors.append(sensor_id)
        
        if not all_values:
            return None
        
        avg = sum(all_values) / len(all_values)
        
        return {
            'zone': self.zone,
            'type': self.measurement_type,
            'average': round(avg, 2),
            'sample_count': len(all_values),
            'sensor_count': len(active_sensors),
            'sensors': active_sensors,
            'timestamp': now
        }
    
    def _publish_loop(self):
        """Periodically publish averages."""
        while self.running:
            time.sleep(self.interval)
            
            result = self._compute_average()
            if result:
                payload = json.dumps(result)
                self.client.publish(self.publish_topic, payload)
                print(f"[AVG {self.zone}/{self.measurement_type}] Average: {result['average']} "
                      f"(from {result['sensor_count']} sensors, {result['sample_count']} samples)")
    
    def run(self):
        """Start the averaging agent."""
        print(f"[AVG {self.zone}/{self.measurement_type}] Starting...")
        print(f"[AVG {self.zone}/{self.measurement_type}] Window: {self.window}s, Interval: {self.interval}s")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Start publishing loop in a thread
            publish_thread = threading.Thread(target=self._publish_loop, daemon=True)
            publish_thread.start()
            
            # Keep running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n[AVG {self.zone}/{self.measurement_type}] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
    
    def stop(self):
        """Stop the agent."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Averaging Agent')
    parser.add_argument('--zone', required=True, help='Zone to monitor')
    parser.add_argument('--type', required=True, dest='measurement_type',
                        help='Measurement type to average')
    parser.add_argument('--window', type=float, default=10.0,
                        help='Time window for averaging (seconds)')
    parser.add_argument('--interval', type=float, default=5.0,
                        help='Publishing interval for averages (seconds)')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    agent = AveragingAgent(
        zone=args.zone,
        measurement_type=args.measurement_type,
        window=args.window,
        interval=args.interval,
        broker=args.broker,
        port=args.port
    )
    agent.run()


if __name__ == "__main__":
    main()


