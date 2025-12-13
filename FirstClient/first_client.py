#!/usr/bin/env python3
"""
BOUKHRISS Youssef - Icho Ibrahim
First MQTT Client - Basic Publish/Subscribe Example

This client connects to an MQTT broker, subscribes to a topic,
prints received messages, and publishes several messages with delays.
"""

import argparse
import time
import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, reason_code, properties):
    """Callback when the client connects to the broker."""
    if reason_code == 0:
        print(f"[INFO] Connected to broker successfully")
        # Subscribe to topic after successful connection
        client.subscribe(userdata['topic'])
        print(f"[INFO] Subscribed to topic: {userdata['topic']}")
    else:
        print(f"[ERROR] Connection failed with code: {reason_code}")


def on_message(client, userdata, msg):
    """Callback when a message is received."""
    print(f"[RECEIVED] Topic: {msg.topic} | Message: {msg.payload.decode()}")


def on_publish(client, userdata, mid, reason_code, properties):
    """Callback when a message is published."""
    print(f"[PUBLISHED] Message ID: {mid}")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    """Callback when subscription is confirmed."""
    print(f"[INFO] Subscription confirmed (mid: {mid})")


def main():
    parser = argparse.ArgumentParser(description='First MQTT Client - Pub/Sub Example')
    parser.add_argument('--broker', default='localhost', help='MQTT broker address')
    parser.add_argument('--port', type=int, default=1883, help='MQTT broker port')
    parser.add_argument('--topic', default='hello', help='Topic to subscribe/publish')
    args = parser.parse_args()

    # Create client with userdata to pass topic info
    userdata = {'topic': args.topic}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=userdata)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe

    print(f"[INFO] Connecting to {args.broker}:{args.port}...")
    
    try:
        # Connect to broker
        client.connect(args.broker, args.port, keepalive=60)
        
        # Start the network loop in a background thread
        client.loop_start()
        
        # Wait for connection
        time.sleep(1)
        
        # Publish several messages with delays
        for i in range(1, 6):
            message = f"Hello MQTT! Message #{i}"
            print(f"[SENDING] Publishing: {message}")
            client.publish(args.topic, message)
            time.sleep(2)  # 2-second delay between messages
        
        # Keep running to receive any remaining messages
        print("[INFO] Finished publishing. Listening for messages (Ctrl+C to exit)...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[INFO] Disconnected from broker")


if __name__ == "__main__":
    main()


