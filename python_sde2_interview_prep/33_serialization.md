# Serialization

Serialization (marshalling) converts in-memory objects into a format that can be stored on disk or transmitted over a network. Deserialization is the reverse process. SDE-2 candidates must know the trade-offs between text-based (JSON, YAML) and binary-based (Pickle, Protobuf) serialization.

## Table of Contents

- [JSON](#json)
- [Pickle](#pickle)
- [Marshal](#marshal)
- [YAML](#yaml)
- [Protocol Buffers (Protobuf)](#protocol-buffers-protobuf)
- [Summary Comparison](#summary-comparison)

---

## JSON

### Explanation

JSON (JavaScript Object Notation) is a human-readable text format. In Python, the standard `json` module translates data structures to/from JSON strings.

- **Pros**: Language independent, human readable, widely supported, safe to deserialize.
- **Cons**: Only supports basic types (dicts, lists, strings, numbers, booleans, None). Cannot serialize custom Python classes or bytes natively.

---

## Pickle

### Explanation

`pickle` is a Python-specific binary serialization protocol. It can serialize almost any Python object (including custom classes, closures, and reference cycles).

- **Pros**: Extremely powerful, handles complex Python-native structures.
- **Cons**: Slow, produces large outputs compared to optimized binary formats, not cross-language.
- **Security**: **Extremely unsafe**. Deserializing a malicious pickle file can execute arbitrary code.

---

## Marshal

### Explanation

`marshal` is a built-in module used internally by CPython to read and write compiled bytecode (`.pyc` files).

- **Pros**: Fast.
- **Cons**: Do not use it for general serialization. The format is **not stable** across different Python versions.

---

## YAML

### Explanation

YAML is a human-readable data serialization standard. It is commonly used for configuration files (e.g., Kubernetes manifests, CI/CD configs).

- **Pros**: Highly readable, supports comments.
- **Cons**: Parsers are slow and complex. Security risk: like pickle, standard YAML loaders can instantiate arbitrary objects unless using `yaml.safe_load()` in PyYAML.

---

## Protocol Buffers (Protobuf)

### Explanation

Protobuf is a binary serialization format developed by Google. It relies on a pre-defined schema file (`.proto`) to serialize structured data efficiently.

- **Pros**: Highly optimized, very small binary footprint, language independent (C++, Go, Java, Python), supports schema evolution.
- **Cons**: Human unreadable without decoding, requires a compilation step (`protoc`) to generate Python code.

---

## Summary Comparison

| Format | Output Type | Cross-Language | Safe? | Schema Required | Custom Classes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **JSON** | Text | Yes | Yes | No | No (requires custom encoder) |
| **YAML** | Text | Yes | Only with `safe_load` | No | Yes |
| **Pickle** | Binary | No (Python only) | **No** (RCE risk) | No | Yes |
| **Protobuf** | Binary | Yes | Yes | **Yes** | Yes (via compiled code) |

---

## Custom JSON Encoding for Non-Primitive Types

```python
import json
from datetime import datetime

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

json.dumps({"created": datetime.now()}, cls=CustomEncoder)
```

## Common Interview Questions

1. **"Why is `pickle.loads` dangerous?"** A crafted pickle stream can define `__reduce__` to call arbitrary functions (e.g., `os.system`) during deserialization — never unpickle data from an untrusted source (network input, user uploads).
2. **"How would you serialize a custom class to JSON?"** Either implement a custom `JSONEncoder.default()` (shown above) or convert to a dict first (`dataclasses.asdict`, `__dict__`) before calling `json.dumps`.
3. **Pitfall:** `json.dumps` doesn't natively support `datetime`, `set`, `Decimal`, or custom objects — always test serialization of complex payloads before deploying.
4. **Pitfall:** Comparing dict-derived JSON output for equality can be order-sensitive as a *string*, even though the underlying dicts are equal — compare parsed objects, not raw JSON text.
