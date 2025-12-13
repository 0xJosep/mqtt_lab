#!/usr/bin/env python3
"""
Supervisor Agent - Contract Net Protocol

Manages job allocation using the Contract Net Protocol:
1. Generates/receives jobs
2. Sends Call for Proposals (CfP)
3. Collects bids from machines
4. Selects winner and awards job
"""

import argparse
import time
import json
import uuid
import random
import threading
from dataclasses import dataclass, asdict
from typing import Optional
import paho.mqtt.client as mqtt


@dataclass
class Job:
    """Represents a job to be scheduled."""
    job_id: str
    job_type: str
    description: str
    timestamp: float


@dataclass
class Bid:
    """Represents a bid from a machine."""
    machine_id: str
    job_id: str
    proposed_time: float
    timestamp: float


class Supervisor:
    """Supervisor agent that manages job allocation."""
    
    # Available job types for simulation
    JOB_TYPES = ['job_A', 'job_B', 'job_C', 'job_D', 'job_E']
    
    def __init__(self, supervisor_id: str, job_interval: float, deadline: float,
                 broker: str, port: int):
        self.supervisor_id = supervisor_id
        self.job_interval = job_interval
        self.deadline = deadline
        self.broker = broker
        self.port = port
        
        # Topics
        self.cfp_topic = "jobs/cfp"
        self.bid_topic = f"jobs/bid/{supervisor_id}"
        
        # State
        self.current_job: Optional[Job] = None
        self.bids: list[Bid] = []
        self.bid_lock = threading.Lock()
        self.collecting_bids = False
        
        # Statistics
        self.jobs_created = 0
        self.jobs_allocated = 0
        self.jobs_failed = 0
        
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
            print(f"[SUPERVISOR {self.supervisor_id}] Connected to broker")
            # Subscribe to bids
            client.subscribe(self.bid_topic)
            print(f"[SUPERVISOR {self.supervisor_id}] Listening for bids on: {self.bid_topic}")
        else:
            print(f"[SUPERVISOR {self.supervisor_id}] Connection failed: {reason_code}")
    
    @staticmethod
    def _on_message(client, userdata, msg):
        """Handle incoming bids."""
        self = userdata
        
        if not self.collecting_bids:
            return
        
        try:
            data = json.loads(msg.payload.decode())
            
            # Check if it's a bid for our current job
            if data.get('job_id') != self.current_job.job_id:
                return
            
            # Check if it's a rejection
            if data.get('type') == 'rejection':
                print(f"[SUPERVISOR] Rejection from {data.get('machine_id')}: {data.get('reason')}")
                return
            
            bid = Bid(
                machine_id=data['machine_id'],
                job_id=data['job_id'],
                proposed_time=data['proposed_time'],
                timestamp=data.get('timestamp', time.time())
            )
            
            with self.bid_lock:
                self.bids.append(bid)
            
            print(f"[SUPERVISOR] Bid received from {bid.machine_id}: {bid.proposed_time}s")
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[SUPERVISOR] Error parsing bid: {e}")
    
    def _generate_job(self) -> Job:
        """Generate a random job."""
        job_type = random.choice(self.JOB_TYPES)
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        job = Job(
            job_id=job_id,
            job_type=job_type,
            description=f"Execute {job_type} operation",
            timestamp=time.time()
        )
        
        self.jobs_created += 1
        return job
    
    def _send_cfp(self, job: Job):
        """Send a Call for Proposal."""
        cfp = {
            'type': 'cfp',
            'supervisor_id': self.supervisor_id,
            'job_id': job.job_id,
            'job_type': job.job_type,
            'description': job.description,
            'deadline': self.deadline,
            'timestamp': time.time()
        }
        
        self.client.publish(self.cfp_topic, json.dumps(cfp))
        print(f"\n[SUPERVISOR] 📢 CfP sent for {job.job_type} (ID: {job.job_id})")
        print(f"[SUPERVISOR] Deadline: {self.deadline}s")
    
    def _select_winner(self) -> Optional[Bid]:
        """Select the best bid (lowest time)."""
        with self.bid_lock:
            if not self.bids:
                return None
            # Select bid with minimum proposed time
            return min(self.bids, key=lambda b: b.proposed_time)
    
    def _send_award(self, winner: Bid, job: Job):
        """Send job award to winning machine."""
        award = {
            'type': 'award',
            'supervisor_id': self.supervisor_id,
            'job_id': job.job_id,
            'job_type': job.job_type,
            'machine_id': winner.machine_id,
            'timestamp': time.time()
        }
        
        topic = f"jobs/award/{winner.machine_id}"
        self.client.publish(topic, json.dumps(award))
        
        print(f"[SUPERVISOR] 🏆 Job awarded to {winner.machine_id} ({winner.proposed_time}s)")
        
        # Send rejections to other bidders
        with self.bid_lock:
            for bid in self.bids:
                if bid.machine_id != winner.machine_id:
                    reject = {
                        'type': 'reject',
                        'supervisor_id': self.supervisor_id,
                        'job_id': job.job_id,
                        'reason': 'Another machine was selected',
                        'timestamp': time.time()
                    }
                    reject_topic = f"jobs/reject/{bid.machine_id}"
                    self.client.publish(reject_topic, json.dumps(reject))
    
    def _run_auction(self, job: Job):
        """Run the Contract Net auction for a job."""
        self.current_job = job
        self.bids = []
        self.collecting_bids = True
        
        # Send CfP
        self._send_cfp(job)
        
        # Wait for deadline
        time.sleep(self.deadline)
        
        self.collecting_bids = False
        
        # Select winner
        print(f"[SUPERVISOR] Deadline reached. {len(self.bids)} bids received.")
        
        winner = self._select_winner()
        
        if winner:
            self._send_award(winner, job)
            self.jobs_allocated += 1
        else:
            print(f"[SUPERVISOR] ❌ No bids received. Job {job.job_id} failed.")
            self.jobs_failed += 1
        
        self.current_job = None
    
    def run(self):
        """Start the supervisor."""
        print(f"[SUPERVISOR {self.supervisor_id}] Starting...")
        print(f"[SUPERVISOR] Job interval: {self.job_interval}s, Deadline: {self.deadline}s")
        
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            time.sleep(1)
            
            while self.running:
                # Generate and auction a job
                job = self._generate_job()
                self._run_auction(job)
                
                # Wait before next job
                print(f"[SUPERVISOR] Waiting {self.job_interval}s before next job...")
                print("-" * 50)
                time.sleep(self.job_interval)
                
        except KeyboardInterrupt:
            print(f"\n[SUPERVISOR] Shutting down...")
        finally:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            print(f"[SUPERVISOR] Stats: {self.jobs_allocated}/{self.jobs_created} jobs allocated, "
                  f"{self.jobs_failed} failed")
    
    def stop(self):
        """Stop the supervisor."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description='Contract Net Supervisor')
    parser.add_argument('--id', default='supervisor_001', help='Supervisor ID')
    parser.add_argument('--job-interval', type=float, default=10.0,
                        help='Interval between jobs (seconds)')
    parser.add_argument('--deadline', type=float, default=3.0,
                        help='Bid collection deadline (seconds)')
    parser.add_argument('--broker', default='localhost', help='MQTT broker')
    parser.add_argument('--port', type=int, default=1883, help='MQTT port')
    args = parser.parse_args()
    
    supervisor = Supervisor(
        supervisor_id=args.id,
        job_interval=args.job_interval,
        deadline=args.deadline,
        broker=args.broker,
        port=args.port
    )
    supervisor.run()


if __name__ == "__main__":
    main()


