# PowerBeacon — Setup Guide

Run `MariaDB`, `Redis`, the `Message Broker`, the `PowerBeacon Server`, and the `Web UI` by hand.  
All config comes from one `.env` file loaded with `python-dotenv`.

---

## Prereqs (once)

- Python 3.11 with a virtual environment
- Packages: `flask`, `flask-socketio`, `redis`, `pymysql`, `eventlet`, `python-dotenv`, `requests`

Create venv & install: 

    python3.11 -m venv .venv        
    source .venv/bin/activate  
    pip install --no-index --find-links=wheelhouse -r services/app/requirements.txt  
    pip install --no-index --find-links=wheelhouse -r services/powerbeacon_server/requirements.txt  
    pip install --no-index --find-links=wheelhouse -r services/messageBroker/requirements.txt  


---

## .env (shared config)

Create `.env` in the repo root and set real values:

    # MariaDB
    DB_HOST=localhost
    DB_PORT=3306
    DB_USER=pbuser
    DB_PASSWD=pbpass
    DB_NAME=powerbeacon

    # Redis
    REDIS_HOST=localhost
    REDIS_PORT=6379
    REDIS_DB=0
    REDIS_PASS=

    # Browser-facing URL of the Message Broker (must be reachable by the browser)
    BROKER_HOST=http://192.168.0.100:5001

Tip: use LAN IP/DNS (not `localhost`) for services other hosts/browsers must reach.

---

## 1) Initialize MariaDB

1. Start MariaDB (on the DB host):
    sudo systemctl enable --now mariadb
    sudo systemctl status mariadb

   If remote clients will connect, set `bind-address = 0.0.0.0` in `/etc/mysql/mariadb.conf.d/50-server.cnf`,
   then `sudo systemctl restart mariadb`.

2. Create DB + user (first time only):
    mysql -u root -p

    -- inside MySQL:
   
       CREATE DATABASE IF NOT EXISTS `powerbeacon`
       CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
       CREATE USER IF NOT EXISTS 'pbuser'@'%' IDENTIFIED BY 'pbpass';
       GRANT ALL PRIVILEGES ON `powerbeacon`.* TO 'pbuser'@'%';
       FLUSH PRIVILEGES;
       EXIT;

4. Import your SQL dump (adjust path):
    mysql -u root -p powerbeacon < powerbeaconDatabase.sql

---

## 2) Start Redis

Local, default (no auth):  
    `redis-server --daemonize yes`

Exposed/remote with password (recommended if not localhost):
    
    redis-server \
      --bind 0.0.0.0 \
      --port 6379 \
      --requirepass "your_redis_password" \
      --protected-mode no \
      --daemonize yes

Ping test:
    `redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASS" PING`  
    # → PONG

---

## 3) Start the Message Broker (dotenv-powered)

From the repo root (with venv active). This injects `.env` automatically:  

    python -m dotenv -f .env run -- \
    python services/messageBroker/messageBroker.py

Basic handshake check (from the browser machine):
    `curl "http://192.168.0.100:5001/socket.io/?EIO=4&transport=polling&t=ping"`  

---

## 4) Start the PowerBeacon Server (backend)

Bind + port + optional TLS:

    python -m dotenv -f .env run -- \
      python services/server/powerbeaconServer.py \
        -b 0.0.0.0 \
        -p 8000 \
        --ssl true

(If you don’t have certs yet, there is a script in extras that can help.)

---

## 5) Start the Web UI

Bind + port:

    python -m dotenv -f .env run -- \
      python services/web/app.py \
        -b 0.0.0.0 \
        -p 8080

Open the UI:

    http://<host-ip>:8080/

---

## Stop Everything

- Processes started in a terminal: press **Ctrl+C** in that terminal.
- Redis (daemonized): `redis-cli -a "$REDIS_PASS" SHUTDOWN`.
- MariaDB (if needed): `sudo systemctl stop mariadb`.

---

