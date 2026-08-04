# File Handling

File system operations and serialization are fundamental tasks in any backend environment. For SDE-2 roles, interviewers expect you to know how to handle files safely without resource leaks, manipulate paths platform-independently, and choose the correct serialization formats.

## Table of Contents

- [File Modes & Text vs Binary Modes](#file-modes--text-vs-binary-modes)
- [Resource Management via Context Managers](#resource-management-via-context-managers)
- [Modern Path Handling: `pathlib` vs `os`](#modern-path-handling-pathlib-vs-os)
- [Serialization: CSV, JSON, and Pickle](#serialization-csv-json-and-pickle)

---

## File Modes & Text vs Binary Modes

### Explanation

When opening a file using the built-in `open(file, mode)` function, the mode dictates the access type and formatting:
- **`r` / `w` / `a`**: Read, write (overwriting), append.
- **`t` / `b`**: Text (default) or Binary.
- **`+`**: Open for updating (reading and writing).

### Why it matters / internals

- **Text Mode (`t`)**: Python decodes bytes from the disk into unicode strings based on a specific encoding (defaults to `utf-8` on most modern platforms, but can vary by OS).
- **Binary Mode (`b`)**: Python reads/writes raw bytes (`bytes` objects) without modification. Necessary for images, zip files, or serialized payloads.
- **Newline Translation**: In text mode, Python translates platform-specific line endings (`\r\n` on Windows, `\n` on Unix) to `\n` upon reading, and back upon writing. In binary mode, no translation occurs.

---

## Resource Management via Context Managers

### Explanation

Opening a file consumes a system file descriptor. File descriptors are a limited OS resource. If you open files without closing them, you run the risk of running out of descriptors (a file descriptor leak).

Using `with open(...) as f:` ensures the file descriptor is closed immediately when exiting the block, even if an exception occurs inside the block.

### Code example

```python
# Bad practice:
f = open("data.txt", "r")
data = f.read()
# If processing data raises an exception, the file remains open!
f.close()

# Good practice:
with open("data.txt", "r") as f:
    data = f.read()
```

---

## Modern Path Handling: `pathlib` vs `os`

### Explanation

- **`os.path`**: Traditional approach. Represents paths as raw strings. Paths are manipulated using string functions or `os.path.join`, which can lead to platform errors (slashes vs backslashes).
- **`pathlib`**: Introduced in PEP 428. Represents paths as first-class, object-oriented path objects.

### Code example

```python
import os
from pathlib import Path

# Traditional os.path
legacy_path = os.path.join("var", "log", "app.log")

# Modern pathlib
modern_path = Path("var") / "log" / "app.log"

print(modern_path.exists())
print(modern_path.parent)
print(modern_path.suffix)  # '.log'
```

---

## Serialization: CSV, JSON, and Pickle

### Explanation

- **CSV**: Standard library `csv` module provides readers/writers that handle quotes and delimiters automatically.
- **JSON**: Standard library `json` module translates Python objects (lists, dicts, strings, ints) into JSON.
- **Pickle**: Standard library `pickle` module serializes arbitrary Python objects into a binary format.

### Why it matters / internals (Pickle Security)

> [!CAUTION]
> **Pickle is unsafe.** Never unpickle untrusted data. Pickle deserialization can execute arbitrary code using the `__reduce__` magic method on a class.

### Code example (Pickle Code Execution)

```python
import pickle
import os

class Malicious:
    def __reduce__(self):
        # Tells pickle to call os.system('whoami') upon deserialization
        return (os.system, ('whoami',))

# Serialize
payload = pickle.dumps(Malicious())

# Deserialize (Executes command!)
pickle.loads(payload)
```

---

## `os` Module Essentials

```python
import os

os.getcwd()                       # current working directory
os.listdir(".")                   # directory listing
os.makedirs("a/b/c", exist_ok=True)
os.environ.get("HOME")            # environment variables
os.path.join("a", "b", "c.txt")   # platform-safe join
os.path.splitext("file.tar.gz")   # ('file.tar', '.gz')
os.remove("file.txt")             # delete a file
```

## Common Interview Questions

1. **"Why prefer `with open(...)` over manual `open`/`close`?"** Guarantees the file descriptor is released even if an exception is raised mid-read/write — manual `close()` calls are skipped when an exception propagates before reaching them.
2. **"What's the difference between `json` and `pickle`?"** JSON is a text format, language-agnostic, and safe for untrusted input (limited to primitives); pickle is Python-specific binary format that can serialize arbitrary objects but is unsafe to deserialize from untrusted sources.
3. **Pitfall:** Reading a huge file with `.read()` loads it entirely into memory — prefer iterating line-by-line (`for line in f:`) or chunked `f.read(size)` for large files.
4. **Pitfall:** Opening a binary file in text mode on Windows silently corrupts data due to newline translation (`\r\n` handling) — always use `"rb"`/`"wb"` for binary content.
