# PowerBeacon Dockerized Architecture

PowerBeacon is a modular Command and Control (C2) framework composed of five Docker containers. Each container serves a distinct purpose in supporting distributed implant communications.
---

## Table of Contents
- [Container Overview](#container-overview)
  - [1. PowerBeacon Server](#1-powerbeacon-server)
  - [2. PowerBeacon Web Application](#2-powerbeacon-web-application)
  - [3. Message Broker](#3-message-broker)
  - [4. Redis](#4-redis)
  - [5. MariaDB](#5-mariadb)
- [Default Port Configurations](#default-port-configurations)
- [Deployment Notes](#deployment-notes)
- [Recommended Order of Operations](#recommended-order-of-operations)
- [Build & Deploy with Docker](#build--deploy-with-docker)
  - [Folder Layout (reference)](#folder-layout-reference)
  - [Prerequisites](#prerequisites)
  - [1) Create/Review .env](#1-createreview-env)
  - [2) Review/Edit compose.yaml](#2-reviewedit-composeyaml)
  - [3) (Optional) Edit Dockerfiles](#3-optional-edit-dockerfiles)
  - [4) Build Application Images](#4-build-application-images)
  - [5) Start the Stack](#5-start-the-stack)
  - [6) Verify](#6-verify)
  - [7) Stop / Restart / Rebuild](#7-stop--restart--rebuild)
  - [8) Common Adjustments](#8-common-adjustments)
  - [9) Quick Start (Minimal)](#9-quick-start-minimal)
  - [11) Offline Lab Note](#11-offline-lab-note)

## Container Overview

### 1. PowerBeacon Server

**Description**:  
Handles incoming HTTP POSTs. It is the backend interface that implants use to check in, receive commands, and post surveys to.

**Responsibilities**:
- Receives and authenticates implant beacons
- Logs communications and results to the MariaDB backend
- Publishes new log entries and events to Redis for downstream consumption

**Notes**:
- Should be exposed on an external-facing port (e.g., 80 or 443)

---

### 2. PowerBeacon Web Application

**Description**:  
The operator-facing frontend that provides visibility and control over implants, logs, and tasking.

**Responsibilities**:
- Displays a list of active implants and related telemetry
- Allows operators to send commands and manage implants
- Subscribes to WebSocket updates for real-time logs and status changes

**Notes**:
- Typically runs on port 5000

---

### 3. Message Broker

**Description**:  
Listens to Redis pub/sub channels and relays messages to frontend clients over WebSockets.

**Responsibilities**:
- Maintains WebSocket connections with clients
- Listens for updates on Redis channels
- Pushes log messages and event updates to the Web UI

**Notes**:
- Runs independently of the frontend or backend API

---

### 4. Redis

**Description**:  
An in-memory data structure store used for message passing between services using pub/sub.

**Responsibilities**:
- Facilitates communication between the PowerBeacon Server and the Message Broker, which relays to the Web Server
- Enables low-latency event publishing for real-time updates

---

### 5. MariaDB

**Description**:  
The relational database used to persist implant data, logs, tasking history, credentials, and other telemetry.

**Responsibilities**:
- Stores all persistent operational data
- Supports query interfaces for both the backend server and frontend UI

**Notes**:
- Initializes with schema and seed data as part of the container boot process
- Requires persistent volume mapping for data durability across restarts

---

## Default Port Configurations

| Container              | Purpose                          | Protocols     | Ports     | Persistent? |
|------------------------|----------------------------------|---------------|-----------|-------------|
| PowerBeacon Server     | Handle implant comms             | HTTP/HTTPS    | 8000      | No          |
| PowerBeacon Web App    | Operator UI                      | HTTP/WebSocket| 5000      | No          |
| Message Broker         | WebSocket and Redis bridge       | WebSocket     | 5001      | No          |
| Redis                  | Pub/Sub messaging layer          | TCP (Redis)   | 6379      | No          |
| MariaDB                | Persistent data storage          | SQL (TCP)     | 3306      | Yes         |

**Notes**:
- These are the exposed ports in the Dockerfiles.  Configure your compose.yaml for the ports you need.

---

## Deployment Notes

- All containers are coordinated using `docker-compose`.
- Environment variables are defined in a `.env` file and passed to each container securely.
- Docker volumes are used to persist MariaDB data across restarts.
- For lab or offline use:
  - Containers can be built and exported as `.tar` files and run without internet access.
  - Consider disabling protected mode in Redis for isolated environments.
- SSL termination can be managed externally (e.g., Nginx proxy container).

---

## Recommended Order of Operations

1. **Start MariaDB** and ensure the schema is initialized via SQL dump or volume.
2. **Start Redis**, configured in unprotected mode if required.
3. **Start the PowerBeacon Server**, ensuring it can write to MariaDB and Redis.
4. **Start the Message Broker**, connected to Redis.
5. **Start the Web Application**, configured to connect to both the Message Broker and MariaDB.

All services should be running under the same Docker network to allow hostname-based container communication.

## Build & Deploy with Docker

This section explains how to build all PowerBeacon containers locally and start the full stack with Docker Compose.

---

### Folder Layout (reference)

> Your repository should look roughly like this. If your layout differs, adjust the paths in `docker-compose.yml`.
```
powerbeacon/
├─ compose.yaml                      # or docker-compose.yml
├─ .env                              # environment variables (create this)
├─ services/
│  ├─ server/
│  │  ├─ Dockerfile
│  │  ├─ PowerbeaconServer.py
│  │  ├─ requirements.txt
│  │  └─ entrypoint.sh
│  ├─ web/
│  │  ├─ Dockerfile
│  │  ├─ app.py 
│  │  ├─ requirements.txt 
│  │  └─ static/ html/ ...
│  ├─ messageBroker/
│  │  ├─ Dockerfile
│  │  ├─ messageBroker.py
│  │  ├─ requirements.txt
├─ mariadb/
│  ├─ init/
│  │  └─ 10_powerbeacon.sql         #Initial DB seed
│  └─Dockerfile                     # optional custom MariaDB config
│  └─ my.cnf                        # optional custom MariaDB config
└─ redis/
   └─ Dockerfile
   └─ redis.conf                    # optional, if not using defaults
```

### Prerequisites

- Docker Engine and Docker Compose v2 installed.
- Internet connectivity **required** (to pull `redis` and `mariadb` base images).
- Open the project root in a terminal.

---

### 1) Create/Review `.env`

Create a `.env` file in the project root. These variables are used by `compose.yaml`.

```ini
# MariaDB
DB_HOST=192.168.0.100
DB_USER=pbuser
DB_PASSWD=pbpassChangeMe
DB_NAME=powerbeaconChangeMe
DB_ROOT_PASS=ChangeMeRoot

# Redis
REDIS_HOST=192.168.0.100
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASS=

# App -> Broker (full URL)
BROKER_HOST=http://192.168.0.100:5001

#Powebeacon SSL (true/false -- override as needed per app)
SSL_TRUE=false
```

---

### 2) Review/Edit `compose.yaml` 

- Ensure service build contexts and Dockerfiles match your folder layout.
- Confirm volumes (especially MariaDB) point to either a **named volume** or a Linux path that Docker can access.
- Add multiple PowerBeaconServers as desired to handle SSL and non-SSL connections.

---

### 3) (Optional) Edit Dockerfiles

You generally **should not need to edit** the Dockerfiles. If you do:
- Pin Python versions if deterministic builds are required.
- Avoid `latest` unless you are comfortable with upstream changes.
- For offline labs later, avoid `pip install` from the internet at runtime; vendor wheels into the repo and `pip install --no-index --find-links=./wheelhouse -r requirements.txt`.

---

### 4) Build Application Images

Build the three PowerBeacon images (Server, WebApp, Message Broker). Redis and MariaDB will be pulled automatically.

```bash
# From the repo root
docker compose build --pull
```

> `--pull` ensures base images for your app containers are refreshed before the build.  
> Pulling `redis` and `mariadb` requires internet connectivity.

---

### 5) Start the Stack

```bash
# Start everything in the background
docker compose up -d
```

Compose will:
- Build any images not already built.
- Pull `redis` and `mariadb` images (internet required).
- Create the network (e.g., `powerbeacon_net`).
- Start containers.
- Run MariaDB init scripts from `db/init/*.sql` (first startup only).

---

### 6) Verify

```bash
# See running services
docker compose ps

# Tail logs for a specific service (Ctrl+C to exit)
docker compose logs -f <image>

```

Health checks to confirm:
- **MariaDB**: accepts connections; init scripts ran without error.
- **Server**: can connect to MariaDB and Redis.
- **Message Broker**: connects to Redis; WebSocket endpoint is reachable at `http://<host>:${BROKER_PORT}/socket.io/` (or equivalent).
- **WebApp**: loads at `http://<host>:${WEBAPP_PORT}` and shows live updates.

---

### 7) Stop / Restart / Rebuild

```bash
# Stop without removing resources
docker compose stop

# Stop and remove containers, network, and anonymous volumes
docker compose down

# Down + remove named volumes (DANGEROUS: wipes DB data)
docker compose down -v

# Rebuild after Dockerfile/app changes
docker compose build --no-cache
docker compose up -d
```

---

### 8) Common Adjustments

- **Ports already in use**: Change `${SERVER_PORT}`, `${WEBAPP_PORT}`, or `${BROKER_PORT}` in `.env` and restart.
- **MariaDB data persistence**:
  - Use a named volume (e.g., `mariadb_data:`) to avoid permissions issues.
- **Redis in lab mode**:
  - In a trusted, isolated lab you may run Redis without a password and with `protected-mode no`. In production-like environments, enable a password and restrict network access.

---

### 9) Quick Start (Minimal)

```bash
# 0) Ensure internet access (needed to pull redis and mariadb images)
# 1) Create .env (see template above)
# 2) Build app images
docker compose build --pull

# 3) Launch
docker compose up -d

# 4) Check logs
docker compose logs -f
```

---

### 11) Offline Lab Note 

This guide assumes you are **online** to fetch `redis` and `mariadb`. For offline deployments later:
- `docker pull` the required images on an internet-connected machine.
- `docker save` them to `.tar` files.
- Transfer and `docker load` on the offline host.
- Vendor Python wheels into `wheelhouse/` and install with `--no-index`.




