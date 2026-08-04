# Python Interview Favorites & Gotchas

Rapid-fire reference for the questions and traps interviewers reach for most often at SDE-2 level. Each item: crisp answer, a minimal code example showing the gotcha, and the trap being tested.

---

## 1. Mutable Default Arguments

**Answer:** Default argument values are evaluated once, at function *definition* time, and reused on every call. A mutable default (list/dict/set) is shared and accumulates state across calls.

```python
def append_to(val, lst=[]):
    lst.append(val)
    return lst

print(append_to(1))  # [1]
print(append_to(2))  # [1, 2]  <- unexpected, same list object
```

**Fix:** `def append_to(val, lst=None): lst = [] if lst is None else lst`

**Trap:** Interviewer wants you to explain *why* (function objects store defaults once in `__defaults__`), not just recite the fix.

---

## 2. Late-Binding Closures

**Answer:** Closures capture variables by reference to the enclosing scope, not by value at creation time. A loop variable captured in a lambda/function resolves to its final value when the closures are actually called.

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])  # [2, 2, 2], not [0, 1, 2]
```

**Fix:** Default-argument binding: `lambda i=i: i`, or a factory function that captures `i` in its own scope.

**Trap:** Confusing this with "closures capture by value" (wrong) — Python closures capture the *variable*, not a snapshot.

---

## 3. LEGB Rule

**Answer:** Name resolution order for variables: **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in.

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)  # local
    inner()

outer()
```

**Trap:** `global` and `nonlocal` keywords change *assignment* target, not lookup order. Forgetting `nonlocal` when mutating an enclosing variable causes `UnboundLocalError`.

---

## 4. `is` vs `==`

**Answer:** `==` calls `__eq__` and checks value equality. `is` checks identity (`id(a) == id(b)`, same object in memory).

```python
a = [1, 2]
b = [1, 2]
print(a == b)  # True
print(a is b)  # False

x, y = 256, 256
print(x is y)  # True  -- small int cache [-5, 256]
x, y = 257, 257
print(x is y)  # False (usually) -- outside cache range
```

**Trap:** Never use `is` to compare values (especially ints/strings) except for `None`, `True`, `False`, or sentinel singletons — `is` behavior on cached small ints/strings is a CPython implementation detail, not a language guarantee.

---

## 5. Deep vs Shallow Copy

**Answer:** Shallow copy (`copy.copy`, `list(x)`, `x[:]`) creates a new container but keeps references to the same nested objects. Deep copy (`copy.deepcopy`) recursively copies everything.

```python
import copy
original = [[1, 2], [3, 4]]
shallow = copy.copy(original)
deep = copy.deepcopy(original)
original[0][0] = 99
print(shallow[0][0])  # 99 -- shared inner list
print(deep[0][0])     # 1  -- isolated
```

**Trap:** Assuming `list(x)` fully copies nested mutable structures.

---

## 6. `__slots__`

**Answer:** `__slots__` declares a fixed set of attributes for a class, replacing the per-instance `__dict__` with fixed-size slot descriptors. Saves memory (no dict overhead per instance) and prevents adding arbitrary new attributes.

```python
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x, self.y = x, y

p = Point(1, 2)
p.z = 3  # AttributeError: no __dict__
```

**Trap:** `__slots__` breaks multiple inheritance from classes that each define non-empty slots, and instances lose `__dict__`/`__weakref__` unless explicitly included.

---

## 7. Monkey Patching

**Answer:** Modifying or replacing attributes/methods of a module, class, or object at runtime, without touching original source. Common in testing (mocking) but risky in production code.

```python
import math
math.sin = lambda x: 0.0  # patched at runtime
```

**Trap:** Interviewer wants awareness of the danger — global, hard-to-trace side effects — and the legitimate use case (test doubles via `unittest.mock.patch`).

---

## 8. Method Overloading Workaround

**Answer:** Python doesn't support compile-time method overloading (same name, different signature) — the last definition wins. Use default/keyword arguments, `*args`/`**kwargs`, or `functools.singledispatch` for type-based dispatch.

```python
from functools import singledispatch

@singledispatch
def process(data):
    raise TypeError("unsupported")

@process.register(int)
def _(data): return f"int: {data}"

@process.register(str)
def _(data): return f"str: {data}"
```

**Trap:** Saying "Python doesn't support overloading" without naming the idiomatic workaround.

---

## 9. Method Overriding

**Answer:** A subclass redefines a method with the same signature to change behavior. Always available (no keyword needed); use `super()` to call the parent's implementation.

```python
class Animal:
    def speak(self): return "..."

class Dog(Animal):
    def speak(self):
        return super().speak() + " Woof"
```

**Trap:** Confusing overriding (subclass, runtime polymorphism) with overloading (same class, multiple signatures — not natively supported).

---

## 10. Diamond Problem

**Answer:** Ambiguity in multiple inheritance when two parent classes share a common ancestor, and it's unclear which parent's method/attribute wins. Python resolves it deterministically via MRO (C3 linearization).

```python
class A:
    def hello(self): return "A"
class B(A):
    def hello(self): return "B"
class C(A):
    def hello(self): return "C"
class D(B, C):
    pass

print(D().hello())     # "B" -- follows MRO
print(D.__mro__)       # (D, B, C, A, object)
```

**Trap:** Expecting depth-first left-to-right like old-style classes; C3 linearization is different and guarantees a consistent order respecting each parent's own MRO.

---

## 11. MRO (Method Resolution Order)

**Answer:** The order Python searches classes for an attribute/method in multiple inheritance, computed via the C3 linearization algorithm. Inspect with `ClassName.__mro__` or `ClassName.mro()`.

```python
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass
print(D.mro())  # [D, B, C, A, object]
```

**Trap:** `super()` follows MRO, not the literal parent class — in cooperative multiple inheritance, `super().__init__()` may call a "sibling" class's `__init__`, not necessarily the immediate base.

---

## 12. Descriptors

**Answer:** Objects implementing `__get__`, `__set__`, or `__delete__` that customize attribute access when placed as a class attribute. Data descriptors (define `__set__`) take priority over instance `__dict__`; non-data descriptors (only `__get__`, e.g. functions) do not.

```python
class Celsius:
    def __get__(self, obj, owner):
        return obj._celsius
    def __set__(self, obj, value):
        obj._celsius = value

class Weather:
    temp = Celsius()

w = Weather()
w.temp = 25
print(w.temp)  # 25
```

**Trap:** `property` is implemented using the descriptor protocol — know that functions themselves are non-data descriptors, which is *how bound methods work*.

---

## 13. Metaclasses

**Answer:** A metaclass is "the class of a class" — it controls class creation. Default metaclass is `type`. Override `__new__`/`__init__` on a metaclass to customize how classes (not instances) are built.

```python
class Meta(type):
    def __new__(mcs, name, bases, ns):
        ns["greeting"] = "hi"
        return super().__new__(mcs, name, bases, ns)

class Foo(metaclass=Meta):
    pass

print(Foo.greeting)  # hi
```

**Trap:** "Use a metaclass" is rarely the right answer in production — mention `__init_subclass__` and class decorators as simpler alternatives for most use cases.

---

## 14. Generators vs Iterators

**Answer:** An iterator is any object implementing `__iter__` and `__next__`. A generator is a convenient way to *create* an iterator using `yield` (or a generator expression) — every generator is an iterator, but not vice versa.

```python
def gen():
    yield 1
    yield 2

g = gen()
print(next(g), next(g))  # 1 2
print(iter(g) is g)      # True -- generators are their own iterator
```

**Trap:** Iterators can be written manually (custom `__next__`) for more control (e.g., resettable state); generators are simpler but single-pass and can't be "rewound."

---

## 15. List vs Tuple

**Answer:** Lists are mutable, dynamic arrays; tuples are immutable, fixed-size sequences. Tuples are hashable (if elements are), slightly faster to create/iterate, and usable as dict keys; lists are not hashable.

```python
t = (1, 2, 3)
l = [1, 2, 3]
d = {t: "ok"}       # works
# d = {l: "fail"}   # TypeError: unhashable type: 'list'
```

**Trap:** Tuples aren't "always faster" in every op — the real distinguishing feature interviewers want is immutability/hashability, not raw speed.

---

## 16. List vs Set

**Answer:** Lists preserve order and allow duplicates with O(n) membership testing. Sets are unordered (insertion order not guaranteed), disallow duplicates, and give O(1) average membership testing via hashing.

```python
big_list = list(range(100000))
big_set = set(big_list)
99999 in big_list  # O(n)
99999 in big_set   # O(1) average
```

**Trap:** Sets require hashable elements; can't store lists/dicts inside a set.

---

## 17. Dict Internals

**Answer:** CPython dicts are hash tables with open addressing. Since 3.7, insertion order is preserved (guaranteed by the language spec, not just a CPython detail) via a compact representation (separate dense array + sparse index table). Average O(1) get/set/delete; worst case O(n) with many hash collisions.

```python
d = {}
d["b"] = 1
d["a"] = 2
print(list(d))  # ['b', 'a'] -- insertion order preserved
```

**Trap:** Resizing/rehashing happens automatically as load factor grows; don't mutate dict size while iterating (`RuntimeError: dictionary changed size during iteration`).

---

## 18. Hash Tables

**Answer:** Data structure mapping keys to buckets via a hash function for average O(1) lookup. Collisions handled via open addressing (CPython) or chaining (other implementations). Requires keys to be hashable and support equality consistent with their hash.

```python
class Bad:
    def __hash__(self): return 1  # always collides -- degrades to O(n)
```

**Trap:** A poor `__hash__` (e.g., constant) is technically legal but destroys performance — know that `hash(a) == hash(b)` is required (not sufficient) for `a == b`.

---

## 19. String Interning

**Answer:** CPython caches certain string objects so identical literals share memory — identifiers/short strings that look like Python identifiers are typically interned automatically; you can force it with `sys.intern()`.

```python
a = "hello"
b = "hello"
print(a is b)  # True -- interned automatically (compile-time constant)

import sys
c = sys.intern("hello world!")
d = sys.intern("hello world!")
print(c is d)  # True -- explicitly interned
```

**Trap:** Interning is an optimization detail, not a guarantee — never rely on `is` for string equality in portable code.

---

## 20. Memory Optimization

**Answer:** Key techniques: `__slots__` to remove per-instance `__dict__`; generators/iterators instead of building full lists; `array`/`numpy` for homogeneous numeric data; string interning; `sys.getsizeof` and `tracemalloc` for profiling; avoiding unnecessary copies (slicing, concatenation in loops).

```python
import sys
print(sys.getsizeof([1, 2, 3]))   # list overhead
print(sys.getsizeof((1, 2, 3)))   # tuple: smaller
```

**Trap:** "Just use less memory" isn't an answer — name concrete tools (`tracemalloc`, `__slots__`, generators) and trade-offs (readability, flexibility lost).

---

## 21. GIL

**Answer:** The Global Interpreter Lock ensures only one thread executes Python bytecode at a time in CPython, simplifying memory management (refcounting) at the cost of true parallel CPU-bound multithreading.

```python
# CPU-bound: threading doesn't help due to GIL
# I/O-bound: threading helps because GIL is released during I/O waits
```

**Trap:** GIL doesn't prevent concurrency for I/O-bound work — only for CPU-bound parallel *execution* of Python bytecode across threads. PEP 703 (Python 3.13+) allows an optional GIL-free build.

---

## 22. Async vs Threading vs Multiprocessing

**Answer:**
- `asyncio`: single-threaded cooperative concurrency, best for I/O-bound with many concurrent connections, no parallel CPU use, avoids thread-safety issues via explicit `await` points.
- `threading`: OS threads, good for I/O-bound (GIL released during I/O), not for CPU-bound due to GIL.
- `multiprocessing`: separate processes, true CPU parallelism (own GIL/interpreter each), higher memory/IPC overhead.

```python
# CPU-bound -> multiprocessing.Pool
# I/O-bound, few connections -> threading
# I/O-bound, thousands of connections -> asyncio
```

**Trap:** Picking threading for a CPU-bound task (matrix math, image processing) — no speedup due to the GIL; should use multiprocessing or release the GIL in C extensions (numpy).

---

## 23. Context Managers

**Answer:** Objects implementing `__enter__`/`__exit__` (or generator-based via `@contextlib.contextmanager`) used with `with` to guarantee setup/teardown (closing files, releasing locks) even on exceptions.

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    print("acquire")
    try:
        yield "resource"
    finally:
        print("release")

with managed_resource() as r:
    print(r)
```

**Trap:** `__exit__` returning `True` suppresses the exception — a common source of silently swallowed bugs if done unintentionally.

---

## 24. Decorators

**Answer:** Higher-order functions that wrap another function/class to add behavior without modifying its source. Use `functools.wraps` to preserve metadata (`__name__`, `__doc__`).

```python
from functools import wraps

def logged(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper

@logged
def add(a, b): return a + b
```

**Trap:** Forgetting `@wraps` breaks introspection (`help()`, debugging tools, other decorators relying on `__name__`).

---

## 25. Dataclasses

**Answer:** `@dataclass` auto-generates `__init__`, `__repr__`, `__eq__` (and optionally ordering/`__hash__`) from type-annotated class attributes, reducing boilerplate versus manually written classes.

```python
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Point:
    x: int
    y: int

p1, p2 = Point(1, 2), Point(1, 2)
print(p1 == p2)  # True (auto __eq__)
```

**Trap:** Mutable default values still need `field(default_factory=...)` — a bare mutable default raises `ValueError` in dataclasses (safer than plain classes, which silently share state).

---

## 26. NamedTuple

**Answer:** A tuple subclass with named fields — immutable, lightweight, indexable by position or name. `typing.NamedTuple` also supports type annotations.

```python
from typing import NamedTuple

class Point(NamedTuple):
    x: int
    y: int

p = Point(1, 2)
print(p.x, p[0])  # 1 1
```

**Trap:** Still immutable like a tuple — `p.x = 5` raises `AttributeError`; use `p._replace(x=5)` to get a modified copy.

---

## 27. Type Hinting

**Answer:** Annotations (`def f(x: int) -> str`) that document intended types for tooling (mypy, IDEs) — not enforced at runtime by the interpreter itself.

```python
def greet(name: str) -> str:
    return "hi " + name

greet(123)  # no runtime error, but a type checker flags it
```

**Trap:** Assuming type hints are enforced — they're purely advisory unless you add explicit runtime validation (e.g., pydantic, manual `isinstance` checks).

---

## 28. Walrus Operator (`:=`)

**Answer:** Assignment expression introduced in 3.8 — assigns and returns a value in the same expression, useful in comprehensions/while loops to avoid recomputation.

```python
data = [1, 2, 3, 4, 5]
if (n := len(data)) > 3:
    print(f"list too long ({n})")

while (chunk := input_stream.read(1024)):
    process(chunk)
```

**Trap:** Can't use bare `:=` at the top level of a statement (`x := 5` alone is a `SyntaxError`) — must be inside an expression context (parens, if/while condition).

---

## 29. Pattern Matching (`match`/`case`)

**Answer:** Structural pattern matching (3.10+) — matches value shape (type, sequence structure, mapping keys), not just equality; supports guards and capture patterns.

```python
def handle(cmd):
    match cmd:
        case ["move", x, y]:
            return f"move to {x},{y}"
        case ["quit"]:
            return "bye"
        case {"action": "set", "key": k, "value": v}:
            return f"set {k}={v}"
        case _:
            return "unknown"
```

**Trap:** `case` patterns can shadow variables via capture — a bare name (`case x:`) always matches and binds, it does not compare against an existing variable named `x` (use `case SomeClass.CONST:` or guards `if x == existing` for value comparison).

---

## 30. f-String Internals

**Answer:** f-strings are compiled at parse time into `str.__format__` calls embedded directly in bytecode — faster than `%`-formatting or `.format()` since there's no runtime parsing of the format string.

```python
name = "world"
print(f"hello {name!r} {1+1}")  # expressions evaluated inline, hello 'world' 2
```

**Trap:** f-strings can't easily be used as reusable templates (the expression is bound at the point of definition) — for deferred/reusable templates use `.format()` or `string.Template`.

---

## 31. Garbage Collection

**Answer:** CPython primarily uses reference counting for deterministic deallocation, plus a generational cyclic garbage collector (`gc` module) to detect and collect reference cycles that refcounting alone can't free.

```python
import gc

class Node:
    def __init__(self): self.ref = None

a, b = Node(), Node()
a.ref, b.ref = b, a  # cycle
del a, b
gc.collect()  # reclaims the cycle
```

**Trap:** Objects with `__del__` in reference cycles used to be uncollectable pre-3.4; modern CPython (3.4+) can collect them, but relying on `__del__` timing is still fragile.

---

## 32. Reference Counting

**Answer:** Every object tracks how many references point to it (`sys.getrefcount`); when the count hits zero, CPython immediately deallocates it — this is why simple objects get freed deterministically without waiting for a GC pass.

```python
import sys
a = []
print(sys.getrefcount(a))  # baseline count (includes temp ref from getrefcount call itself)
b = a
print(sys.getrefcount(a))  # +1
```

**Trap:** Refcounting alone cannot free reference cycles (two objects referencing each other) — that's what the generational `gc` handles.

---

## 33. Weak References

**Answer:** `weakref` lets you reference an object without increasing its refcount, so it can still be garbage collected — useful for caches/observers that shouldn't keep objects alive.

```python
import weakref

class Data: pass
d = Data()
r = weakref.ref(d)
print(r())  # <Data object>
del d
print(r())  # None -- object was collected
```

**Trap:** Not all objects support weak references by default (e.g., plain `int`, `list` don't unless the class defines `__weakref__` slot, which normal classes have automatically but `__slots__` classes must opt in to).

---

## 34. Circular References

**Answer:** Two or more objects referencing each other, keeping refcounts above zero even when unreachable externally. The generational GC (not simple refcounting) is needed to detect and collect these.

```python
class Node:
    def __init__(self):
        self.next = None

a, b = Node(), Node()
a.next, b.next = b, a
del a, b  # not collected until gc.collect() runs (or next automatic cycle)
```

**Trap:** Fix proactively with `weakref` (e.g., parent-child or doubly-linked structures) rather than relying on the cyclic collector, especially in performance-sensitive code.

---

## 35. Bytecode Inspection (`dis`)

**Answer:** The `dis` module disassembles Python functions/code objects into CPython bytecode instructions — useful for understanding performance or exact semantics (e.g., closures, comprehension scoping).

```python
import dis

def add(a, b):
    return a + b

dis.dis(add)
# LOAD_FAST  a
# LOAD_FAST  b
# BINARY_ADD (or BINARY_OP depending on version)
# RETURN_VALUE
```

**Trap:** Bytecode is CPython-version-specific and an implementation detail — never write code that depends on exact bytecode output; use `dis` for understanding/debugging only.

---

## 36. Object Lifecycle

**Answer:** `__new__` (allocates and returns the instance) runs before `__init__` (initializes it). Object destruction is triggered by refcount reaching zero (or GC for cycles), calling `__del__` if defined, before memory is reclaimed.

```python
class Foo:
    def __new__(cls, *a, **kw):
        print("new")
        return super().__new__(cls)
    def __init__(self):
        print("init")
    def __del__(self):
        print("del")

f = Foo()
del f
```

**Trap:** `__new__` must return an instance of `cls` (or a subclass) for `__init__` to run automatically — returning something else (or an instance of an unrelated class) skips `__init__`.

---

## 37. Import System

**Answer:** `import` triggers the import machinery: check `sys.modules` cache → find the module via finders/loaders (`sys.meta_path`) → execute the module code once → cache it in `sys.modules`. Re-imports reuse the cached module object.

```python
import sys
import json
print("json" in sys.modules)  # True after first import
```

**Trap:** Circular imports fail or yield partially-initialized modules — because the importing module is added to `sys.modules` *before* its body finishes executing, a circular import can see an incomplete module.

---

## 38. Descriptor Protocol

**Answer:** Defined by `__get__(self, obj, objtype)`, `__set__(self, obj, value)`, `__delete__(self, obj)`. A "data descriptor" defines `__set__` and/or `__delete__` and takes priority over instance `__dict__`; a "non-data descriptor" defines only `__get__` and instance `__dict__` takes priority over it.

```python
class ReadOnly:
    def __set_name__(self, owner, name):
        self._name = name
    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._name]
    def __set__(self, obj, value):
        raise AttributeError("read-only")

class C:
    x = ReadOnly()
    def __init__(self, x):
        self.__dict__["x"] = x
```

**Trap:** `property` is just a built-in data descriptor — knowing the raw protocol lets you explain *why* properties override instance attributes but plain methods don't.

---

## 39. Attribute Lookup Order

**Answer:** For `obj.attr`, CPython's `__getattribute__` checks, in order:
1. Data descriptors found via the type's MRO.
2. Instance `__dict__`.
3. Non-data descriptors / class attributes found via the type's MRO.
4. `__getattr__` (only called if the above all fail) — fallback hook, not part of normal lookup.

```python
class C:
    class Desc:
        def __get__(self, obj, objtype=None): return "descriptor"
    x = Desc()

c = C()
c.__dict__["x"] = "instance value"
print(c.x)  # "descriptor" if Desc is a data descriptor (defines __set__), else "instance value"
```

**Trap:** `__getattr__` vs `__getattribute__` — `__getattribute__` is invoked for *every* attribute access and is rarely overridden; `__getattr__` is only invoked when normal lookup fails.
