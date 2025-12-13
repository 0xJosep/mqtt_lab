#!/usr/bin/env python3
"""
Anomaly Detection System Starter

Starts all components of the anomaly detection system:
- Normal sensors
- Faulty sensors (for testing)
- Averaging agents
- Detection agent
- Identification agent
"""

import subprocess
import sys
import time
import threading
import os


class AnomalyDetectionSimulation:
    """Manages the anomaly detection simulation."""
    
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.sensor_network_dir = os.path.join(os.path.dirname(self.script_dir), 'SensorNetwork')
        self.processes = {}
        self.running = True
    
    def _start_process(self, name: str, script: str, args: list, directory: str = None):
        """Start a subprocess."""
        if directory is None:
            directory = self.script_dir
        script_path = os.path.join(directory, script)
        cmd = [sys.executable, script_path] + args + ['--broker', self.broker, '--port', str(self.port)]
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        self.processes[name] = proc
        print(f"[MASTER] Started: {name}")
        return proc
    
    def _stop_process(self, name: str):
        """Stop a subprocess."""
        if name in self.processes:
            proc = self.processes[name]
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
            del self.processes[name]
            print(f"[MASTER] Stopped: {name}")
    
    def _output_reader(self, proc, name):
        """Read and print output from a process."""
        try:
            for line in iter(proc.stdout.readline, ''):
                if line and self.running:
                    print(f"{line.rstrip()}")
        except Exception:
            pass
    
    def run_simulation(self):
        """Run the full simulation."""
        print("=" * 70)
        print("         ANOMALY DETECTION SYSTEM")
        print("=" * 70)
        
        zone = 'test_zone'
        mtype = 'temperature'
        
        try:
            # Start averaging agent
            print("\n[MASTER] Starting averaging agent...")
            self._start_process(
                'avg',
                'averaging_agent.py',
                ['--zone', zone, '--type', mtype, '--window', '15', '--interval', '5'],
                self.sensor_network_dir
            )
            
            time.sleep(1)
            
            # Start normal sensors
            print("\n[MASTER] Starting normal sensors...")
            for i in range(3):
                self._start_process(
                    f'sensor_normal_{i}',
                    'sensor_agent.py',
                    ['--id', f'normal_{i:03d}', '--zone', zone, '--type', mtype],
                    self.sensor_network_dir
                )
                time.sleep(0.3)
            
            time.sleep(2)
            
            # Start detection agent
            print("\n[MASTER] Starting detection agent...")
            self._start_process(
                'detector',
                'detection_agent.py',
                ['--threshold', '2.0']
            )
            
            time.sleep(1)
            
            # Start identification agent
            print("\n[MASTER] Starting identification agent...")
            self._start_process(
                'identifier',
                'identification_agent.py',
                ['--threshold', '2', '--cooldown', '20']
            )
            
            time.sleep(2)
            
            # Start faulty sensor
            print("\n[MASTER] Starting faulty sensor...")
            self._start_process(
                'sensor_faulty',
                'faulty_sensor.py',
                ['--id', 'faulty_001', '--zone', zone, '--type', mtype,
                 '--error-rate', '0.3', '--error-magnitude', '5.0']
            )
            
            # Start output readers
            for name, proc in self.processes.items():
                reader = threading.Thread(
                    target=self._output_reader,
                    args=(proc, name),
                    daemon=True
                )
                reader.start()
            
            print("\n" + "=" * 70)
            print("[MASTER] All agents started. Press Ctrl+C to stop.")
            print("=" * 70 + "\n")
            
            # Wait for Ctrl+C
            while self.running:
                time.sleep(1)
                # Check for dead processes
                for name, proc in list(self.processes.items()):
                    if proc.poll() is not None:
                        print(f"[MASTER] Process {name} exited")
                    
        except KeyboardInterrupt:
            print("\n\n[MASTER] Stopping simulation...")
        finally:
            self.running = False
            for name in list(self.processes.keys()):
                self._stop_process(name)
            print("[MASTER] All agents stopped.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Anomaly Detection System')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    sim = AnomalyDetectionSimulation(broker=args.broker, port=args.port)
    sim.run_simulation()


if __name__ == "__main__":
    main()


