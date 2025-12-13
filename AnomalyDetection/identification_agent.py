#!/usr/bin/env python3
"""
Identification Agent - Sends reset commands to suspected faulty sensors

Subscribes to: alerts/anomaly
Publishes reset commands to: commands/reset/<sensor_id>
"""

import argparse
import time
import json
from collections import defaultdict
import paho.mqtt.client as mqtt


class IdentificationAgent:
    """Identifies and sends reset commands to faulty sensors."""
    
    def __init__(self, alert_threshold: int, cooldown: float,
                 broker: str, port: int):
        self.alert_threshold = alert_threshold  # Alerts before reset
        self.cooldown = cooldown  # Cooldown between resets for same sensor
        self.broker = broker
        self.port = port
        
        # Track alerts per sensor: {sensor_id: [timestamps]}
        self.alert_counts = defaultdict(list)
        # Track last reset time: {sensor_id: timestamp}
        self.last_reset = {}
        
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
            print(f"[IDENTIFIER] Connected to broker")
            client.subscribe("alerts/anomaly")
            print(f"[IDENTIFIER] Listening for anomaly alerts")
            print(f"[IDENTIFIER] Reset threshold: {self.alert_threshold} alerts, cooldown: {self.cooldown}s")
        else:
            print(f"[IDENTIFIER] Connection failed: {reason_code}")
    
    def _should_reset(self, sensor_id: str) -> bool:
        """Check if a sensor should be reset."""
        now = time.time()
        
        # Check cooldown
        if sensor_id in self.last_reset:
            if now - self.last_reset[sensor_id] < self.cooldown:
                return False
        
        # Count recent alerts (last 60 seconds)
        recent = [t for t in self.alert_counts[sensor_id] if now - t < 60]
        self.alert_counts[sensor_id] = recent
        
        return len(recent) >= self.alert_threshold
    
    def _send_reset(self, sensor_id: str, zone: str, mtype: str):
        """Send a reset command to a sensor."""
        now = time.time()
        
        reset_command = {
            'sensor_id': sensor_id,
            'action': 'reset',
            'reason': 'anomaly_detected',
            'timestamp': now
        }
        
        topic = f"commands/reset/{sensor_id}"
        self.client.publish(topic, json.dumps(reset_command))
        
        self.last_reset[sensor_id] = now
        
        print(f"\n[IDENTIFIER] 🔄 RESET COMMAND SENT")
        print(f"[IDENTIFIER]    Sensor: {sensor_id}")
        print(f"[IDENTIFIER]    Zone: {zone}, Type: {mtype}")
        print(f"[IDENTIFIER]    Topic: {topic}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Callback when an alert is received."""
        self = userdata
        try:
            if msg.topic == "alerts/anomaly":
                data = json.loads(msg.payload.decode())
                sensor_id = data.get('sensor_id')
                zone = data.get('zone', 'unknown')
                mtype = data.get('type', 'unknown')
                timestamp = data.get('timestamp', time.time())
                
                if sensor_id:
                    # Record alert
                    self.alert_counts[sensor_id].append(timestamp)
                    
                    print(f"[IDENTIFIER] Alert received for {sensor_id} "
                          f"({len(self.alert_counts[sensor_id])} recent alerts)")
                    
                    # Check if reset is needed
                    if self._should_reset(sensor_id):
                        self._send_reset(sensor_id, zone, mtype)
                    
        except json.JSONDecodeError:
            pass
    
    def run(self):
        """Start the identification agent."""
        print("[IDENTIFIER] Starting...")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[IDENTIFIER] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
    
    def stop(self):
        """Stop the agent."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Identification Agent')
    parser.add_argument('--threshold', type=int, default=3,
                        help='Number of alerts before sending reset')
    parser.add_argument('--cooldown', type=float, default=30.0,
                        help='Cooldown between resets for same sensor (seconds)')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    agent = IdentificationAgent(
        alert_threshold=args.threshold,
        cooldown=args.cooldown,
        broker=args.broker,
        port=args.port
    )
    agent.run()


if __name__ == "__main__":
    main()


