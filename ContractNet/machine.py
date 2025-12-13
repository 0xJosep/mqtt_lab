#!/usr/bin/env python3
"""
BOUKHRISS Youssef - Icho Ibrahim
Machine Agent - Contract Net Protocol

Represents a machine that can perform certain job types.
- Receives Call for Proposals
- Submits bids for jobs it can handle
- Executes awarded jobs
"""

import argparse
import time
import json
import threading
from typing import Optional
import paho.mqtt.client as mqtt


class Machine:
    """Machine agent that bids on and executes jobs."""
    
    def __init__(self, machine_id: str, capabilities: dict[str, float],
                 broker: str, port: int):
        self.machine_id = machine_id
        self.capabilities = capabilities  # {job_type: execution_time}
        self.broker = broker
        self.port = port
        
        # Topics
        self.cfp_topic = "jobs/cfp"
        self.award_topic = f"jobs/award/{machine_id}"
        self.reject_topic = f"jobs/reject/{machine_id}"
        
        # State
        self.busy = False
        self.current_job: Optional[str] = None
        self.current_job_end: float = 0
        
        # Statistics
        self.jobs_bid = 0
        self.jobs_won = 0
        self.jobs_completed = 0
        self.jobs_rejected = 0
        
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
            print(f"[MACHINE {self.machine_id}] Connected to broker")
            print(f"[MACHINE {self.machine_id}] Capabilities: {self.capabilities}")
            # Subscribe to relevant topics
            client.subscribe(self.cfp_topic)
            client.subscribe(self.award_topic)
            client.subscribe(self.reject_topic)
            print(f"[MACHINE {self.machine_id}] Subscribed to CfP and award topics")
        else:
            print(f"[MACHINE {self.machine_id}] Connection failed: {reason_code}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Handle incoming messages."""
        self = userdata
        
        try:
            data = json.loads(msg.payload.decode())
            msg_type = data.get('type')
            
            if msg_type == 'cfp':
                self._handle_cfp(data)
            elif msg_type == 'award':
                self._handle_award(data)
            elif msg_type == 'reject':
                self._handle_reject(data)
                
        except json.JSONDecodeError as e:
            print(f"[MACHINE {self.machine_id}] Error parsing message: {e}")
    
    def _handle_cfp(self, data: dict):
        """Handle a Call for Proposal."""
        job_type = data.get('job_type')
        job_id = data.get('job_id')
        supervisor_id = data.get('supervisor_id')
        
        print(f"[MACHINE {self.machine_id}] CfP received: {job_type} (ID: {job_id})")
        
        # Check if we're busy
        if self.busy:
            print(f"[MACHINE {self.machine_id}] Busy, sending rejection")
            self._send_rejection(supervisor_id, job_id, "Machine is busy")
            return
        
        # Check if we can do this job
        if job_type not in self.capabilities:
            print(f"[MACHINE {self.machine_id}] Cannot do {job_type}, sending rejection")
            self._send_rejection(supervisor_id, job_id, f"Cannot perform {job_type}")
            return
        
        # Submit bid
        execution_time = self.capabilities[job_type]
        self._send_bid(supervisor_id, job_id, execution_time)
    
    def _send_bid(self, supervisor_id: str, job_id: str, execution_time: float):
        """Send a bid to the supervisor."""
        bid = {
            'type': 'bid',
            'machine_id': self.machine_id,
            'job_id': job_id,
            'proposed_time': execution_time,
            'timestamp': time.time()
        }
        
        bid_topic = f"jobs/bid/{supervisor_id}"
        self.client.publish(bid_topic, json.dumps(bid))
        self.jobs_bid += 1
        
        print(f"[MACHINE {self.machine_id}] 📤 Bid sent: {execution_time}s for job {job_id}")
    
    def _send_rejection(self, supervisor_id: str, job_id: str, reason: str):
        """Send a rejection to the supervisor."""
        rejection = {
            'type': 'rejection',
            'machine_id': self.machine_id,
            'job_id': job_id,
            'reason': reason,
            'timestamp': time.time()
        }
        
        bid_topic = f"jobs/bid/{supervisor_id}"
        self.client.publish(bid_topic, json.dumps(rejection))
    
    def _handle_award(self, data: dict):
        """Handle a job award."""
        job_id = data.get('job_id')
        job_type = data.get('job_type')
        supervisor_id = data.get('supervisor_id')
        
        if data.get('machine_id') != self.machine_id:
            return  # Not for us
        
        print(f"\n[MACHINE {self.machine_id}] 🎉 WON job {job_id} ({job_type})!")
        
        self.jobs_won += 1
        self.busy = True
        self.current_job = job_id
        
        # Execute job in background
        execution_time = self.capabilities.get(job_type, 5.0)
        thread = threading.Thread(
            target=self._execute_job,
            args=(job_id, job_type, execution_time, supervisor_id),
            daemon=True
        )
        thread.start()
    
    def _execute_job(self, job_id: str, job_type: str, execution_time: float, supervisor_id: str):
        """Execute a job (simulated)."""
        print(f"[MACHINE {self.machine_id}] ⚙️  Executing {job_type} for {execution_time}s...")
        
        time.sleep(execution_time)
        
        # Job complete
        self.busy = False
        self.current_job = None
        self.jobs_completed += 1
        
        # Notify completion
        completion = {
            'type': 'completion',
            'machine_id': self.machine_id,
            'job_id': job_id,
            'job_type': job_type,
            'execution_time': execution_time,
            'timestamp': time.time()
        }
        
        complete_topic = f"jobs/complete/{supervisor_id}"
        self.client.publish(complete_topic, json.dumps(completion))
        
        print(f"[MACHINE {self.machine_id}] ✅ Completed job {job_id}")
    
    def _handle_reject(self, data: dict):
        """Handle a bid rejection."""
        job_id = data.get('job_id')
        reason = data.get('reason', 'Unknown')
        
        print(f"[MACHINE {self.machine_id}] 😔 Bid rejected for {job_id}: {reason}")
        self.jobs_rejected += 1
    
    def run(self):
        """Start the machine agent."""
        print(f"[MACHINE {self.machine_id}] Starting...")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n[MACHINE {self.machine_id}] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            print(f"[MACHINE {self.machine_id}] Stats: "
                  f"Bids: {self.jobs_bid}, Won: {self.jobs_won}, "
                  f"Completed: {self.jobs_completed}, Rejected: {self.jobs_rejected}")
    
    def stop(self):
        """Stop the machine."""
        self.running = False


def parse_capabilities(cap_str: str) -> dict[str, float]:
    """Parse capabilities string like 'job_A:5,job_B:3,job_C:8'."""
    capabilities = {}
    for item in cap_str.split(','):
        item = item.strip()
        if ':' in item:
            job_type, time_str = item.split(':')
            capabilities[job_type.strip()] = float(time_str.strip())
    return capabilities


def main():
    parser = argparse.ArgumentParser(description='Contract Net Machine Agent')
    parser.add_argument('--id', required=True, help='Machine ID')
    parser.add_argument('--capabilities', required=True,
                        help='Capabilities as "job_type:time,..." e.g., "job_A:5,job_B:3"')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    capabilities = parse_capabilities(args.capabilities)
    
    if not capabilities:
        print("Error: No valid capabilities provided")
        return
    
    machine = Machine(
        machine_id=args.id,
        capabilities=capabilities,
        broker=args.broker,
        port=args.port
    )
    machine.run()


if __name__ == "__main__":
    main()


