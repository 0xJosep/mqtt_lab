#!/usr/bin/env python3
"""
Contract Net Protocol Simulation Starter

Starts:
- One supervisor generating jobs
- Multiple machines with different capabilities
"""

import subprocess
import sys
import time
import threading
import os


class ContractNetSimulation:
    """Manages the Contract Net simulation."""
    
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.processes = {}
        self.running = True
    
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
        """Run the Contract Net simulation."""
        print("=" * 70)
        print("         CONTRACT NET PROTOCOL - JOB SCHEDULING")
        print("=" * 70)
        
        # Machine configurations: different capabilities for each machine
        machines = [
            ('machine_001', 'job_A:3,job_B:5,job_C:7'),         # Good at job_A
            ('machine_002', 'job_B:2,job_C:4,job_D:6'),         # Good at job_B
            ('machine_003', 'job_A:6,job_C:3,job_E:4'),         # Good at job_C
            ('machine_004', 'job_D:2,job_E:3'),                  # Specialized in D,E
            ('machine_005', 'job_A:4,job_B:4,job_C:4,job_D:4,job_E:4'),  # Generalist
        ]
        
        try:
            # Start machines
            print("\n[MASTER] Starting machines...")
            for machine_id, caps in machines:
                self._start_process(
                    machine_id,
                    'machine.py',
                    ['--id', machine_id, '--capabilities', caps]
                )
                time.sleep(0.5)
            
            time.sleep(2)
            
            # Start supervisor
            print("\n[MASTER] Starting supervisor...")
            self._start_process(
                'supervisor',
                'supervisor.py',
                ['--id', 'supervisor_001', '--job-interval', '8', '--deadline', '3']
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
            print("[MASTER] Contract Net simulation running. Press Ctrl+C to stop.")
            print("=" * 70 + "\n")
            
            # Wait for Ctrl+C
            while self.running:
                time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n\n[MASTER] Stopping simulation...")
        finally:
            self.running = False
            for name in list(self.processes.keys()):
                self._stop_process(name)
            print("[MASTER] All agents stopped.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Contract Net Simulation')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    sim = ContractNetSimulation(broker=args.broker, port=args.port)
    sim.run_simulation()


if __name__ == "__main__":
    main()


