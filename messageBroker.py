#!/usr/bin/python3
from flask import Flask
from flask_socketio import SocketIO
import redis
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)

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
            uuid = message['data'].decode('utf-8')
            socketio.emit('implant_checkin', {'uuid': uuid})


threading.Thread(target=log_listener, daemon=True).start()
threading.Thread(target=checkin_listener, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
