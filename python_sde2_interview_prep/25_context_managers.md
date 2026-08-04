# Context Managers

Context managers in Python are a primary mechanism for managing resources safely. They ensure that setup and teardown tasks (like closing database connections, unlocking mutexes, or closing files) are reliably executed, even if errors occur. For SDE-2 roles, you should know the context manager protocol, how to write them using generators, and utility patterns in `contextlib`.

## Table of Contents

- [The `with` Statement](#the-with-statement)
- [The Context Manager Protocol](#the-context-manager-protocol)
- [Generator-based Context Managers (`@contextmanager`)](#generator-based-context-managers-contextmanager)
- [Advanced Helpers in `contextlib` (`suppress`, `ExitStack`)](#advanced-helpers-in-contextlib-suppress-exitstack)

---

## The `with` Statement

### Explanation

The `with` statement simplifies resource cleanup by defining a runtime context. 

```python
with expression as target:
    # Code block
```

It guarantees that cleanup actions are run, wrapping the block execution in an implicit `try...finally` structure.

---

## The Context Manager Protocol

### Explanation

Any object that implements the context manager protocol can be used in a `with` statement. The protocol requires two methods:

1. **`__enter__(self)`**: Sets up the context and returns the target resource (bound to the `as` variable).
2. **`__exit__(self, exc_type, exc_val, exc_tb)`**: Handles teardown. It receives three arguments containing the exception details if one was raised within the `with` block.

### Why it matters / internals

- If no exception occurred, `exc_type`, `exc_val`, and `exc_tb` are `None`.
- If an exception occurred, returning `True` from `__exit__` suppresses the exception (preventing it from propagating). Returning `False` (or `None`) causes the exception to be re-raised after `__exit__` completes.

### Code example

```python
class ManagedLock:
    def __enter__(self):
        print("Acquiring lock...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Releasing lock...")
        if exc_type is not None:
            print(f"Handled exception: {exc_val}")
            return True  # Suppress the exception
        return False

with ManagedLock():
    print("Executing block...")
    raise ValueError("Something went wrong")

print("Program continues successfully!")
```

---

## Generator-based Context Managers (`@contextmanager`)

### Explanation

Creating a class to implement the protocol can be boilerplate-heavy. The `contextlib` module provides the `@contextmanager` decorator, which turns a generator function into a context manager.

### Code example

```python
from contextlib import contextmanager

@contextmanager
def file_manager(filepath, mode):
    # Setup phase (runs when entering the block)
    f = open(filepath, mode)
    try:
        yield f  # The value yielded is bound to the 'as' variable
    finally:
        # Teardown phase (runs when exiting the block)
        print("Closing file...")
        f.close()

with file_manager("test.txt", "w") as f:
    f.write("Hello World")
```

---

## Advanced Helpers in `contextlib` (`suppress`, `ExitStack`)

### Explanation

- **`contextlib.suppress(*exceptions)`**: A clean context manager to suppress specified exceptions. It is cleaner than using a `try-except` block with `pass`.
- **`contextlib.ExitStack`**: Allows dynamically managing an arbitrary number of context managers. This is crucial when you need to open multiple files or resources whose counts are determined at runtime.

### Code example

```python
from contextlib import suppress, ExitStack
import os

# Using suppress
with suppress(FileNotFoundError):
    os.remove("non_existent_file.txt")  # Will not raise an error

# Using ExitStack
files_to_open = ["a.txt", "b.txt"]
with ExitStack() as stack:
    # Dynamically enter all context managers
    file_objects = [stack.enter_context(open(name, "w")) for name in files_to_open]
    
    file_objects[0].write("Data for A")
    file_objects[1].write("Data for B")
# All files are guaranteed to be closed here!
```

---

## Common Interview Questions

1. **"What happens if `__exit__` raises its own exception?"** It replaces (and swallows) whatever exception was propagating from the `with` block — a common source of masked errors if `__exit__` itself is unreliable.
2. **"Can you nest multiple context managers in one `with` statement?"** Yes — `with open("a") as a, open("b") as b:` is equivalent to nested `with` blocks, entered left-to-right and exited right-to-left.
3. **"Difference between `@contextmanager` and writing a class?"** `@contextmanager` is more concise for simple setup/teardown pairs (one `yield`), but a class is better when the context manager needs to be re-entrant, hold complex state, or be reused/inspected as an object.
4. **Pitfall:** A generator-based context manager must wrap the `yield` in `try/finally` — without it, an exception raised inside the `with` block skips the cleanup code that comes after `yield`.
