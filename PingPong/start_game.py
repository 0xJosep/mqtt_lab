#!/usr/bin/env python3
"""
BOUKHRISS Youssef - Icho Ibrahim
Automated Ping-Pong Game Starter

This script spawns both ping and pong clients as subprocesses.
"""

import subprocess
import sys
import time
import signal
import os


def main():
    print("[MASTER] Starting Ping-Pong game...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    client_script = os.path.join(script_dir, "pingpong_client.py")
    
    processes = []
    
    try:
        # Start pong client first (it just listens)
        print("[MASTER] Starting pong client...")
        pong_proc = subprocess.Popen(
            [sys.executable, client_script, "pong"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("PONG", pong_proc))
        
        # Small delay to ensure pong is ready
        time.sleep(1)
        
        # Start ping client with --initial to begin the game
        print("[MASTER] Starting ping client (with initial message)...")
        ping_proc = subprocess.Popen(
            [sys.executable, client_script, "ping", "--initial"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("PING", ping_proc))
        
        print("[MASTER] Both clients started. Press Ctrl+C to stop.")
        print("-" * 50)
        
        # Monitor output from both processes
        import select
        import threading
        
        def read_output(name, proc):
            """Read and print output from a subprocess."""
            try:
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        print(f"{line.rstrip()}")
                    if proc.poll() is not None:
                        break
            except Exception:
                pass
        
        # Start threads to read output
        threads = []
        for name, proc in processes:
            t = threading.Thread(target=read_output, args=(name, proc), daemon=True)
            t.start()
            threads.append(t)
        
        # Wait for Ctrl+C
        while True:
            time.sleep(0.5)
            # Check if any process died
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"[MASTER] {name} process exited with code {proc.returncode}")
            
    except KeyboardInterrupt:
        print("\n[MASTER] Stopping all clients...")
    finally:
        # Terminate all processes
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
                print(f"[MASTER] Terminated {name}")
        
        # Wait for processes to end
        for name, proc in processes:
            proc.wait(timeout=5)
        
        print("[MASTER] All clients stopped.")


if __name__ == "__main__":
    main()


