# PowerBeacon Dockerized Architecture

PowerBeacon is a modular Command and Control (C2) framework composed of five Docker containers. Each container serves a distinct purpose in supporting distributed implant communications.

---

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




