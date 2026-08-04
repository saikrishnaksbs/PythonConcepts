# Logging

In production, stdout prints (`print()`) are insufficient. SDE-2 candidates are expected to know how to use Python's built-in `logging` module to direct structured messages to multiple destinations (console, files, metrics systems), implement log rotation, and configure logging asynchronously or with proper formatters.

## Table of Contents

- [Logging Architecture (Loggers, Handlers, Formatters)](#logging-architecture-loggers-handlers-formatters)
- [Log Levels](#log-levels)
- [Rotating Logs](#rotating-logs)
- [Structured Logging (JSON Logging)](#structured-logging-json-logging)

---

## Logging Architecture (Loggers, Handlers, Formatters)

### Explanation

Python's logging system uses a modular design consisting of four main components:
1. **Logger**: The entry point providing the interface for application code (e.g., `logger.info()`). Loggers are organized in a hierarchy (separated by dots, like `app.db`).
2. **Handler**: Directs log records to the appropriate destination (e.g., `StreamHandler` for console, `FileHandler` for disk, `SysLogHandler` for remote syslog).
3. **Formatter**: Dictates the layout of the log message (injecting timestamps, line numbers, log levels).
4. **Filter**: Offers fine-grained control to filter records based on custom criteria.

---

## Log Levels

### Explanation

Log levels categorize messages by severity. By default, setting a level on a logger or handler suppresses all messages below that level.

| Level | Value | Usage |
| :--- | :--- | :--- |
| **DEBUG** | 10 | Detailed debug information (disabled in production). |
| **INFO** | 20 | Normal application behavior (e.g., startup, completed request). |
| **WARNING** | 30 | Something unexpected occurred, but the app is still working. |
| **ERROR** | 40 | Serious issue preventing a specific function from executing. |
| **CRITICAL** | 50 | Fatal error; application or system shutdown. |

---

## Rotating Logs

### Explanation

Writing all logs to a single file indefinitely will eventually fill up the host storage disk. Log rotation limits file size or age by rotating/renaming old files and keeping only a specified number of historical backups.

- **`RotatingFileHandler`**: Rotates based on file size (in bytes).
- **`TimedRotatingFileHandler`**: Rotates based on time intervals (e.g., daily).

### Code example

```python
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Rotate when file size reaches 5MB, keep up to 3 backup files
handler = RotatingFileHandler("app.log", maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.info("Application started with log rotation.")
```

---

## Structured Logging (JSON Logging)

### Explanation

In cloud environments (like Kubernetes, AWS ECS), logs are aggregated by systems like Elasticsearch, Splunk, or Datadog. These systems work best when logs are structured as JSON records rather than plain text, enabling easy filtering and querying by specific fields (e.g., `user_id`, `request_id`).

You can implement this in Python using libraries like `structlog` or by writing a custom Formatter that outputs JSON.

### Code example (Custom JSON Formatter)

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        # Include custom attributes if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        return json.dumps(log_data)

# Usage
logger = logging.getLogger("api")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("API request completed", extra={"request_id": "req-123"})
# Output: {"timestamp": "...", "level": "INFO", "message": "API request completed", "module": "...", "line": ..., "request_id": "req-123"}
```

---

## Common Interview Questions

1. **"Why not just use `print()` for logging?"** `print` can't be selectively filtered by severity, redirected per-destination, or turned off in production without code changes — `logging` decouples "what to log" from "where it goes and at what level."
2. **"What is propagation in the logger hierarchy?"** By default, a log record handled by a child logger (e.g., `app.db`) also propagates up to `app`'s and the root logger's handlers, unless `logger.propagate = False` is set — this is how you can attach one handler at the root and have every module's logs flow through it.
3. **Pitfall:** Configuring logging with `logging.basicConfig()` more than once has no effect after the first call (it's a no-op if handlers already exist on the root logger) — a common source of "why isn't my config taking effect" bugs.
4. **Pitfall:** Using string formatting (`f"{x}"`) inside a log call instead of lazy `%s` args (`logger.debug("%s", x)`) means the string is built even when the log level suppresses the message — wasteful in hot paths.
