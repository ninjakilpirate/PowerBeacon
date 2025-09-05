#!/bin/bash
set -e

# Generate cert and key if missing
if [ ! -f /tmp/key.pem ] || [ ! -f /tmp/cert.pem ]; then
    openssl req -x509 -newkey rsa:4096 -nodes -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -subj '/CN=localhost'
fi

POWERBEACON_SERVER_BIND_IP="${POWERBEACON_SERVER_BIND_IP:-0.0.0.0}"
POWERBEACON_SERVER_PORT="${POWERBEACON_SERVER_PORT:-8000}"

exec python -u powerbeaconServer.py -p "$POWERBEACON_SERVER_PORT" -b "$POWERBEACON_SERVER_BIND_IP" --ssl "$SSL_TRUE"
