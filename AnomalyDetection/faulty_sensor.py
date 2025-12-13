#!/usr/bin/env python3
"""
BOUKHRISS Youssef - Icho Ibrahim
Faulty Sensor - A sensor that can send erroneous readings

This sensor is used for testing anomaly detection.
It can intentionally send values far from normal.
It also listens for reset commands and resets its state when received.
"""

import argparse
import time
import math
import json
import random
import paho.mqtt.client as mqtt


class FaultySensor:
    """A sensor that can send faulty readings for testing."""
    
    DEFAULT_VALUES = {
        'temperature': 22.0,
        'humidity': 50.0,
        'pressure': 1013.25,
    }
    
    def __init__(self, sensor_id: str, zone: str, measurement_type: str,
                 interval: float, base_value: float, amplitude: float,
                 error_rate: float, error_magnitude: float,
                 broker: str, port: int):
        self.sensor_id = sensor_id
        self.zone = zone
        self.measurement_type = measurement_type
        self.interval = interval
        self.base_value = base_value
        self.amplitude = amplitude
        self.error_rate = error_rate
        self.error_magnitude = error_magnitude
        self.broker = broker
        self.port = port
        
        # Topics
        self.publish_topic = f"sensors/{zone}/{measurement_type}/{sensor_id}"
        self.reset_topic = f"commands/reset/{sensor_id}"
        
        # State
        self.start_time = time.time()
        self.phase = hash(sensor_id) % 100
        self.faulty_mode = True  # Can be disabled via command
        
        # Statistics
        self.normal_readings = 0
        self.faulty_readings = 0
        
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
            print(f"[FAULTY {self.sensor_id}] Connected to broker")
            print(f"[FAULTY {self.sensor_id}] Publishing on: {self.publish_topic}")
            print(f"[FAULTY {self.sensor_id}] Error rate: {self.error_rate*100:.0f}%, Magnitude: {self.error_magnitude}σ")
            # Subscribe to reset commands
            client.subscribe(self.reset_topic)
            print(f"[FAULTY {self.sensor_id}] Listening for resets on: {self.reset_topic}")
        else:
            print(f"[FAULTY {self.sensor_id}] Connection failed: {reason_code}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Handle reset commands."""
        self = userdata
        try:
            if msg.topic == self.reset_topic:
                data = json.loads(msg.payload.decode())
                if data.get('action') == 'reset':
                    self._handle_reset()
        except json.JSONDecodeError:
            pass
    
    def _handle_reset(self):
        """Handle a reset command."""
        print(f"\n[FAULTY {self.sensor_id}] ⚡ RESET RECEIVED!")
        print(f"[FAULTY {self.sensor_id}] Resetting to normal operation...")
        
        # Reset state
        self.start_time = time.time()
        self.phase = random.randint(0, 100)
        
        # Temporarily disable faulty mode (simulate "fixed" sensor)
        # It will start generating faults again after some time
        self.faulty_mode = False
        
        # Re-enable after 20-40 seconds
        import threading
        def reenable_faults():
            time.sleep(random.uniform(20, 40))
            if self.running:
                self.faulty_mode = True
                print(f"\n[FAULTY {self.sensor_id}] 🔧 Fault mode re-enabled")
        
        threading.Thread(target=reenable_faults, daemon=True).start()
        
        print(f"[FAULTY {self.sensor_id}] Stats before reset: "
              f"{self.normal_readings} normal, {self.faulty_readings} faulty")
        self.normal_readings = 0
        self.faulty_readings = 0
    
    def _generate_reading(self) -> float:
        """Generate a reading, potentially faulty."""
        # Normal value
        elapsed = time.time() - self.start_time
        normal_value = self.base_value + self.amplitude * math.sin(
            (elapsed + self.phase) * 2 * math.pi / 60
        )
        noise = random.gauss(0, self.amplitude * 0.1)
        normal_value += noise
        
        # Check if we should generate a fault
        if self.faulty_mode and random.random() < self.error_rate:
            # Generate faulty value (several standard deviations away)
            direction = random.choice([-1, 1])
            error = direction * self.amplitude * self.error_magnitude
            faulty_value = normal_value + error
            self.faulty_readings += 1
            return round(faulty_value, 2), True
        
        self.normal_readings += 1
        return round(normal_value, 2), False
    
    def run(self):
        """Start the faulty sensor."""
        print(f"[FAULTY {self.sensor_id}] Starting in zone '{self.zone}'")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            time.sleep(0.5)
            
            while self.running:
                value, is_faulty = self._generate_reading()
                
                payload = json.dumps({
                    'sensor_id': self.sensor_id,
                    'zone': self.zone,
                    'type': self.measurement_type,
                    'value': value,
                    'timestamp': time.time()
                })
                
                self.client.publish(self.publish_topic, payload)
                
                marker = "FAULTY" if is_faulty else "✓"
                print(f"[FAULTY {self.sensor_id}] {marker} Published: {value}")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n[FAULTY {self.sensor_id}] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            print(f"[FAULTY {self.sensor_id}] Final stats: "
                  f"{self.normal_readings} normal, {self.faulty_readings} faulty")
    
    def stop(self):
        """Stop the sensor."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Faulty Sensor Agent')
    parser.add_argument('--id', required=True, help='Sensor ID')
    parser.add_argument('--zone', required=True, help='Zone name')
    parser.add_argument('--type', required=True, dest='measurement_type',
                        help='Measurement type')
    parser.add_argument('--interval', type=float, default=2.0,
                        help='Publishing interval')
    parser.add_argument('--base-value', type=float, default=None,
                        help='Base value')
    parser.add_argument('--amplitude', type=float, default=5.0,
                        help='Normal variation amplitude')
    parser.add_argument('--error-rate', type=float, default=0.3,
                        help='Probability of faulty reading (0.0-1.0)')
    parser.add_argument('--error-magnitude', type=float, default=4.0,
                        help='Error magnitude in standard deviations')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    base_value = args.base_value
    if base_value is None:
        base_value = FaultySensor.DEFAULT_VALUES.get(args.measurement_type, 50.0)
    
    sensor = FaultySensor(
        sensor_id=args.id,
        zone=args.zone,
        measurement_type=args.measurement_type,
        interval=args.interval,
        base_value=base_value,
        amplitude=args.amplitude,
        error_rate=args.error_rate,
        error_magnitude=args.error_magnitude,
        broker=args.broker,
        port=args.port
    )
    sensor.run()


if __name__ == "__main__":
    main()


