# Magic (Dunder) Methods

Magic methods (also called dunder methods, for "double underscore") are the mechanism Python uses to let user-defined classes integrate with built-in language syntax and protocols. When you write `a + b`, `len(x)`, `for i in x`, `x[0]`, or `with x:`, Python does not special-case your class — it looks up a corresponding dunder method (`__add__`, `__len__`, `__iter__`, `__getitem__`, `__enter__`) and calls it. This is the basis of Python's "data model" and is a favorite SDE-2 interview topic because it tests whether you understand *how* Python actually executes seemingly simple syntax, not just that it works.

## Table of Contents

- `__init__` and `__new__`
- `__str__` vs `__repr__`
- `__len__`
- `__iter__` and `__next__`
- `__getitem__` and `__setitem__`
- `__contains__`
- `__call__`
- `__enter__` and `__exit__`
- `__eq__` and `__hash__`
- Arithmetic operator overloading

---

## `__init__` and `__new__`

### Explanation

`__new__` and `__init__` are both involved in object construction, but they do different jobs:

- `__new__(cls, ...)` is a **static method** (implicitly) responsible for **creating and returning** a new instance of `cls`. It is called *before* `__init__`.
- `__init__(self, ...)` **initializes** an already-created instance. It must return `None`.

When you write `MyClass(args)`, Python actually does roughly:

```python
obj = MyClass.__new__(MyClass, args)
if isinstance(obj, MyClass):
    MyClass.__init__(obj, args)
return obj
```

### Why it matters / internals

- `__new__` is what you override when subclassing immutable types (`int`, `str`, `tuple`, `frozenset`) because by the time `__init__` runs, the immutable value is already fixed — you must set it during creation in `__new__`.
- `__new__` is also the hook used to implement the Singleton pattern, since it controls whether a *new* object is even created.
- If `__new__` does not return an instance of `cls` (or a subclass), `__init__` is **not** called automatically.
- `object.__new__` and `object.__init__` are the defaults; overriding one without understanding the other is a common source of `TypeError: object.__new__() takes exactly one argument`.

### Code example

```python
class Point(tuple):
    """Immutable point built on top of tuple, customized via __new__."""
    def __new__(cls, x, y):
        return super().__new__(cls, (x, y))

    def __init__(self, x, y):
        # Runs AFTER __new__; tuple contents are already fixed above.
        self.label = f"({x}, {y})"


class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value=None):
        # Careful: __init__ runs every time Singleton() is called,
        # even when __new__ returns the cached instance!
        if value is not None:
            self.value = value


p = Point(3, 4)
print(p, p.label)          # (3, 4) (3, 4)

s1 = Singleton(1)
s2 = Singleton(2)
print(s1 is s2, s1.value)  # True 2  (s1.value got overwritten!)
```

### Common interview questions / gotchas

- "Why can't you set attributes on an immutable subclass in `__init__`?" — because the underlying immutable value must be finalized in `__new__`.
- "What happens if `__new__` returns an object of a different class?" — `__init__` is skipped entirely.
- "Implement a thread-unsafe vs thread-safe Singleton." — expect a follow-up about locking (`threading.Lock`) around `__new__`.
- `__init__` is called **every time** the class is "instantiated" via `()`, even for a cached Singleton — a classic gotcha shown above.

### Pitfalls

- Forgetting `return` in `__new__` (it must return the instance, not `None`).
- Overriding `__new__` without calling `super().__new__(cls, ...)`.
- Assuming `__init__` always runs — it does not if `__new__` returns something not an instance of `cls`.

---

## `__str__` vs `__repr__`

### Explanation

- `__repr__` should return an **unambiguous**, ideally eval-able, developer-facing representation: `repr(obj)`, used by the REPL, debuggers, and containers (e.g., `print([obj])` calls `repr` on each element, not `str`).
- `__str__` should return a **readable**, user-facing string: used by `str(obj)`, `print(obj)`, and f-strings without a format spec.
- If `__str__` is not defined, Python falls back to `__repr__`. The reverse is not true.

### Why it matters / internals

- Interviewers use this to test whether you know the *fallback chain* and the *contract*: `repr` should ideally satisfy `eval(repr(obj)) == obj` for simple types.
- Logging and debugging in production rely heavily on a good `__repr__` — this is a real-world code-quality signal.

### Code example

```python
class Money:
    def __init__(self, amount, currency="USD"):
        self.amount = amount
        self.currency = currency

    def __repr__(self):
        return f"Money({self.amount!r}, {self.currency!r})"

    def __str__(self):
        return f"{self.amount:.2f} {self.currency}"


m = Money(19.999, "USD")
print(str(m))     # 20.00 USD
print(repr(m))    # Money(19.999, 'USD')
print(m)          # 20.00 USD  (print uses __str__)
print([m])        # [Money(19.999, 'USD')]  (list repr uses __repr__ per item)
```

### Common interview questions / gotchas

- "Why does `print([obj])` not use `__str__`?" — containers always use `repr()` on their elements.
- "What is the fallback order?" — `str(obj)` -> `__str__` -> if missing -> `__repr__` -> if missing -> `object.__repr__` (shows `<Class object at 0x...>`).
- Use `!r` inside f-strings/`__repr__` to correctly quote nested strings.

### Pitfalls

- Defining `__str__` but not `__repr__`, leaving debug output as the ugly default `<Money object at 0x7f...>`.
- Making `__repr__` expensive (e.g., DB calls) — it gets invoked implicitly by debuggers/loggers frequently.

---

## `__len__`

### Explanation

`__len__(self)` backs the built-in `len(obj)` and must return a non-negative `int`. It also implicitly affects truthiness: if `__bool__` is not defined, Python uses `bool(len(obj))` to decide truthiness in `if obj:`.

### Why it matters / internals

- CPython's `len()` calls `PyObject_Size`, which looks up `__len__` via the type's slot (`tp_as_sequence->sq_length` or `tp_as_mapping->mp_length`), not by generic attribute lookup — this is why dunder methods must be defined on the **class**, not just the instance (see gotcha below).

### Code example

```python
class Deck:
    def __init__(self, cards):
        self._cards = list(cards)

    def __len__(self):
        return len(self._cards)


d = Deck(range(52))
print(len(d))          # 52
print(bool(Deck([])))  # False, because __len__ returns 0
```

### Common interview questions / gotchas

- "Can `__len__` return a negative number?" — no, raises `ValueError: __len__() should return >= 0`.
- "Why doesn't assigning `obj.__len__ = lambda: 5` on an instance work?" — special methods are looked up on the **type**, bypassing instance `__dict__`, for performance and consistency (implicit invocation uses `type(obj).__len__`).

### Pitfalls

- Very large lengths must fit in `Py_ssize_t` or you'll get `OverflowError`.
- Relying on `__len__` for truthiness while forgetting an explicit `__bool__` might be needed for non-sized objects.

---

## `__iter__` and `__next__`

### Explanation

`__iter__(self)` should return an **iterator** object (which implements `__next__`), enabling `for x in obj:`. `__next__(self)` returns the next value or raises `StopIteration` when exhausted. An object implementing both is itself an iterator (common pattern: `return self` from `__iter__`).

### Why it matters / internals

- This is the **iterator protocol**, the backbone of `for` loops, comprehensions, `*` unpacking, and `next()`. `for x in obj` desugars to calling `iter(obj)` once then `next()` repeatedly until `StopIteration`.
- See file `11_iterators_generators.md` for the full iterable vs iterator distinction and generators as a shortcut for implementing this protocol.

### Code example

```python
class Countdown:
    def __init__(self, start):
        self.start = start

    def __iter__(self):
        self.current = self.start
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1


for n in Countdown(3):
    print(n)   # 3 2 1
```

### Common interview questions / gotchas

- "Difference between iterable and iterator?" — iterable implements `__iter__`; iterator implements both `__iter__` (returning self) and `__next__`.
- "Why can you only loop over a generator once?" — a generator is its own iterator; once exhausted, calling `iter()` on it again returns the same exhausted object.
- Implement a custom range-like class from scratch (classic whiteboard question).

### Pitfalls

- Returning a *new* iterator each time from `__iter__` but keeping shared mutable state (`self.current`) causes bugs when iterating the same object twice concurrently — nested loops over the same instance will interfere with each other.
- Forgetting to raise `StopIteration` causes an infinite loop.

---

## `__getitem__` and `__setitem__`

### Explanation

- `__getitem__(self, key)` backs `obj[key]` (also enables iteration via the old-style protocol if `__iter__` is absent, and slicing when `key` is a `slice` object).
- `__setitem__(self, key, value)` backs `obj[key] = value`.
- There's also `__delitem__(self, key)` for `del obj[key]`.

### Why it matters / internals

- If a class defines `__getitem__` but not `__iter__`, `for x in obj` still works: Python falls back to calling `obj[0]`, `obj[1]`, ... until `IndexError`. This is a legacy protocol interviewers love to probe.
- Supporting `slice` objects lets your class behave like a list/array with `obj[1:5]` syntax.

### Code example

```python
class Matrix:
    def __init__(self, rows):
        self.rows = rows

    def __getitem__(self, key):
        if isinstance(key, tuple):
            r, c = key
            return self.rows[r][c]
        return self.rows[key]   # supports slicing too, since list handles slices

    def __setitem__(self, key, value):
        r, c = key
        self.rows[r][c] = value


m = Matrix([[1, 2], [3, 4]])
print(m[0, 1])   # 2
m[0, 1] = 99
print(m.rows)    # [[1, 99], [3, 4]]
print(m[0])      # [1, 99]  (row slice)
```

### Common interview questions / gotchas

- "How does `for x in obj` work without `__iter__`?" — fallback via `__getitem__(0)`, `__getitem__(1)`, ... until `IndexError`.
- "How do you support `obj[1:3]`?" — Python passes a `slice` object as `key`; you must handle it explicitly if `self.rows` doesn't already support slicing.
- Implement negative indexing support manually — tests understanding that raw dict-like `__getitem__` does NOT get negative indexing for free unless you code it.

### Pitfalls

- Raising the wrong exception type (`KeyError` vs `IndexError`) — this actually changes fallback behavior in `for` loops and `in` checks.
- Forgetting `__delitem__` when `__setitem__` is defined, leaving `del obj[k]` broken.

---

## `__contains__`

### Explanation

`__contains__(self, item)` backs the `in` operator: `item in obj`. If absent, Python falls back to iterating via `__iter__`/`__getitem__` and comparing with `==`.

### Why it matters / internals

- Defining `__contains__` explicitly can turn an O(n) membership check into O(1) (e.g., backed by a `set` or `dict` internally), which is a real performance-relevant interview point.

### Code example

```python
class RangeSet:
    def __init__(self, lo, hi):
        self.lo, self.hi = lo, hi

    def __contains__(self, item):
        return self.lo <= item < self.hi   # O(1) instead of iterating


rs = RangeSet(0, 1_000_000)
print(999_999 in rs)   # True, O(1) check
```

### Common interview questions / gotchas

- "What's the fallback if `__contains__` isn't defined?" — Python iterates the object using `__iter__`/`__getitem__`, O(n).
- "Does `in` use `==` or `is`?" — uses `==` (equality), unless `__contains__` overrides that behavior entirely.

### Pitfalls

- Implementing `__contains__` with O(n) logic while claiming it's an optimization — always verify complexity.
- Inconsistent semantics between `__contains__` and `__iter__` (e.g., `in` says True but iterating never yields the item) confuses users of your class.

---

## `__call__`

### Explanation

`__call__(self, ...)` lets **instances** be called like functions: `obj(args)` invokes `type(obj).__call__(obj, args)`. This makes the object "callable" (`callable(obj)` returns `True`).

### Why it matters / internals

- Used heavily for stateful function-like objects: decorators implemented as classes, memoization caches, ML model wrappers (`model(x)`), and strategy/command patterns.
- All functions and classes are themselves callable via their type's `__call__` (`type.__call__` is what invokes `__new__`/`__init__` when you instantiate a class!).

### Code example

```python
class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, x):
        return x * self.factor


double = Multiplier(2)
print(double(21))         # 42
print(callable(double))   # True


class Memoize:
    """Class-based decorator using __call__."""
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args not in self.cache:
            self.cache[args] = self.func(*args)
        return self.cache[args]


@Memoize
def slow_square(n):
    return n * n


print(slow_square(5), slow_square(5))  # 25 25 (second call is cached)
```

### Common interview questions / gotchas

- "Implement a decorator as a class instead of a function." — expects `__call__` and often `functools.wraps`-equivalent metadata handling.
- "How is instantiating a class (`MyClass()`) related to `__call__`?" — `MyClass` is an instance of `type`, so `MyClass()` invokes `type.__call__`, which in turn calls `__new__` then `__init__`.

### Pitfalls

- Forgetting that class-based decorators break `functools.wraps`-style introspection (`__name__`, `__doc__`) unless manually forwarded.
- Mutable shared cache state (as in `Memoize`) can leak across unrelated call sites if the decorated function is reused unexpectedly.

---

## `__enter__` and `__exit__`

### Explanation

These implement the **context manager protocol** used by `with` statements.

- `__enter__(self)` runs at the start of the `with` block and its return value is bound to the `as` target.
- `__exit__(self, exc_type, exc_val, exc_tb)` runs when the block exits, whether normally or via exception. Returning a **truthy** value from `__exit__` **suppresses** the exception; returning falsy (or `None`) lets it propagate.

### Why it matters / internals

- Guarantees deterministic cleanup (closing files, releasing locks, closing DB connections) even in the presence of exceptions — a robust replacement for manual `try/finally`.
- See `12_exception_handling.md` for `contextlib.contextmanager`, a generator-based shortcut for building context managers without writing a class.

### Code example

```python
class ManagedFile:
    def __init__(self, path, mode):
        self.path, self.mode = path, mode

    def __enter__(self):
        self.file = open(self.path, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        if exc_type is ValueError:
            print(f"Suppressing ValueError: {exc_val}")
            return True   # suppress only ValueError
        return False      # propagate everything else


with ManagedFile("/tmp/example.txt", "w") as f:
    f.write("hello")
    raise ValueError("oops")   # suppressed by __exit__

print("Execution continues here")
```

### Common interview questions / gotchas

- "What does returning `True` from `__exit__` do?" — suppresses the exception raised inside the `with` block.
- "Is `__exit__` guaranteed to run if the code inside `with` raises?" — yes, exactly like `finally`.
- "Write a context manager for measuring elapsed time / DB transactions with rollback on error."

### Pitfalls

- Accidentally suppressing **all** exceptions by unconditionally `return True` in `__exit__` — silently hides bugs.
- Not closing resources in `__exit__` if `__enter__` itself partially failed (needs careful handling, sometimes via nested try/except in `__enter__`).
- Forgetting `__exit__` must accept exactly 3 positional args besides `self`.

---

## `__eq__` and `__hash__`

### Explanation

- `__eq__(self, other)` backs `==`. Default (`object.__eq__`) is identity comparison (`is`).
- `__hash__(self)` backs `hash(obj)`, used by `dict`/`set` for bucket placement. Must satisfy: **if `a == b`, then `hash(a) == hash(b)`**.
- **Critical rule:** if you define `__eq__` without defining `__hash__`, Python automatically sets `__hash__` to `None`, making instances **unhashable** (cannot be put in a `set` or used as `dict` keys).

### Why it matters / internals

- This directly affects whether your objects can be used in hash-based collections, and is a very common real-world bug source (`TypeError: unhashable type`).
- `dataclasses` handle this automatically: `@dataclass(eq=True, frozen=True)` generates both consistently; `@dataclass(eq=True)` (default, mutable) sets `__hash__ = None`.

### Code example

```python
class Point:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


p1, p2 = Point(1, 2), Point(1, 2)
print(p1 == p2)              # True
print(p1 is p2)              # False
print({p1, p2})              # {Point(1, 2)}  -- deduped because eq+hash agree
print(len({p1, p2}))         # 1
```

### Common interview questions / gotchas

- "Why does defining `__eq__` alone break `set`/`dict` usage?" — Python sets `__hash__` to `None` automatically to prevent violating the hash/eq contract by accident.
- "Should mutable objects define `__hash__`?" — generally no; if fields used in `__hash__` change after insertion into a set, the object becomes "lost" (still in the set's bucket for the old hash, but lookups with the new hash fail).
- "What should `__eq__` return when types don't match?" — `NotImplemented` (not `False`), so Python can try the reflected comparison on the other operand.

### Pitfalls

- Implementing `__hash__` using mutable fields — corrupts sets/dicts if the object mutates after being hashed.
- Returning `False` instead of `NotImplemented` from `__eq__` for unrelated types — breaks symmetric comparisons in some edge cases.
- Forgetting `__slots__` classes still need explicit `__eq__`/`__hash__` if defaults aren't wanted.

---

## Arithmetic operator overloading (`__add__`, `__sub__`, `__mul__`, `__radd__`, `__iadd__`, etc.)

### Explanation

Python maps operators to dunder methods:

| Operator | Method | Reflected (right-side) | In-place |
|---|---|---|---|
| `+` | `__add__` | `__radd__` | `__iadd__` |
| `-` | `__sub__` | `__rsub__` | `__isub__` |
| `*` | `__mul__` | `__rmul__` | `__imul__` |
| `/` | `__truediv__` | `__rtruediv__` | `__itruediv__` |
| `//` | `__floordiv__` | `__rfloordiv__` | `__ifloordiv__` |
| `%` | `__mod__` | `__rmod__` | `__imod__` |
| `**` | `__pow__` | `__rpow__` | `__ipow__` |

For `a + b`: Python first tries `a.__add__(b)`. If that returns `NotImplemented` (e.g., type mismatch), Python tries `b.__radd__(a)`. If both fail, `TypeError` is raised. There's a special rule: if `type(b)` is a **subclass** of `type(a)` and overrides `__radd__`, Python tries `b.__radd__(a)` **first**.

`__iadd__` backs `a += b` — if defined, it should mutate `a` in place and return `self` (used for mutable types like `list`). If **not** defined, `a += b` falls back to `a = a.__add__(b)` (creating a new object) — this is why `+=` behaves differently for `list` (mutates) vs `tuple`/`int` (rebinds).

### Why it matters / internals

- Operator overloading is how libraries like NumPy, `datetime`, `Decimal`, and `fractions.Fraction` provide natural mathematical syntax.
- Understanding the `NotImplemented` vs `False`/exception distinction is essential — returning the wrong thing breaks Python's dispatch to the reflected method.
- `__iadd__` vs `__add__` distinction explains a classic gotcha: `l1 = l2 = [1]; l1 += [2]` mutates the object both names point to, while `l1 = l1 + [2]` does not.

### Code example

```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, other):
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        # Enables sum([v1, v2, v3]) which starts with 0 + v1
        if other == 0:
            return self
        return NotImplemented

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __mul__(self, scalar):
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__   # 2 * v works the same as v * 2

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"


v1, v2 = Vector(1, 2), Vector(3, 4)
print(v1 + v2)          # Vector(4, 6)
print(sum([v1, v2]))    # Vector(4, 6), uses __radd__ with other=0
print(2 * v1)           # Vector(2, 4), uses __rmul__

v1 += v2                # calls __iadd__, mutates v1 in place
print(v1)                # Vector(4, 6)

try:
    v1 + 5
except TypeError as e:
    print("TypeError:", e)   # NotImplemented from both sides -> TypeError
```

### Common interview questions / gotchas

- "Why does `a += b` behave differently for lists vs tuples?" — lists define `__iadd__` (mutates), tuples/ints don't (falls back to `__add__`, creating a new object and rebinding the name).
- "What should you return from `__add__` for an unsupported type?" — `NotImplemented`, never raise `TypeError` directly (that prevents Python from trying the reflected method on the other operand).
- "How does `sum()` work with custom objects?" — `sum` starts with `0` by default, so your class needs `__radd__` to handle `0 + obj`.
- Implement a `Fraction`/`Money` class supporting `+`, `-`, `*`, comparisons, and explain precision/type-coercion pitfalls.

### Pitfalls

- Returning `False` or raising inside `__add__` for unsupported operand types instead of `NotImplemented` — breaks the reflected-method fallback mechanism.
- Defining `__iadd__` but forgetting to `return self` — `+=` will silently rebind the name to `None`.
- Mutating `self` in `__add__` (should be pure, returning a new object) versus intentionally mutating in `__iadd__` — mixing these up causes surprising aliasing bugs.
- Forgetting `__radd__`/`__rmul__` when the left operand won't recognize your type (e.g., `5 * my_obj` when `int.__mul__` doesn't know about `my_obj`).
