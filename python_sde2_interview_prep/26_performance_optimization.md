# Performance Optimization

Performance optimization is key to running cost-effective, responsive backend systems. For SDE-2 interviews, you should be able to analyze the time complexity of Python built-ins, identify bottleneck areas using profilers, and leverage optimization tools like `__slots__`, caching, and efficient data structures.

## Table of Contents

- [Time Complexities of Built-in Structures](#time-complexities-of-built-in-structures)
- [Profiling Tools (`timeit`, `cProfile`)](#profiling-tools-timeit-cprofile)
- [Memoization with `lru_cache`](#memoization-with-lru_cache)
- [Memory Savings via `__slots__`](#memory-savings-via-__slots__)
- [Code-Level Optimization Techniques](#code-level-optimization-techniques)

---

## Time Complexities of Built-in Structures

### Explanation

Choosing the correct data structure is the easiest way to optimize code. Python's built-ins (Lists, Sets, Dicts) are implemented in C and have distinct performance profiles:

| Operation | List | Set | Dict | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Append / Insert** | $O(1)$ (amortized) | $O(1)$ | $O(1)$ | List insert at index $0$ is $O(N)$ due to shifting elements. |
| **Lookup / Membership** | $O(N)$ | $O(1)$ | $O(1)$ | Set/Dict use hash tables. List uses linear scan. |
| **Delete** | $O(N)$ | $O(1)$ | $O(1)$ | List deletes shift remaining elements. |
| **Get Item (Index)** | $O(1)$ | N/A | N/A | Lists provide direct array access. |

### Why it matters / internals

- Lists are dynamic arrays. Appending is $O(1)$ amortized because when the array fills up, Python allocates a larger block of memory and copies elements over.
- Sets and Dictionaries are hash tables. If hash collisions are high (due to poor hashing), performance degrades to $O(N)$.

---

## Profiling Tools (`timeit`, `cProfile`)

### Explanation

Don't optimize blindly. Identify bottleneck operations using profilers first.
- **`timeit`**: Used to benchmark small code snippets.
- **`cProfile`**: A built-in deterministic profiler that reports call counts and execution times for all functions.

### Code example

```python
import cProfile

def compute_squares():
    return [x * x for x in range(100000)]

# Run profiler
cProfile.run("compute_squares()")
```

---

## Memoization with `lru_cache`

### Explanation

`functools.lru_cache` is a decorator that caches the results of function calls based on the arguments passed, using a Least Recently Used eviction policy.

### Code example

```python
from functools import lru_cache

# Cache up to 128 distinct results
@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(fibonacci(100))  # Extremely fast instead of taking years!
```

---

## Memory Savings via `__slots__`

### Explanation

By default, Python instances store attributes in a dynamic dictionary (`self.__dict__`), which allows adding attributes at runtime but carries substantial memory overhead.

Defining `__slots__` tells Python to allocate a fixed-size array for attributes instead of a dictionary.

### Code example

```python
class RegularPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class SlottedPoint:
    __slots__ = ('x', 'y')  # Restricts attributes to x and y
    def __init__(self, x, y):
        self.x = x
        self.y = y

# SlottedPoint uses ~3-5x less memory per instance.
```

### Pitfalls

- Class instances with `__slots__` cannot have new attributes added to them dynamically at runtime unless `__dict__` is included in `__slots__` (which defeats the memory benefit).
- Multi-inheritance with multiple slotted classes requires careful design to avoid conflicts.

---

## Code-Level Optimization Techniques

### Explanation

1. **Avoid Unnecessary Copies**: Use generators instead of list comprehensions when piping data.
2. **Local Scope Lookup**: Accessing local variables is faster than accessing global variables or object attributes.
3. **Use Built-in Functions**: Built-in functions like `map`, `filter`, `sum`, and operators from the `operator` module run compiled C-code and are faster than equivalent Python-level loops.
4. **String Concatenation**: Avoid concatenating strings using `+` in loops; strings are immutable, meaning each `+` creates a new string object. Use `''.join(list_of_strings)` instead.

---

## `timeit` Usage

```python
import timeit

# From the command line: python -m timeit "'-'.join(str(n) for n in range(100))"
t = timeit.timeit("'-'.join(str(n) for n in range(100))", number=10000)
print(t)
```

`timeit` disables garbage collection during measurement by default and runs the snippet many times to reduce noise — always prefer it over manual `time.time()` deltas for micro-benchmarks.

## Avoiding Unnecessary Copies

```python
# Bad: creates a new list copy for slicing large data repeatedly
chunk = big_list[1000:2000]

# Better for read-only iteration: use itertools.islice (no copy)
from itertools import islice
chunk_iter = islice(big_list, 1000, 2000)

# Bad: string += in a loop is O(n^2) due to repeated reallocation
s = ""
for word in words:
    s += word  # avoid

# Good: O(n)
s = "".join(words)
```

## Common Interview Questions

1. **"How do you find the bottleneck in a slow endpoint?"** Profile first with `cProfile`/`py-spy` (sampling, low overhead in production) to find hot functions, then micro-benchmark the specific hot path with `timeit` before optimizing.
2. **"Why is `lru_cache` unsafe for methods with mutable arguments?"** Cache keys are derived from argument hashes — unhashable arguments (lists, dicts) raise `TypeError`, and mutable-but-hashable objects that change after caching return stale results.
3. **Pitfall:** Premature optimization — always measure before rewriting "slow-looking" code; Python's built-ins (implemented in C) are often faster than a hand-rolled equivalent.
4. **Pitfall:** `@lru_cache` on instance methods keeps a reference to `self` for the cache's lifetime, which can prevent garbage collection of the instance (a common memory-leak trap in long-lived services).
