#!/usr/bin/env python3
"""
Sensor Network Simulation Starter

Automatically starts multiple sensors, averaging agents, and an interface agent.
Also demonstrates dynamic agent spawning and removal.
"""

import subprocess
import sys
import time
import threading
import random
import os


class NetworkSimulation:
    """Manages the sensor network simulation."""
    
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.processes = {}  # {name: (process, config)}
        self.running = True
        self.sensor_counter = 0
        
        # Network configuration
        self.zones = ['living_room', 'bedroom', 'kitchen']
        self.measurement_types = ['temperature', 'humidity']
    
    def _start_process(self, name: str, script: str, args: list):
        """Start a subprocess."""
        script_path = os.path.join(self.script_dir, script)
        cmd = [sys.executable, script_path] + args + ['--broker', self.broker, '--port', str(self.port)]
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.processes[name] = (proc, {'script': script, 'args': args})
        print(f"[MASTER] Started: {name}")
        return proc
    
    def _stop_process(self, name: str):
        """Stop a subprocess."""
        if name in self.processes:
            proc, _ = self.processes[name]
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
            del self.processes[name]
            print(f"[MASTER] Stopped: {name}")
    
    def start_sensor(self, sensor_id: str, zone: str, measurement_type: str,
                     interval: float = 2.0, amplitude: float = 5.0):
        """Start a sensor agent."""
        name = f"sensor_{sensor_id}"
        args = [
            '--id', sensor_id,
            '--zone', zone,
            '--type', measurement_type,
            '--interval', str(interval),
            '--amplitude', str(amplitude)
        ]
        self._start_process(name, 'sensor_agent.py', args)
    
    def start_averaging_agent(self, zone: str, measurement_type: str,
                              window: float = 10.0, interval: float = 5.0):
        """Start an averaging agent."""
        name = f"avg_{zone}_{measurement_type}"
        args = [
            '--zone', zone,
            '--type', measurement_type,
            '--window', str(window),
            '--interval', str(interval)
        ]
        self._start_process(name, 'averaging_agent.py', args)
    
    def start_interface(self):
        """Start the interface agent."""
        self._start_process('interface', 'interface_agent.py', [])
    
    def _dynamic_spawner(self):
        """Dynamically spawn and remove sensors."""
        print("[MASTER] Dynamic spawner started")
        time.sleep(20)  # Wait before starting dynamic behavior
        
        while self.running:
            # Wait random interval
            time.sleep(random.uniform(10, 20))
            
            if not self.running:
                break
            
            # Randomly add or remove a sensor
            action = random.choice(['add', 'remove', 'remove'])
            
            if action == 'add':
                # Add a new sensor
                self.sensor_counter += 1
                sensor_id = f"dynamic_{self.sensor_counter:03d}"
                zone = random.choice(self.zones)
                mtype = random.choice(self.measurement_types)
                
                print(f"\n[MASTER] 🆕 Spawning new sensor: {sensor_id} in {zone}")
                self.start_sensor(sensor_id, zone, mtype)
                
            elif action == 'remove':
                # Remove a random dynamic sensor
                dynamic_sensors = [name for name in self.processes.keys()
                                   if name.startswith('sensor_dynamic_')]
                if dynamic_sensors:
                    to_remove = random.choice(dynamic_sensors)
                    print(f"\n[MASTER] 💀 Removing sensor: {to_remove}")
                    self._stop_process(to_remove)
    
    def _output_reader(self, proc, name):
        """Read output from a process."""
        try:
            for line in iter(proc.stdout.readline, ''):
                if line and self.running:
                    # Only print sensor/avg output if not interface (interface clears screen)
                    if name != 'interface':
                        pass  # Suppress output for cleaner display
        except Exception:
            pass
    
    def run_simulation(self, enable_dynamics: bool = True):
        """Run the full simulation."""
        print("=" * 60)
        print("         SENSOR NETWORK SIMULATION")
        print("=" * 60)
        
        try:
            # Start averaging agents first
            print("\n[MASTER] Starting averaging agents...")
            for zone in self.zones:
                for mtype in self.measurement_types:
                    self.start_averaging_agent(zone, mtype)
                    time.sleep(0.2)
            
            time.sleep(1)
            
            # Start initial sensors (2-3 per zone per type)
            print("\n[MASTER] Starting initial sensors...")
            for zone in self.zones:
                for mtype in self.measurement_types:
                    for i in range(random.randint(2, 3)):
                        self.sensor_counter += 1
                        sensor_id = f"{zone[:3]}_{mtype[:4]}_{self.sensor_counter:03d}"
                        self.start_sensor(sensor_id, zone, mtype)
                        time.sleep(0.2)
            
            time.sleep(2)
            
            # Start interface agent
            print("\n[MASTER] Starting interface agent...")
            self.start_interface()
            
            # Start dynamic spawner if enabled
            if enable_dynamics:
                spawner_thread = threading.Thread(target=self._dynamic_spawner, daemon=True)
                spawner_thread.start()
            
            # Start output readers for non-interface processes
            for name, (proc, _) in self.processes.items():
                if name != 'interface':
                    reader = threading.Thread(
                        target=self._output_reader,
                        args=(proc, name),
                        daemon=True
                    )
                    reader.start()
            
            print("\n[MASTER] Simulation running. Press Ctrl+C to stop.")
            print("-" * 60)
            
            # Wait for interface process or Ctrl+C
            interface_proc, _ = self.processes.get('interface', (None, None))
            if interface_proc:
                interface_proc.wait()
            else:
                while self.running:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n\n[MASTER] Stopping simulation...")
        finally:
            self.running = False
            
            # Stop all processes
            for name in list(self.processes.keys()):
                self._stop_process(name)
            
            print("[MASTER] All agents stopped.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sensor Network Simulation')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    parser.add_argument('--no-dynamics', action='store_true',
                        help='Disable dynamic agent spawning')
    args = parser.parse_args()
    
    sim = NetworkSimulation(broker=args.broker, port=args.port)
    sim.run_simulation(enable_dynamics=not args.no_dynamics)


if __name__ == "__main__":
    main()


