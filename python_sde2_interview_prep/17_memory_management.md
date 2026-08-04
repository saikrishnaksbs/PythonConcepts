# Memory Management

Python manages memory automatically, but an SDE-2 must understand its underlying mechanisms to prevent memory leaks, optimize memory layout, and debug high-memory usage in production. CPython's memory management relies on two primary pillars: **Reference Counting** and a **Generational Cyclic Garbage Collector**.

## Table of Contents

- [Reference Counting](#reference-counting)
- [Generational Garbage Collection (GC)](#generational-garbage-collection-gc)
- [Cyclic References](#cyclic-references)
- [Weak References (`weakref`)](#weak-references-weakref)
- [Small Object Allocator (PyMalloc)](#small-object-allocator-pymalloc)
- [Common Memory Leaks in Python](#common-memory-leaks-in-python)

---

## Reference Counting

### Explanation

Every object in CPython contains a field in its C header (`ob_refcnt`) that tracks how many references point to it.
- When an object is bound to a variable, added to a container, or passed to a function, its reference count increases.
- When a variable goes out of scope, is reassigned, or deleted, the reference count decreases.
- When the reference count drops to **exactly zero**, CPython immediately deallocates the object's memory.

### Why it matters / internals

- Reference counting is deterministic and handles the vast majority of memory deallocations instantly.
- `sys.getrefcount(obj)` returns the object's reference count. Note: calling this function increases the reference count by 1 temporarily because the object is passed as an argument.

### Code example

```python
import sys

a = []
print(sys.getrefcount(a))  # 2 (variable 'a' and argument to getrefcount)

b = a
print(sys.getrefcount(a))  # 3 (a, b, and argument)

del b
print(sys.getrefcount(a))  # 2
```

---

## Generational Garbage Collection (GC)

### Explanation

Reference counting alone cannot detect **cyclic references** (objects that reference each other). To clean these up, CPython uses a cyclic garbage collector that runs periodically in the background.

The collector groups objects into three generations (Generation 0, 1, and 2) based on survival history:
- **Generation 0**: Newly created objects. This generation is collected most frequently.
- If an object survives a collection of Generation 0, it is promoted to **Generation 1**.
- If it survives a collection of Generation 1, it is promoted to **Generation 2** (collected least frequently).

### Why it matters / internals

- The GC only tracks container objects (lists, dicts, tuples, custom classes) because simple types like integers or strings cannot create cycles.
- It works by finding all reachable objects using a graph traversal, determining which objects are only reachable via circular references, and clearing them.
- You can control the collector using the `gc` module: `gc.collect()`, `gc.disable()`, `gc.set_threshold()`.

---

## Cyclic References

### Explanation

A cyclic reference occurs when two or more objects refer to each other, forming a loop. Their reference counts never drop to zero, even if they are no longer accessible from your code's execution scope.

### Code example

```python
import gc

class Node:
    def __init__(self):
        self.ref = None

# Enable GC debugging to see what gets collected
gc.set_debug(gc.DEBUG_SAVEALL)

n1 = Node()
n2 = Node()
n1.ref = n2
n2.ref = n1  # Cycle created!

del n1
del n2       # Objects are unreachable, but ob_refcnt is still 1 for both!

# Force a garbage collection
gc.collect()
# The cycle is detected and cleaned up by the cyclic GC.
```

---

## Weak References (`weakref`)

### Explanation

A **weak reference** allows you to reference an object without increasing its reference count. If the only remaining references to an object are weak, the object is deallocated, and the weak reference automatically returns `None` or raises an exception.

### Why it matters / internals

- Used for implementing caches (like `weakref.WeakValueDictionary`) so that cached objects can be garbage collected when they are no longer referenced elsewhere in the application.

### Code example

```python
import weakref

class LargeObject:
    pass

obj = LargeObject()
r = weakref.ref(obj)

print(r())  # <__main__.LargeObject object at 0x...>

del obj
print(r())  # None (Automatically cleared!)
```

---

## Small Object Allocator (PyMalloc)

### Explanation

Frequently allocating and freeing small chunks of memory via the OS (`malloc` / `free`) causes memory fragmentation and performance overhead.

### Why it matters / internals

- CPython uses **PyMalloc** for objects smaller than or equal to 512 bytes.
- It pre-allocates large blocks of memory (called Arenas, containing Pools of Blocks) and manages allocations internally.
- Larger objects (> 512 bytes) bypass PyMalloc and go directly to the standard system allocator.

---

## Common Memory Leaks in Python

### Explanation

Even with automatic memory management, memory leaks occur when references to unused objects are kept alive unintentionally:
1. **Global variables/static attributes**: Objects appended to module-level lists or stored in global dictionaries.
2. **Growing caches**: Caches (like a raw dictionary or a custom cache without eviction policies or weak references) that grow indefinitely.
3. **Circular references with custom `__del__` methods (Pre-Python 3.4)**: Before PEP 442, Python could not safely garbage collect cycles if any object in the cycle had a `__del__` method, leaving them permanently in `gc.garbage`. (Fixed in Python 3.4+).
4. **Unbounded `lru_cache`/memoization**: caching function results keyed by large or ever-growing argument sets without a `maxsize` keeps every result alive forever.
5. **Closures capturing large objects**: a closure or decorator that captures an entire object (instead of just the field it needs) keeps that whole object alive as long as the closure exists.

## Object Lifetime & `sys.getsizeof`

```python
import sys

print(sys.getsizeof(0))          # ~28 bytes (small int overhead)
print(sys.getsizeof("hello"))    # str object overhead + chars
print(sys.getsizeof([]))         # empty list overhead
```

`sys.getsizeof` reports only the shallow size of the object itself (not nested objects) — for real memory profiling of an object graph use `tracemalloc` or third-party tools like `pympler`.

## Common Interview Questions

1. **"Why does CPython use both reference counting and a cyclic GC?"** Refcounting gives immediate, deterministic cleanup for the common case (no cycles); the cyclic GC exists solely to catch what refcounting structurally cannot — reference cycles.
2. **"How would you find a memory leak in a long-running Python service?"** Use `tracemalloc.take_snapshot()` at intervals and diff snapshots, or `gc.get_objects()`/`objgraph` to find growing object counts by type.
3. **Pitfall:** Calling `gc.disable()` to "improve performance" removes cycle collection entirely — cyclic garbage accumulates unboundedly until the process is restarted.
