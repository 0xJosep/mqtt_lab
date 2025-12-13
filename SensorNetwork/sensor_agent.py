#!/usr/bin/env python3
"""
BOUKHRISS Youssef - Icho Ibrahim
Sensor Agent - Simulates a sensor publishing readings via MQTT

Publishes readings on topic: sensors/<zone>/<measurement_type>/<sensor_id>
Values follow a sinusoidal pattern to simulate realistic variations.
"""

import argparse
import time
import math
import json
import paho.mqtt.client as mqtt


class SensorAgent:
    """Simulates a sensor that publishes readings at regular intervals."""
    
    # Default base values for different measurement types
    DEFAULT_VALUES = {
        'temperature': 22.0,    # Celsius
        'humidity': 50.0,       # Percentage
        'pressure': 1013.25,    # hPa
        'light': 500.0,         # Lux
    }
    
    def __init__(self, sensor_id: str, zone: str, measurement_type: str,
                 interval: float, base_value: float, amplitude: float,
                 broker: str, port: int):
        self.sensor_id = sensor_id
        self.zone = zone
        self.measurement_type = measurement_type
        self.interval = interval
        self.base_value = base_value
        self.amplitude = amplitude
        self.broker = broker
        self.port = port
        
        # Build topic
        self.topic = f"sensors/{zone}/{measurement_type}/{sensor_id}"
        
        # For sinusoidal variation
        self.start_time = time.time()
        self.phase = hash(sensor_id) % 100  # Random phase offset based on ID
        
        # MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=self)
        self.client.on_connect = self._on_connect
        self.running = True
    
    @staticmethod
    def _on_connect(client, userdata, flags, reason_code, properties):
        """Callback when connected to broker."""
        self = userdata
        if reason_code == 0:
            print(f"[SENSOR {self.sensor_id}] Connected to broker")
            print(f"[SENSOR {self.sensor_id}] Publishing on: {self.topic}")
        else:
            print(f"[SENSOR {self.sensor_id}] Connection failed: {reason_code}")
    
    def _generate_reading(self) -> float:
        """Generate a sensor reading following a sinusoidal pattern."""
        elapsed = time.time() - self.start_time
        # Period of about 60 seconds for full cycle
        value = self.base_value + self.amplitude * math.sin(
            (elapsed + self.phase) * 2 * math.pi / 60
        )
        # Add small random noise
        import random
        noise = random.gauss(0, self.amplitude * 0.1)
        return round(value + noise, 2)
    
    def run(self):
        """Start the sensor and publish readings."""
        print(f"[SENSOR {self.sensor_id}] Starting in zone '{self.zone}'")
        print(f"[SENSOR {self.sensor_id}] Type: {self.measurement_type}, Interval: {self.interval}s")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            time.sleep(0.5)  # Wait for connection
            
            while self.running:
                reading = self._generate_reading()
                
                # Create message payload
                payload = json.dumps({
                    'sensor_id': self.sensor_id,
                    'zone': self.zone,
                    'type': self.measurement_type,
                    'value': reading,
                    'timestamp': time.time()
                })
                
                self.client.publish(self.topic, payload)
                print(f"[SENSOR {self.sensor_id}] Published: {reading} ({self.measurement_type})")
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n[SENSOR {self.sensor_id}] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
    
    def stop(self):
        """Stop the sensor."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Sensor Agent')
    parser.add_argument('--id', required=True, help='Unique sensor ID')
    parser.add_argument('--zone', required=True, help='Zone/room name')
    parser.add_argument('--type', required=True, dest='measurement_type',
                        help='Measurement type (temperature, humidity, etc.)')
    parser.add_argument('--interval', type=float, default=2.0,
                        help='Publishing interval in seconds')
    parser.add_argument('--base-value', type=float, default=None,
                        help='Base value for measurements')
    parser.add_argument('--amplitude', type=float, default=5.0,
                        help='Amplitude of variation')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    # Set default base value if not provided
    base_value = args.base_value
    if base_value is None:
        base_value = SensorAgent.DEFAULT_VALUES.get(args.measurement_type, 50.0)
    
    agent = SensorAgent(
        sensor_id=args.id,
        zone=args.zone,
        measurement_type=args.measurement_type,
        interval=args.interval,
        base_value=base_value,
        amplitude=args.amplitude,
        broker=args.broker,
        port=args.port
    )
    agent.run()


if __name__ == "__main__":
    main()


