# Testing

Writing testable code and testing it thoroughly is a key SDE-2 expectation. You must be comfortable structuring tests, using fixtures, isolating external dependencies via mocks, and running coverage checks.

## Table of Contents

- [`unittest` vs `pytest`](#unittest-vs-pytest)
- [Pytest Fixtures](#pytest-fixtures)
- [Mocking & Patching](#mocking--patching)
- [Parameterized Tests](#parameterized-tests)
- [Test Coverage](#test-coverage)

---

## `unittest` vs `pytest`

### Explanation

- **`unittest`**: Built-in standard library testing framework. It is object-oriented, requiring you to subclass `unittest.TestCase` and use assertions like `self.assertEqual()`.
- **`pytest`**: Third-party framework. It is the industry standard for modern Python. It allows writing tests as simple functions and using standard Python `assert` statements directly. It also features a powerful fixture system.

### Code comparison

```python
# Unittest style
import unittest

class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(1 + 1, 2)

# Pytest style
def test_add():
    assert 1 + 1 == 2
```

---

## Pytest Fixtures

### Explanation

Fixtures provide a fixed baseline upon which tests can reliably and repeatedly execute. They are used to set up database connections, initialize clients, or create temp directories.

### Why it matters / internals

- Fixtures can specify a **scope** (`function`, `class`, `module`, `session`), indicating how often the setup runs.
- Fixtures can use `yield` to split setup and teardown phases.

### Code example

```python
import pytest

@pytest.fixture(scope="module")
def db_connection():
    print("\n[Setup] Connecting to Database...")
    db = {"connection": "active"}
    yield db
    print("\n[Teardown] Closing Database Connection...")

def test_query(db_connection):
    assert db_connection["connection"] == "active"
```

---

## Mocking & Patching

### Explanation

Mocking isolates code under test by replacing complex, external, or slow dependencies (e.g., third-party API clients, databases) with dummy objects that record interactions and return pre-set values.

- `unittest.mock.Mock`: Generic mock object.
- `unittest.mock.patch`: Replaces a name in a given module with a Mock object for the duration of the test.

### Why it matters / internals (Where to Patch Gotcha)

> [!IMPORTANT]
> **Patch where the name is looked up, not where it is defined.**
> If `app.py` does `from service import fetch_data` and uses `fetch_data`, patching `service.fetch_data` will **not** work. You must patch `app.fetch_data` because `app.py` has already bound its own reference to that function during import.

### Code example

```python
from unittest.mock import patch
import requests

def get_status_code(url):
    response = requests.get(url)
    return response.status_code

# We mock requests.get to avoid making a real HTTP request
@patch("requests.get")
def test_get_status_code(mock_get):
    # Set mock response behavior
    mock_get.return_value.status_code = 200
    
    assert get_status_code("https://example.com") == 200
    mock_get.assert_called_once_with("https://example.com")
```

---

## Parameterized Tests

### Explanation

Parameterized testing runs a single test function multiple times with different sets of inputs and expected outcomes.

### Code example (Pytest)

```python
import pytest

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (5, 5, 10),
    (-1, 1, 0)
])
def test_addition(a, b, expected):
    assert a + b == expected
```

---

## Test Coverage

### Explanation

Test coverage measures the percentage of code executed during your tests. Run coverage using the `coverage` tool:

```bash
# Run tests under coverage analysis
coverage run -m pytest

# Generate a terminal report
coverage report -m

# Generate an interactive HTML report
coverage html
```

---

## `monkeypatch` Fixture

Pytest's built-in `monkeypatch` fixture safely sets/deletes attributes, dict items, or environment variables for the duration of a test, automatically undoing changes afterward (safer than manually patching and forgetting to revert).

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key-123")
    import os
    assert os.environ["API_KEY"] == "test-key-123"
    # automatically restored after the test
```

## Common Interview Questions

1. **"What's the difference between a `Mock` and a `MagicMock`?"** `MagicMock` additionally implements Python's magic/dunder methods (`__len__`, `__iter__`, etc.), so it can be used where the code under test relies on those protocols; plain `Mock` does not support them out of the box.
2. **"How do you test code that depends on the current time?"** Patch `datetime.now`/`time.time` (or inject a clock dependency) rather than sleeping in tests — `freezegun` is a common third-party tool for this.
3. **Pitfall:** Over-mocking makes tests pass while the real integration is broken — mocks should stand in for genuinely external/slow dependencies, not the code under test itself.
4. **Pitfall:** High coverage % doesn't imply correctness — a line can be "covered" by a test that never asserts anything meaningful about its behavior.
