# Exception Handling

Robust exception handling separates normal flow from error recovery. CPython uses exceptions for normal flow control (such as `StopIteration`), meaning exceptions in Python are relatively cheap compared to languages like C++ or Java. For SDE-2 interviews, understanding execution flows, exception chaining, custom exceptions, and the built-in hierarchy is essential.

## Table of Contents

- [The `try-except-else-finally` Flow](#the-try-except-else-finally-flow)
- [Exception Chaining (`raise ... from ...`)](#exception-chaining-raise--from-)
- [Custom Exceptions](#custom-exceptions)
- [Python Exception Hierarchy](#python-exception-hierarchy)
- [The `traceback` Module](#the-traceback-module)

---

## The `try-except-else-finally` Flow

### Explanation

- **`try`**: Wraps the code that might raise an exception.
- **`except`**: Captures and handles specified exceptions.
- **`else`**: Runs only if **no exceptions** were raised in the `try` block. Use this to avoid catching unexpected exceptions in code that runs after a successful operation.
- **`finally`**: Always runs, regardless of whether an exception occurred, was handled, or was re-raised. Used for clean-up tasks.

### Why it matters / internals

- If an exception occurs in the `try` block, execution immediately halts and jumps to the matching `except` block.
- **`finally` overrides returns**: If the `try` or `except` block has a `return` statement, but the `finally` block also returns a value, the `finally` block's return value will be the one returned by the function.

### Code example

```python
def division(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print("Cannot divide by zero!")
        return 0
    else:
        print("Division successful.")
        return result
    finally:
        print("Cleaning up resources.")

print(division(10, 2))
# Outputs:
# Division successful.
# Cleaning up resources.
# 5.0
```

---

## Exception Chaining (`raise ... from ...`)

### Explanation

When handling an exception, raising a different exception can lead to losing the original context (traceback). Python 3 introduced exception chaining to address this.
- Implicit chaining: An exception raised inside an `except` block automatically lists the original exception as the cause.
- Explicit chaining: Using `raise NewException from original_exception` sets the `__cause__` attribute on the new exception, linking them in the traceback.

### Code example

```python
def read_config(filepath):
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError as err:
        # Wrap FileNotFoundError into a custom ConfigurationError
        raise ValueError("Configuration file missing") from err

# Calling this will show:
# FileNotFoundError: ...
# The above exception was the direct cause of the following exception:
# ValueError: Configuration file missing
```

---

## Custom Exceptions

### Explanation

To define a custom exception, subclass the built-in `Exception` class (or one of its subclasses). Avoid inheriting from `BaseException` directly.

### Code example

```python
class CustomValidationError(Exception):
    """Raised when request payload fails internal business validation."""
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

try:
    raise CustomValidationError("Invalid age parameter", 400)
except CustomValidationError as err:
    print(f"Error: {err.args[0]}, Code: {err.error_code}")
```

---

## Python Exception Hierarchy

### Explanation

Understanding the exception hierarchy helps write specific `except` handlers:

```text
BaseException
 ├── SystemExit
 ├── KeyboardInterrupt
 ├── GeneratorExit
 └── Exception
      ├── ArithmeticError
      │    └── ZeroDivisionError
      ├── LookupError
      │    ├── IndexError
      │    └── KeyError
      └── ValueError
```

### Why it matters / internals

- Never use `except BaseException:` unless you intend to intercept system exits and interrupt signals, which usually prevents the program from closing.
- Always catch specific exceptions (e.g., `KeyError`) before general ones (e.g., `LookupError`, `Exception`).

---

## The `traceback` Module

### Explanation

The `traceback` module provides standard interfaces to extract, format, and print stack traces. This is particularly useful in logging systems or background task runners where exceptions must be serialized and logged without crashing the thread.

### Code example

```python
import traceback

try:
    1 / 0
except ZeroDivisionError:
    tb_string = traceback.format_exc()
    print("Logged traceback:\n", tb_string)
```

---

## Context Managers for Exception Cleanup

Context managers (`with`) are the idiomatic alternative to `try/finally` for resource cleanup (see [25_context_managers.md](25_context_managers.md) for the full protocol). `__exit__(self, exc_type, exc_val, exc_tb)` receives exception info and can suppress it by returning `True`.

```python
class SuppressValueError:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return exc_type is ValueError  # suppress only ValueError

with SuppressValueError():
    raise ValueError("swallowed")
print("execution continues")
```

## Multiple Except Clauses & Exception Groups

```python
try:
    risky()
except (KeyError, IndexError) as e:
    print("lookup issue", e)
except Exception as e:
    print("generic", e)

# Python 3.11+: except* for exception groups (from asyncio TaskGroup, etc.)
try:
    raise ExceptionGroup("multi", [ValueError("a"), TypeError("b")])
except* ValueError as eg:
    print("value errors:", eg.exceptions)
except* TypeError as eg:
    print("type errors:", eg.exceptions)
```

## Common Interview Questions

1. **"What happens if `finally` itself raises?"** The exception from `finally` replaces any exception/return value from `try`/`except` — the original is lost unless explicitly chained.
2. **"Difference between `except Exception` and bare `except:`?"** Bare `except:` also catches `BaseException` subclasses like `KeyboardInterrupt` and `SystemExit`, which usually should propagate — always prefer `except Exception`.
3. **Pitfall:** Catching `Exception` and logging without re-raising can silently swallow bugs — always weigh whether to re-raise after logging.
