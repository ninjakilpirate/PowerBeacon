#!/bin/bash
set -e

# Generate cert and key if missing
if [ ! -f /tmp/key.pem ] || [ ! -f /tmp/cert.pem ]; then
    openssl req -x509 -newkey rsa:4096 -nodes -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -subj '/CN=localhost'
fi

exec python -u powerbeaconServer.py -p 8000 --ssl "$SSL_TRUE"
