# Auto-Logging Configuration

## 🎯 Objectives of This Logging System

The logging system is built to achieve the following goals
1. ✅ Structured JSON logging
2. ✅ Request‑level correlation (`request_id`)
3. ✅ User session tracing via JWT (future‑safe)
4. ✅ Automatic log rotation
5. ✅ Automatic expiration of logs older than 5 days
6. ✅ Async‑safe behavior for FastAPI
7. ✅ Compatibility with ELK, Loki, OpenSearch, CloudWatch
8. ✅ Zero coupling to authentication logic

### -----------------------------------------------------------------------------------------------------

## 📁 Folder Structure

```
core/
│
├── logging/
│   ├── context.py
│   ├── loging_config.py
│   ├── middleware.py
│   └── route_logger.py
│   
│
└── main.py
```

Each file has its own role and works togetehr to provide a complete logging pipeline. 

### -----------------------------------------------------------------------------------------------------

# 1️⃣ context.py — Request & User Context Storage

### Purpose
FastAPI runs multiple requests concurrently using asynchronous execution. Therefore, **global variables should not be used** to store data since they would leak between users.

To solve this, Python provides **contextvars**, which allow data to be stored **per request context**.

#### What this file stores

Each incoming request gets its own isolated context:

* `request_id` — unique identifier for tracing
* `user_id` — extracted from JWT (if present)
* `user_email` — optional
* `user_role` — optional

### How It Works

1. Middleware generates a `request_id`
2. Middleware optionally decodes JWT
3. Extracted values are stored in context variables
4. Logging formatter reads from context automatically

This means:

> Any log written anywhere in the application automatically contains request and user metadata.

Even inside:

* services
* repositories
* background tasks
* Celery workers

No parameters need to be passed manually.

### -----------------------------------------------------------------------------------------------------


# 2️⃣ logging_config.py — Global Logging Engine

### Purpose

This file initializes and controls the **entire logging system**.

It is executed once during application startup.

---

## Logging Initialization Flow

```
Application starts
        ↓
setup_logging() is called
        ↓
Old log files are cleaned
        ↓
Logging handlers are created
        ↓
JSON formatter is attached
        ↓
Logging becomes globally available
```

---

## JSON Logging Format

All logs are written as **single‑line JSON objects**.

This allows:

* machine readability
* easy indexing
* filtering by fields
* time‑series analytics

### Example Log

```
json
{
  "timestamp": "2026-01-23T10:14:02Z",
  "level": "INFO",
  "logger": "http",
  "message": "HTTP request completed",
  "request_id": "c0e5a4d2-0a2b-4ad0",
  "user_id": "42",
  "path": "/api/v1/tires",
  "status_code": 200
}
```

## Automatic Context Injection

The formatter automatically injects:

* request_id
* user_id
* email
* role

This is done by reading from `contextvars`.

Developers **never need to add these manually**.

## Log Rotation

The system uses:

* `TimedRotatingFileHandler`

Configured behavior:

| Feature       | Value |
| ------------- | ----- |
| Rotation      | Daily |
| Timezone      | UTC   |
| File encoding | UTF‑8 |
| Backup count  | 5     |

Rotation happens automatically at **UTC midnight**.

---

## Log Retention Cleanup

Python logging does **not delete old files on startup**. To fix this, a manual cleanup process is executed:

* All `.log*` files are scanned
* & Files older than 5 days are deleted

This guarantees:

* no storage growth
* predictable storage usage


## Console Logging

A separate console handler exists for:

* local development
* Docker stdout
* debugging

Console logs remain human‑readable while file logs remain structured JSON.

### -----------------------------------------------------------------------------------------------------

# 3️⃣ middleware.py — HTTP Request Tracing

### Purpose

This middleware intercepts **every HTTP request**.

It's main role is trace HTTP requests across the system.

## Request Lifecycle

```
Incoming request
      ↓
Generate request_id
      ↓
Attempt JWT extraction
      ↓
Store request context
      ↓
Process request
      ↓
Measure latency
      ↓
Log response
      ↓
Attach X‑Request‑ID header
```

---

## Request ID Correlation

Each request receives a UUID:

```
X‑Request‑ID: 9c6e0f92‑e1a3‑4b77‑9b23
```

Benefits:

* trace a request across logs
* debug production issues
* correlate frontend ↔ backend
* follow microservice chains

---

## JWT User Logging (Future‑Safe)

The middleware **does not enforce authentication**.

Instead, it:

* checks for Authorization header
* decodes token if present
* extracts user fields

If JWT is not implemented yet:

* logging still works
* no errors occur

Once JWT is added later:

* user data automatically appears in logs
* no logging changes required

---

## Safety Design

* JWT decoding failures never break requests
* Logging never blocks response execution
* No request bodies are consumed
* Streaming responses remain safe

### -----------------------------------------------------------------------------------------------------

# 4️⃣ main.py Integration

Only two lines are required:

```
setup_logging()
app.add_middleware(RequestLoggingMiddleware)
```

This instantly enables:

* structured logs
* request tracing
* user session visibility
* retention cleanup

---

# ✅ Final System Capabilities

| Feature              | Supported |
| -------------------- | --------- |
| FastAPI              | ✅         |
| Async‑safe           | ✅         |
| Request tracing      | ✅         |
| JWT user logging     | ✅         |
| Log rotation         | ✅         |
| Log expiration       | ✅         |
| JSON structured logs | ✅         |
| ELK / Loki ready     | ✅         |
| Celery compatible    | ✅         |

---

## 🧠 Summary

This logging system provides:

* enterprise‑grade observability
* clean separation of concerns
* future‑proof authentication logging
* zero developer overhead

