#!/usr/bin/python3
from flask import Flask
from flask_socketio import SocketIO
import redis
import os
import threading
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
#Configure Redis Connection
redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))
redis_pass = os.getenv('REDIS_PASS', 'password')
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, username="default", password=redis_pass)

try:
    redis_client.ping()
except redis.ConnectionError:
    print("Redis server is not available")
    print("Exiting...")
    exit(1)

def log_listener():
    pubsub = redis_client.pubsub()
    pubsub.subscribe('log_channel')
    for message in pubsub.listen():
        if message['type'] == 'message':
            socketio.emit('log_update', {'data': 'new log entry'})

def checkin_listener():
    pubsub = redis_client.pubsub()
    pubsub.subscribe('checkin_channel')
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'].decode('utf-8'))
                socketio.emit('implant_checkin', data)
            except Exception as e:
                print(f"Error decoding checkin_channel message: {e}")

threading.Thread(target=log_listener, daemon=True).start()
threading.Thread(target=checkin_listener, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
