#!/bin/sh
set -e

# Generate cert and key if missing
if [ ! -f /tmp/key.pem ] || [ ! -f /tmp/cert.pem ]; then
    openssl req -x509 -newkey rsa:4096 -nodes -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -subj '/CN=localhost'
fi

LISTEN_PORT="${SOCAT_LISTEN_PORT:-443}"
FORWARD_IP="${SOCAT_FORWARD_IP:-127.0.0.1}"
FORWARD_PORT="${SOCAT_FORWARD_PORT:-80}"

exec socat OPENSSL-LISTEN:${LISTEN_PORT},cert=/tmp/cert.pem,key=/tmp/key.pem,verify=0,reuseaddr,fork TCP:${FORWARD_IP}:${FORWARD_PORT}
