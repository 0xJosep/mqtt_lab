# Contract Net Protocol - Job Scheduling

Implementation of the Contract Net Protocol for distributed job scheduling using MQTT.

## Overview

This system implements a multi-agent job scheduling system where:
- A **Supervisor** agent generates jobs and manages the allocation process
- Multiple **Machine** agents bid on jobs they can perform
- Jobs are allocated using the Contract Net Protocol

## Protocol Flow

1. Supervisor sends **Call for Proposal (CfP)** with job details
2. Machines reply with **Bids** (proposed time) or **Rejections**
3. After deadline, Supervisor selects best bid
4. Supervisor sends **Award** to winner, **Reject** to others
5. Winning machine executes the job

## Topics

| Topic | Description |
|-------|-------------|
| `jobs/cfp` | Call for Proposals from Supervisor |
| `jobs/bid/<supervisor_id>` | Bids from machines |
| `jobs/award/<machine_id>` | Job award to specific machine |
| `jobs/reject/<machine_id>` | Bid rejection notification |
| `jobs/complete/<supervisor_id>` | Job completion notification |

## Agents

### Supervisor (`supervisor.py`)

Generates jobs and manages the Contract Net auction.

```bash
python supervisor.py --id supervisor_001
```

**Arguments:**
- `--id`: Supervisor ID
- `--job-interval`: Time between job generations (default: 10s)
- `--deadline`: Bid collection deadline (default: 3s)
- `--broker`: MQTT broker (default: localhost)
- `--port`: MQTT port (default: 1883)

### Machine (`machine.py`)

Represents a machine that can perform certain job types.

```bash
python machine.py --id machine_001 --capabilities "job_A:5,job_B:3,job_C:8"
```

**Arguments:**
- `--id`: Machine ID
- `--capabilities`: Comma-separated list of `job_type:time` pairs
- `--broker`: MQTT broker (default: localhost)
- `--port`: MQTT port (default: 1883)

## Design Decisions

### Machine IDs in Messages

Machine IDs are included in bid messages (not just topics) to ensure reliable 
identification even with MQTT wildcards. The supervisor extracts machine IDs 
from the message payload.

### Job Award Distribution

Awards are sent only to the winning machine on its specific topic 
(`jobs/award/<machine_id>`). Rejection messages are sent to losing bidders
to allow them to update their state if needed.

## Running the Simulation

```bash
python start_contract_net.py
```

This starts:
- One supervisor generating random jobs
- Multiple machines with different capabilities


