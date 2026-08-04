# Decorators

Decorators are clean abstractions that wrap functions or classes to modify or extend their behavior without altering the original code. For SDE-2 interviews, you should be ready to write parameterized decorators, class decorators, and explain how they interact with scope, metadata, and closures.

## Table of Contents

- [Function Decorators](#function-decorators)
- [Class Decorators](#class-decorators)
- [Chaining Decorators](#chaining-decorators)
- [Parameterized Decorators](#parameterized-decorators)
- [Preserving Metadata with `functools.wraps`](#preserving-metadata-with-functoolswraps)

---

## Function Decorators

### Explanation

A function decorator is a callable that accepts a function as an argument and returns a new callable (usually a wrapper function).

When you write:
```python
@my_decorator
def my_func():
    pass
```
Python converts this at definition time to:
```python
my_func = my_decorator(my_func)
```

### Code example

```python
def log_execution(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} completed")
        return result
    return wrapper

@log_execution
def greet(name):
    return f"Hello, {name}"

print(greet("Alice"))
```

---

## Class Decorators

### Explanation

Decorators can also wrap classes. A class decorator takes a class object as its argument and returns a modified class (or a new class entirely). This is often cleaner than using metaclasses for simple registry patterns or attribute additions.

### Code example

```python
def add_repr(cls):
    # Dynamically inject or override __repr__
    cls.__repr__ = lambda self: f"{self.__class__.__name__}({self.__dict__})"
    return cls

@add_repr
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(p)  # Point({'x': 1, 'y': 2})
```

---

## Chaining Decorators

### Explanation

You can apply multiple decorators to a single function. The order of evaluation is **bottom-up** (or inside-out).

When you write:
```python
@dec1
@dec2
def func():
    pass
```
It is equivalent to:
```python
func = dec1(dec2(func))
```

---

## Parameterized Decorators

### Explanation

To pass arguments to a decorator, you must create a **decorator factory**. This is a function that accepts the arguments, and returns the actual decorator, which in turn accepts the target function.

### Code example

```python
def repeat(times):
    def decorator_repeat(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator_repeat

@repeat(times=3)
def greet(name):
    print(f"Hi {name}")

greet("Bob")  # Prints "Hi Bob" 3 times
```

---

## Preserving Metadata with `functools.wraps`

### Explanation

When you wrap a function, the wrapped function's metadata (like its name `__name__`, docstring `__doc__`, and type annotations) is replaced by the wrapper function's metadata.

To prevent this loss of information, always use `@functools.wraps(func)` on the wrapper function.

### Why it matters / internals

- `@wraps` copies attributes like `__name__`, `__doc__`, `__module__`, and `__annotations__` to the wrapper function.
- It also adds the `__wrapped__` attribute, allowing developers to access the original, undecorated function.

### Code example

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def example():
    """This is a docstring."""
    pass

print(example.__name__)  # 'example' (instead of 'wrapper')
print(example.__doc__)   # 'This is a docstring.' (instead of None)
```

---

## Class-based Decorators (using `__call__`)

A class with `__call__` can act as a decorator, useful when the decorator needs to maintain state across calls (e.g., a call counter).

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        print(f"Call #{self.calls} to {self.func.__name__}")
        return self.func(*args, **kwargs)

@CountCalls
def say_hi():
    print("hi")

say_hi(); say_hi()  # Call #1 ...; Call #2 ...
```

## Common Interview Questions

1. **"Write a decorator that only works on instance methods and caches the result per-instance."** Tests understanding of `functools.cached_property` vs a manual descriptor-based cache.
2. **"What's the execution order of stacked decorators — at definition time vs call time?"** Decorators apply bottom-up at *definition* time (`dec1(dec2(func))`), but at *call* time execution happens outside-in (`dec1`'s wrapper code runs first, then calls into `dec2`'s wrapper, then the original function).
3. **Pitfall:** A decorator without `*args, **kwargs` in its wrapper breaks any decorated function that takes different signatures — always forward arguments generically unless intentionally restricting them.
4. **Pitfall:** Class decorators that return a *new* class (instead of mutating in place) change `isinstance` behavior for previously-held references to the original class.
