#!/usr/bin/env python3
"""
BOUKHRISS Youssef - Icho Ibrahim
Detection Agent - Monitors sensor readings and detects anomalies

Subscribes to:
- sensors/+/+/+ (all sensor readings)
- averages/+/+ (all averages)

Publishes alerts to: alerts/anomaly

An anomaly is detected when a reading is more than N standard deviations
from the current average.
"""

import argparse
import time
import json
import threading
import math
from collections import defaultdict
import paho.mqtt.client as mqtt


class DetectionAgent:
    """Detects anomalies in sensor readings."""
    
    def __init__(self, threshold: float, broker: str, port: int):
        self.threshold = threshold  # Number of standard deviations
        self.broker = broker
        self.port = port
        
        # Store recent readings per zone/type for std dev calculation
        # {(zone, type): [(sensor_id, value, timestamp), ...]}
        self.readings = defaultdict(list)
        # Store latest averages: {(zone, type): average}
        self.averages = {}
        self.lock = threading.Lock()
        
        # Time window for std dev calculation (seconds)
        self.window = 30
        
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
            print(f"[DETECTOR] Connected to broker")
            client.subscribe("sensors/+/+/+")
            client.subscribe("averages/+/+")
            print(f"[DETECTOR] Monitoring for anomalies (threshold: {self.threshold} σ)")
        else:
            print(f"[DETECTOR] Connection failed: {reason_code}")
    
    def _compute_stats(self, zone: str, mtype: str) -> tuple:
        """Compute mean and standard deviation for a zone/type."""
        key = (zone, mtype)
        now = time.time()
        cutoff = now - self.window
        
        with self.lock:
            # Get recent readings
            readings = [(sid, val, ts) for sid, val, ts in self.readings[key]
                        if ts >= cutoff]
            self.readings[key] = readings
            
            if len(readings) < 2:
                return None, None
            
            values = [val for _, val, _ in readings]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = math.sqrt(variance) if variance > 0 else 0.001
            
            return mean, std_dev
    
    def _check_anomaly(self, sensor_id: str, zone: str, mtype: str, value: float):
        """Check if a reading is anomalous."""
        mean, std_dev = self._compute_stats(zone, mtype)
        
        if mean is None or std_dev is None:
            return  # Not enough data
        
        # Calculate Z-score
        z_score = abs(value - mean) / std_dev if std_dev > 0 else 0
        
        if z_score > self.threshold:
            # Anomaly detected!
            alert = {
                'sensor_id': sensor_id,
                'zone': zone,
                'type': mtype,
                'value': value,
                'expected_mean': round(mean, 2),
                'std_dev': round(std_dev, 2),
                'z_score': round(z_score, 2),
                'timestamp': time.time()
            }
            
            print(f"\n[DETECTOR] ⚠️  ANOMALY DETECTED!")
            print(f"[DETECTOR]    Sensor: {sensor_id}")
            print(f"[DETECTOR]    Zone: {zone}, Type: {mtype}")
            print(f"[DETECTOR]    Value: {value} (expected: {mean:.2f} ± {std_dev:.2f})")
            print(f"[DETECTOR]    Z-score: {z_score:.2f} (threshold: {self.threshold})")
            
            # Publish alert
            self.client.publish("alerts/anomaly", json.dumps(alert))
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Callback when a message is received."""
        self = userdata
        try:
            topic_parts = msg.topic.split('/')
            data = json.loads(msg.payload.decode())
            
            if topic_parts[0] == 'sensors' and len(topic_parts) >= 4:
                # Sensor reading
                zone = topic_parts[1]
                mtype = topic_parts[2]
                sensor_id = topic_parts[3]
                value = data.get('value')
                timestamp = data.get('timestamp', time.time())
                
                if value is not None:
                    # Store reading
                    with self.lock:
                        self.readings[(zone, mtype)].append((sensor_id, value, timestamp))
                    
                    # Check for anomaly
                    self._check_anomaly(sensor_id, zone, mtype, value)
            
            elif topic_parts[0] == 'averages' and len(topic_parts) >= 3:
                # Store average
                zone = topic_parts[1]
                mtype = topic_parts[2]
                avg = data.get('average')
                with self.lock:
                    self.averages[(zone, mtype)] = avg
                    
        except json.JSONDecodeError:
            pass
    
    def run(self):
        """Start the detection agent."""
        print("[DETECTOR] Starting anomaly detection...")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[DETECTOR] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
    
    def stop(self):
        """Stop the agent."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Detection Agent')
    parser.add_argument('--threshold', type=float, default=2.0,
                        help='Anomaly threshold in standard deviations')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    agent = DetectionAgent(
        threshold=args.threshold,
        broker=args.broker,
        port=args.port
    )
    agent.run()


if __name__ == "__main__":
    main()


