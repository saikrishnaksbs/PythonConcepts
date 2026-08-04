# Iterators & Generators

Iterators and generators are core components of Python's lazy evaluation model. They allow processing large datasets (or infinite streams) without loading the entire collection into memory at once. For SDE-2 roles, you must understand the underlying protocol, the execution model of generators, and how `yield` works.

## Table of Contents

- [Iterable vs Iterator](#iterable-vs-iterator)
- [The Iterator Protocol](#the-iterator-protocol)
- [Generator Functions & `yield`](#generator-functions--yield)
- [Generator Expressions](#generator-expressions)
- [Lazy Evaluation & Memory Efficiency](#lazy-evaluation--memory-efficiency)
- [How `StopIteration` Works](#how-stopiteration-works)
- [Send, Throw, and Close (Advanced Generator Control)](#send-throw-and-close-advanced-generator-control)

---

## Iterable vs Iterator

### Explanation

- **Iterable**: Any object that can return its members one at a time. It implements `__iter__` (which returns an iterator object) or `__getitem__`. Examples: lists, tuples, dicts, strings, sets.
- **Iterator**: An agent representing a stream of data. It implements `__next__` (which returns the next item or raises `StopIteration`) and `__iter__` (which returns `self`).

---

## The Iterator Protocol

### Explanation

Any object that implements the **Iterator Protocol** can be used in a `for` loop. The protocol consists of:
1. `__iter__(self)`: Returns the iterator object itself.
2. `__next__(self)`: Returns the next item. If no items are left, raises `StopIteration`.

### Code example

```python
class ReverseIterator:
    def __init__(self, data):
        self.data = data
        self.index = len(data)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index -= 1
        return self.data[self.index]

rev = ReverseIterator([1, 2, 3])
for item in rev:
    print(item)  # 3, 2, 1
```

---

## Generator Functions & `yield`

### Explanation

A **generator function** is a function containing the `yield` keyword. Calling it returns a **generator object** (a subclass of iterator) without executing the body. When `__next__()` is called, the function executes until it reaches `yield`, yields the value, and **suspends** its execution state (including local variables, instruction pointer, and stack frame).

### Why it matters / internals

- Unlike standard functions whose stack frames are popped when they return, a generator's frame remains alive on the heap, allowing it to resume later.
- This suspension makes generators extremely memory-efficient.

### Code example

```python
def fibonacci(limit):
    a, b = 0, 1
    for _ in range(limit):
        yield a
        a, b = b, a + b

fib = fibonacci(5)
print(next(fib))  # 0
print(next(fib))  # 1
```

---

## Generator Expressions

### Explanation

A generator expression is a compact syntax for creating a generator object. It looks like a list comprehension but uses parentheses `()` instead of brackets `[]`.

```python
# List comprehension (eager)
squares_list = [x*x for x in range(1000000)]  # Allocates memory for 1M ints

# Generator expression (lazy)
squares_gen = (x*x for x in range(1000000))   # Allocates memory for 1 generator object
```

---

## Lazy Evaluation & Memory Efficiency

### Explanation

With eager evaluation (e.g., lists), all values are calculated upfront. With lazy evaluation (e.g., generators), values are calculated on-the-fly when requested.

### Why it matters / internals

Using generators is crucial when:
1. Working with large files (e.g., reading gigabyte log files line-by-line).
2. Representing infinite streams (e.g., live sensor feeds, UUID generation).
3. Piping data processing stages (e.g., filter -> map -> reduce) without intermediate lists.

---

## How `StopIteration` Works

### Explanation

- When an iterator runs out of values, `__next__()` raises a `StopIteration` exception.
- Python `for` loops catch `StopIteration` internally and terminate the loop cleanly.
- PEP 479 changes generator behavior: a `StopIteration` raised inside a generator is transformed into a `RuntimeError` to prevent silent bugs.

---

## Send, Throw, and Close (Advanced Generator Control)

### Explanation

Generators are not just producers; they can also consume data.
- `generator.send(value)`: Resumes the generator and sends a value to the yielding expression.
- `generator.throw(type, value)`: Raises an exception at the point where the generator was suspended.
- `generator.close()`: Raises a `GeneratorExit` exception inside the generator to clean up resources.

### Code example

```python
def consumer():
    print("Consumer started")
    while True:
        val = yield
        print(f"Received: {val}")

c = consumer()
next(c)          # "Prime" the generator (advances to first yield)
c.send("Hello")  # Prints "Received: Hello"
c.send("World")  # Prints "Received: World"
c.close()
```

**Interview question:** Why must you call `next(c)` before the first `send()`? Because the generator must be advanced to its first `yield` expression before it can receive a value there — sending into a freshly-created, un-started generator raises `TypeError: can't send non-None value to a just-started generator`.

---

## `itertools` Module

### Explanation

`itertools` provides fast, memory-efficient building blocks for iterator algebra — combining, filtering, and transforming iterators lazily. Frequently used to avoid manually writing nested loops.

### Key functions with examples

```python
import itertools

# chain: flatten multiple iterables into one
list(itertools.chain([1, 2], [3, 4]))  # [1, 2, 3, 4]

# islice: slice an iterator without consuming it all
list(itertools.islice(range(100), 5))  # [0, 1, 2, 3, 4]

# count: infinite arithmetic sequence
counter = itertools.count(start=10, step=2)
next(counter), next(counter)  # (10, 12)

# cycle: infinite repetition of an iterable
c = itertools.cycle([1, 2, 3])
[next(c) for _ in range(5)]  # [1, 2, 3, 1, 2]

# groupby: group consecutive equal keys (input must be pre-sorted/grouped)
data = [("a", 1), ("a", 2), ("b", 3)]
for key, group in itertools.groupby(data, key=lambda x: x[0]):
    print(key, list(group))
# a [('a', 1), ('a', 2)]
# b [('b', 3)]

# tee: split one iterator into n independent iterators
it1, it2 = itertools.tee(iter([1, 2, 3]), 2)

# accumulate: running totals
list(itertools.accumulate([1, 2, 3, 4]))  # [1, 3, 6, 10]
```

**Trap:** `groupby` only groups *consecutive* matching keys — it does not group globally like a SQL `GROUP BY`; the input must already be sorted by the grouping key or you'll get multiple groups with the same key.

---

## Common Interview Questions

1. **"Is every iterator an iterable?"** Yes — because iterators implement `__iter__` returning `self`, satisfying the iterable protocol too.
2. **"Can you iterate a generator twice?"** No — once exhausted, a generator cannot be reset; you must call the generator function again to get a fresh generator object.
3. **"What's the memory complexity difference between `range(n)` and `list(range(n))`?"** `range` is O(1) space (computes values on demand via `__getitem__`/iteration); `list(range(n))` is O(n) space.
4. **Pitfall:** Passing a generator to `len()` fails — generators don't know their length in advance (`TypeError: object of type 'generator' has no len()`).
