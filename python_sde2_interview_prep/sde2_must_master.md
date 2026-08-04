# SDE-2 Python: High-Priority Must-Master Topics

This guide provides an in-depth exploration of the 20 high-priority Python topics required for SDE-2 interviews. It covers the underlying mechanics, CPython internals, performance implications, and practical code implementations for each topic.

---

## Table of Contents

1. [Object Model (Everything is an Object)](#1-object-model-everything-is-an-object)
2. [Memory Management & Garbage Collection](#2-memory-management--garbage-collection)
3. [Reference Counting](#3-reference-counting)
4. [The Global Interpreter Lock (GIL)](#4-the-global-interpreter-lock-gil)
5. [Threading vs Multiprocessing vs Asyncio](#5-threading-vs-multiprocessing-vs-asyncio)
6. [Async/Await and the Event Loop](#6-asyncawait-and-the-event-loop)
7. [Decorators](#7-decorators)
8. [Closures](#8-closures)
9. [Generators](#9-generators)
10. [Iterators](#10-iterators)
11. [Descriptors](#11-descriptors)
12. [Metaclasses (Basics)](#12-metaclasses-basics)
13. [MRO and Multiple Inheritance](#13-mro-and-multiple-inheritance)
14. [Magic Methods](#14-magic-methods)
15. [Hashing and Dictionary Internals](#15-hashing-and-dictionary-internals)
16. [Shallow vs Deep Copy](#16-shallow-vs-deep-copy)
17. [Mutable vs Immutable Objects](#17-mutable-vs-immutable-objects)
18. [Namespaces and the LEGB Rule](#18-namespaces-and-the-legb-rule)
19. [Bytecode Execution Model](#19-bytecode-execution-model)
20. [Performance Optimization and Profiling](#20-performance-optimization-and-profiling)

---

## 1. Object Model (Everything is an Object)

### Explanation
In Python, class definitions, functions, modules, stack frames, integers, and strings are all first-class objects. Each object resides in memory and has a type, value, and unique identity.

### CPython Internals
Every Python object is represented in CPython by a C structure containing the `PyObject` header:
```c
struct _object {
    _PyObject_HEAD_EXTRA // Doubly-linked list pointer to keep track of all active objects (for debugging/GC)
    Py_ssize_t ob_refcnt;
    struct _typeobject *ob_type;
};
```
- `ob_refcnt`: Reference counter for memory management.
- `ob_type`: Pointer to the type object (e.g., `PyType_Type` for classes), defining how the object behaves.

```python
# Functions are objects
def greet(): pass
print(isinstance(greet, object))  # True
print(greet.__class__)            # <class 'function'>

# Types are objects
print(isinstance(int, object))    # True
print(int.__class__)              # <class 'type'>
```

---

## 2. Memory Management & Garbage Collection

### Explanation
Python uses automatic memory management consisting of two components:
1. **Reference Counting**: The primary deallocation mechanism. Objects are immediately freed when their reference count drops to 0.
2. **Generational Garbage Collector**: Resolves circular references (cycles) among container objects.

### CPython Internals
The cyclic garbage collector runs periodically and categorizes container objects into three generations:
- **Generation 0**: New objects. Checked most frequently. Surviving objects migrate to Gen 1.
- **Generation 1**: Intermediate survival. Checked less frequently. Surviving objects migrate to Gen 2.
- **Generation 2**: Long-lived objects. Checked least frequently.

It uses a double linked list of objects and determines reachability by temporarily subtracting 1 from the reference counts of all referenced objects in the group. If an object's effective reference count drops to 0, it is unreachable from the user namespace and slated for deletion.

---

## 3. Reference Counting

### Explanation
Reference counting tracks the number of pointers referencing an object.
- **Incremented**: Assigning to a variable, adding to a list/dict, passing to a function.
- **Decremented**: Deleting a variable (`del`), leaving a scope, overwriting a variable.

### Code Example
```python
import sys

x = [1, 2, 3]
print(sys.getrefcount(x))  # 2 (x, plus temporary reference in getrefcount argument)

y = x
print(sys.getrefcount(x))  # 3 (x, y, getrefcount argument)
```

---

## 4. The Global Interpreter Lock (GIL)

### Explanation
The GIL is a mutual exclusion lock used by CPython to prevent multiple native threads from executing Python bytecodes at once. It is necessary because CPython's memory management (reference counting) is not thread-safe.

### Performance Profile
- **CPU-Bound Tasks**: Multithreading does **not** provide parallel execution. In fact, it degrades performance due to thread scheduling overhead. Use `multiprocessing` instead.
- **I/O-Bound Tasks**: Threading is efficient because threads release the GIL while waiting for network/disk operations.

---

## 5. Threading vs Multiprocessing vs Asyncio

### Comparison Matrix

| Approach | Concurrency Model | Best For | GIL Impact | Overhead |
| :--- | :--- | :--- | :--- | :--- |
| **Threading** | Preemptive multitasking | I/O-bound tasks | Blocked by GIL | Low memory, medium context switch |
| **Multiprocessing** | OS-level processes | CPU-bound tasks | Bypasses GIL (separate VM per process) | High memory, slow startup |
| **Asyncio** | Cooperative multitasking | Single-threaded high concurrency I/O | Single thread (GIL irrelevant) | Very low memory, fast context switch |

---

## 6. Async/Await and the Event Loop

### Explanation
`asyncio` uses cooperative multitasking. Instead of the OS preemptively swapping threads, the programmer explicitly yields execution back to the **Event Loop** using `await` when waiting on I/O.

### Code Example
```python
import asyncio

async def fetch_data(delay):
    print("Start fetch...")
    await asyncio.sleep(delay)  # Yields control back to the event loop
    print("Done fetch!")
    return {"data": 123}

async def main():
    # Run tasks concurrently in the single thread event loop
    results = await asyncio.gather(fetch_data(1), fetch_data(1))
    print(results)

asyncio.run(main())
```

---

## 7. Decorators

### Explanation
Decorators wrap callable objects to dynamically modify behavior.

### Code Example (Timer Decorator)
```python
import time
from functools import wraps

def time_it(func):
    @wraps(func)  # Preserves func metadata
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        print(f"{func.__name__} took {duration:.4f}s")
        return result
    return wrapper

@time_it
def compute():
    return sum(i * i for i in range(1000000))

compute()
```

---

## 8. Closures

### Explanation
A closure is an inner function that retains references to variables from its outer enclosing scope, even after the outer function has finished executing.

### Code Example (Stateful Counter)
```python
def make_counter():
    count = 0
    def counter():
        nonlocal count  # Modify outer variable
        count += 1
        return count
    return counter

c = make_counter()
print(c())  # 1
print(c())  # 2
```

---

## 9. Generators

### Explanation
Generators are functions that contain `yield`. Instead of returning a single value, they produce a sequence of values lazily, pausing execution and preserving local frame state.

### Code Example
```python
def read_large_file(filepath):
    with open(filepath, "r") as f:
        for line in f:
            yield line.strip()  # Yields one line at a time, keeping memory usage constant
```

---

## 10. Iterators

### Explanation
Iterators implement the **Iterator Protocol**:
1. `__iter__`: Returns the iterator object itself.
2. `__next__`: Returns the next element or raises `StopIteration` if exhausted.

```python
class CountToThree:
    def __init__(self):
        self.num = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.num >= 3:
            raise StopIteration
        self.num += 1
        return self.num

for val in CountToThree():
    print(val)  # 1, 2, 3
```

---

## 11. Descriptors

### Explanation
Descriptors are objects that customize attribute access lookup behavior (`get`, `set`, `delete`) when they are placed as class-level attributes. They are the underlying technology behind `@property`, `@classmethod`, `@staticmethod`, and ORMs.

### Code Example (Type-checked Descriptor)
```python
class NonNegative:
    def __set_name__(self, owner, name):
        self.private_name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name, 0)

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError("Value cannot be negative")
        setattr(instance, self.private_name, value)

class Product:
    price = NonNegative()

p = Product()
p.price = 10  # Ok
# p.price = -5  # Raises ValueError
```

---

## 12. Metaclasses (Basics)

### Explanation
A metaclass is the "class of a class". Standard classes define the behavior of class instances, whereas metaclasses define the behavior of classes themselves (their creation, modification, and namespace).

### Code Example (Auto-registering Metaclass)
```python
class RegistryMeta(type):
    registry = {}

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        if name != "BaseModel":
            cls.registry[name] = new_class
        return new_class

class BaseModel(metaclass=RegistryMeta):
    pass

class User(BaseModel):
    pass

print(RegistryMeta.registry)  # {'User': <class '__main__.User'>}
```

---

## 13. MRO and Multiple Inheritance

### Explanation
Python supports multiple inheritance. When looking up a method, it resolves ambiguity by following the **Method Resolution Order (MRO)**, computed using the **C3 Linearization** algorithm.

### Code Example
```python
class A:
    def execute(self):
        print("A")

class B(A):
    def execute(self):
        print("B")
        super().execute()

class C(A):
    def execute(self):
        print("C")
        super().execute()

class D(B, C):
    pass

print(D.__mro__)  # (D, B, C, A, object)
D().execute()     # Prints D -> B -> C -> A (not B -> A -> C -> A)
```

---

## 14. Magic Methods

### Explanation
Magic (or dunder) methods are special hooks that begin and end with double underscores. They allow custom classes to integrate with built-in language structures.

| Dunder Method | Triggered By |
| :--- | :--- |
| `__new__` | Object instantiation (before `__init__`) |
| `__repr__` | String representations inside REPL, debuggers |
| `__getitem__` | Indexing access `obj[key]` |
| `__enter__` / `__exit__` | Entering/exiting a `with` context |
| `__call__` | Invoking the instance like a function: `obj()` |

---

## 15. Hashing and Dictionary Internals

### Explanation
Python dictionaries are hash tables.
- Keys must be **hashable** (immutable objects implementing `__hash__` and `__eq__`).
- Starting in Python 3.6, dicts are **ordered** and memory-compact. They are implemented using two arrays:
  1. A sparse indices array (containing pointers into the entries array).
  2. A dense entries array containing hash values, keys, and values sequentially.

### Performance
- **Get / Set**: Average case $O(1)$, worst case $O(N)$ (in case of high hash collisions).

---

## 16. Shallow vs Deep Copy

### Explanation
- **Shallow Copy (`copy.copy`)**: Copies the outer container but references the original objects for nested collections.
- **Deep Copy (`copy.deepcopy`)**: Recursively copies both the outer container and all nested child elements.

```python
import copy

orig = [[1, 2]]
shallow = copy.copy(orig)
deep = copy.deepcopy(orig)

orig[0].append(3)
print(shallow)  # [[1, 2, 3]] (Shared inner reference)
print(deep)     # [[1, 2]]    (Fully isolated copy)
```

---

## 17. Mutable vs Immutable Objects

### Explanation
- **Mutable**: Values can change in-place without changing object identity. Examples: `list`, `dict`, `set`, `bytearray`.
- **Immutable**: Once created, the value cannot change. Modifying it returns a new object with a new identity. Examples: `int`, `float`, `str`, `tuple`, `frozenset`.

```python
x = (1, 2)
# x[0] = 99  # TypeError: 'tuple' object does not support item assignment
```

---

## 18. Namespaces and the LEGB Rule

### Explanation
Namespaces are directories of name-to-object bindings. Variables are resolved from inner to outer namespaces following the **LEGB rule**:
- **Local (L)**: Inner function variables.
- **Enclosing (E)**: Surrounding nested function scopes.
- **Global (G)**: Module-level variables.
- **Built-in (B)**: Core language built-ins (e.g., `ValueError`).

---

## 19. Bytecode Execution Model

### Explanation
1. **Source Code** is compiled into **AST** (Abstract Syntax Tree).
2. AST is compiled into **Bytecode** (stored in `.pyc` files inside `__pycache__`).
3. The **Python Virtual Machine (PVM)** interprets the bytecode. It is a stack-based virtual machine.

```python
import dis
def f(x): return x + 1
dis.dis(f)  # Inspect compiler bytecode instructions
```

---

## 20. Performance Optimization and Profiling

### Profiling
Before optimizing, measure using tools:
- `cProfile`: To evaluate call stacks and identify bottlenecks.
- `timeit`: Benchmark small code blocks.

### Optimization Checklist
1. Use local variables instead of global lookups inside tight loops.
2. Leverage `__slots__` to save memory on massive numbers of class instances.
3. Use built-in C-implemented operations (`map`, `filter`, `sum`, list-comprehensions) instead of manual Python loops.
4. Avoid string concatenation using `+` in loops; collect in a list and use `''.join()`.
