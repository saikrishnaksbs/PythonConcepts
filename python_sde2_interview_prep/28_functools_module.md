# functools Module

## Overview

`functools` is the standard library module for higher-order functions —
functions that act on or return other functions. At the SDE-2 level,
interviewers expect you to not just know the API but to reason about
*why* each tool exists, what it costs (time/space/thread-safety), and
where it silently breaks (mutable default args, unhashable arguments,
memory leaks from caching instances, etc.). This file covers `partial`,
`reduce`, `lru_cache`, `singledispatch`/`singledispatchmethod`, and
`cached_property` in depth, with `wraps`, `total_ordering`, and
`cmp_to_key` covered briefly at the end since they routinely come up in
the same conversation.

---

## functools.partial

### Explanation

`partial(func, *args, **kwargs)` returns a new callable with some
positional/keyword arguments "frozen." Calling the resulting object
supplies the remaining arguments. It is Python's built-in mechanism for
**partial application** (not true currying, since it doesn't force
one-argument-at-a-time application, but achieves the same practical
goal).

### Why it matters / internals

- `partial` is implemented in C (`_functools.partial`) for performance;
  there's also a pure-Python reference implementation in the
  `functools` source that's worth knowing:

```python
class partial:
    def __new__(cls, func, /, *args, **keywords):
        if not callable(func):
            raise TypeError("the first argument must be callable")
        if isinstance(func, partial):
            args = func.args + args
            keywords = {**func.keywords, **keywords}
            func = func.func
        self = super().__new__(cls)
        self.func = func
        self.args = args
        self.keywords = keywords
        return self

    def __call__(self, /, *args, **keywords):
        keywords = {**self.keywords, **keywords}
        return self.func(*self.args, *args, **keywords)
```

- Notice: **nesting `partial(partial(...))` flattens automatically** —
  this is a real interview gotcha. Also note new keyword args passed at
  call time **override** the frozen ones, but frozen *positional* args
  always come first (you cannot "unset" a frozen positional arg).
- Common real-world uses: binding callbacks in GUI/event systems,
  pre-configuring `functools.reduce` operations, adapting a function's
  signature to fit an API like `multiprocessing.Pool.map` (which only
  passes one argument), or building partially-configured loggers/
  serializers.

### Code example

```python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube = partial(power, exponent=3)

print(square(5))   # 25
print(cube(2))     # 8

# Using with multiprocessing.Pool.map, which requires a single-arg callable
import multiprocessing as mp

def add(x, y):
    return x + y

if __name__ == "__main__":
    add_ten = partial(add, 10)
    with mp.Pool(2) as pool:
        print(pool.map(add_ten, [1, 2, 3]))  # [11, 12, 13]

# partial objects expose .func, .args, .keywords for introspection
p = partial(power, 2, exponent=10)
print(p.func, p.args, p.keywords)  # <function power> (2,) {'exponent': 10}

# Nested partials flatten
p1 = partial(power, 2)
p2 = partial(p1, exponent=4)
print(p2.func is power, p2.args)  # True (2,)
```

### Interview questions / gotchas

- "How is `partial` different from a lambda closure that captures
  variables?" — `partial` freezes arguments eagerly at creation time
  (like default-argument binding), avoiding late-binding closure bugs;
  a `lambda: f(x)` re-reads `x` from the enclosing scope every call.
- "What happens when you call `partial()` on a `partial` object?" — it
  flattens into a single `partial` referencing the original function
  (see internals above), it does not create a chain of wrappers.
- "Can positional args frozen by `partial` be overridden at call time?"
  — No, for positional args, new positional args are *appended* after
  the frozen ones, not merged into the same slots — a classic footgun
  when you freeze positionally and then try to override.

### Pitfalls

- `partial` objects don't automatically carry `__name__`, `__doc__`,
  etc. from the wrapped function (unlike `functools.wraps`-decorated
  functions), which can break tools that introspect function metadata
  (e.g., some CLI frameworks or debuggers) — use `update_wrapper` if
  you need that.
- Freezing mutable objects (e.g., a list) means every call shares the
  same mutable reference — classic aliasing bug if the function mutates
  its argument.

---

## functools.reduce

### Explanation

`reduce(function, iterable[, initializer])` cumulatively applies a
binary function to the items of an iterable, left to right, collapsing
it to a single value. It's the direct equivalent of `fold_left` in
functional languages.

### Why it matters / internals

Pure-Python equivalent (this is literally in the docs, worth memorizing):

```python
def reduce(function, iterable, initializer=None):
    it = iter(iterable)
    if initializer is None:
        value = next(it)
    else:
        value = initializer
    for element in it:
        value = function(value, element)
    return value
```

- `reduce` is O(n) with O(1) extra space (excluding the iterable itself),
  since it only ever holds the running accumulator.
- Guido van Rossum famously suggested `reduce` be less prominent in
  Python 3 (moved from builtin to `functools`) because explicit loops
  are usually more readable — that's a legitimate interview talking
  point: know when *not* to use `reduce`.
- `sum()`, `math.prod()`, `all()`, `any()`, `max()`, `min()` cover the
  vast majority of "reduce" use cases with better readability and (for
  `sum`/`prod`) better performance since they're implemented in C
  without a Python-level callable overhead per element.

### Code example

```python
from functools import reduce
import operator

# Product of a list
nums = [1, 2, 3, 4, 5]
product = reduce(operator.mul, nums)
print(product)  # 120

# Using an initializer (important when iterable might be empty)
print(reduce(operator.mul, [], 1))  # 1 (safe)
# reduce(operator.mul, [])  # raises TypeError: reduce() of empty iterable with no initial value

# Flatten a list of lists
nested = [[1, 2], [3, 4], [5]]
flat = reduce(operator.iadd, nested, [])
print(flat)  # [1, 2, 3, 4, 5]

# Compose a pipeline of functions
def compose(*funcs):
    return reduce(lambda f, g: lambda x: g(f(x)), funcs)

pipeline = compose(lambda x: x + 1, lambda x: x * 2, str)
print(pipeline(3))  # "8"

# Find max via reduce (illustrative; use max() in practice)
words = ["a", "bbb", "cc"]
longest = reduce(lambda a, b: a if len(a) >= len(b) else b, words)
print(longest)  # "bbb"
```

### Interview questions / gotchas

- "What happens if the iterable is empty and no initializer is given?"
  — raises `TypeError: reduce() of empty iterable with no initial
  value`. Always supply an initializer for safety in production code.
- "Why was `reduce` removed from builtins in Python 3?" — readability;
  the BDFL felt most uses are clearer as explicit loops or as one of
  `sum`/`any`/`all`/`max`/`min`.
- "Implement `reduce` yourself" — expect to write the loop shown above,
  including the empty-iterable/no-initializer edge case.

### Pitfalls

- Using `reduce` for simple sums/products instead of the built-in
  `sum()`/`math.prod()` — slower and less idiomatic.
  interviewers may dock points for choosing `reduce` when a more direct
  tool exists.
- Non-associative operations combined with the assumption reduce could
  be parallelized — `reduce` is strictly sequential/left-to-right; you
  cannot assume the order doesn't matter (e.g., string concatenation
  order, or floating point addition where associativity technically
  doesn't hold due to rounding).

---

## functools.lru_cache

### Explanation

`@lru_cache(maxsize=128, typed=False)` memoizes a function's return
value keyed by its arguments, evicting least-recently-used entries once
`maxsize` is exceeded. It turns exponential-time recursive algorithms
(e.g., naive Fibonacci) into linear time by avoiding recomputation.

### Why it matters / internals

- Internally backed by a doubly linked list + dict for O(1) get/put and
  O(1) move-to-front on cache hit — the textbook LRU cache data
  structure, implemented in C in CPython for speed.
- Arguments must be **hashable** — the cache key is built from
  `args + tuple(sorted(kwargs.items()))` (roughly); passing a `list` or
  `dict` argument raises `TypeError: unhashable type`.
- `maxsize=None` disables the LRU eviction and turns it into a simple
  unbounded memoization dict — faster (skips the linked-list
  bookkeeping) but risks unbounded memory growth. `maxsize` must be a
  power-of-two-friendly value ideally (implementation detail: any int
  works, but internal wraparound arithmetic is optimized for it).
- `typed=True` makes `f(1)` and `f(1.0)` cache as *different* entries
  (since `1 == 1.0` but they're different types) — relevant when a
  function's behavior differs across numeric types.
- `.cache_info()` returns `CacheInfo(hits, misses, maxsize, currsize)`
  — great for demonstrating cache effectiveness in an interview or in
  production debugging.
- `.cache_clear()` resets hits/misses/entries — useful in tests to
  avoid cross-test pollution when the cached function is module-level.
- **Thread-safety**: `lru_cache` *is* thread-safe for concurrent calls
  — CPython protects the internal cache structure with a lock so
  concurrent `get`/`put` operations won't corrupt state. However, it
  does **not** prevent the classic "cache stampede" — if two threads
  call with the same uncached argument simultaneously, both may end up
  computing the value (the lock protects data-structure integrity, not
  the underlying function call itself).
- `functools.cache` (Python 3.9+) is simply `lru_cache(maxsize=None)`
  — a convenience alias for unbounded memoization with no eviction
  bookkeeping overhead. Prefer `cache` when you know the argument space
  is small/finite; prefer `lru_cache(maxsize=...)` when the argument
  space is unbounded or memory is a concern.

### Code example

```python
from functools import lru_cache, cache
import time

@lru_cache(maxsize=128)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(35))
print(fib.cache_info())  # CacheInfo(hits=..., misses=36, maxsize=128, currsize=36)
fib.cache_clear()
print(fib.cache_info())  # CacheInfo(hits=0, misses=0, maxsize=128, currsize=0)

# typed=True distinguishes int vs float keys
@lru_cache(maxsize=None, typed=True)
def identity(x):
    return x

identity(1)
identity(1.0)
print(identity.cache_info().currsize)  # 2 (would be 1 if typed=False)

# functools.cache == lru_cache(maxsize=None)
@cache
def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)

print(factorial(10))

# Unhashable argument raises TypeError
@lru_cache()
def process(data):
    return sum(data)

try:
    process([1, 2, 3])  # list is unhashable
except TypeError as e:
    print("Error:", e)
process((1, 2, 3))  # tuples work fine
```

### Interview questions / gotchas

- "Is `lru_cache` thread-safe?" — Yes, internal state is protected by a
  lock; but that doesn't prevent redundant recomputation under a
  concurrent cache-miss race (cache stampede), and it doesn't make the
  *decorated function itself* thread-safe if it has side effects.
- "Why can't you cache a function that takes a list argument?" —
  cache keys must be hashable; lists/dicts/sets are not hashable.
  Convert to `tuple`/`frozenset` first.
- "What's the difference between `lru_cache(maxsize=None)` and
  `cache`?" — functionally identical; `cache` is just a clearer,
  slightly faster (no LRU bookkeeping) spelling introduced in 3.9.
- "How would you cache a method on a class without leaking memory?" —
  `lru_cache` on an instance method keeps a strong reference to `self`
  as part of the cache key, which **prevents garbage collection** of
  instances as long as the cache holds an entry (classic memory leak
  in long-lived processes with many short-lived instances). Mitigate
  with `cached_property` (per-instance, no global cache) or a
  bounded cache with a weak-reference wrapper.
- "How would you implement `lru_cache` yourself?" — be ready to sketch
  `OrderedDict` (move_to_end + popitem(last=False)) or a hashmap +
  doubly linked list.

### Pitfalls

- Decorating an instance method with `@lru_cache` — leaks memory (see
  above) since `self` becomes part of the cache key and is kept alive.
- Mutable default results — if the cached return value is mutable and
  the caller mutates it, subsequent cache hits return the *same
  mutated object* (cache stores references, not copies).
- Caching functions with side effects (I/O, printing, timestamps) leads
  to stale/incorrect behavior since subsequent calls skip execution
  entirely.
- Forgetting `cache_clear()` between tests when a cached function is
  imported at module scope, causing test pollution/flakiness.

---

## functools.singledispatch (and singledispatchmethod)

### Explanation

`@singledispatch` implements single-argument generic functions/dynamic
overloading based on the **type of the first argument**, similar to
function overloading in statically typed languages. `register()` adds
type-specific implementations.

### Why it matters / internals

- Uses an internal type-based dispatch cache (a dict mapping type ->
  implementation) and consults the **MRO (Method Resolution Order)**
  for subclasses — if you register `list`, a call with a `MyList(list)`
  subclass instance will correctly resolve to the `list` implementation
  if no more specific one is registered.
- `functools.singledispatchmethod` (3.8+) is the equivalent for
  instance/class methods, dispatching on the type of the **first
  argument after `self`/`cls`**.
- Since 3.7, `register` supports being used with type annotations
  instead of explicit type arguments (`@func.register def _(arg: int):
  ...`), which is more idiomatic in modern code.
- This is Python's structured answer to "avoid long `if isinstance(...)
  elif isinstance(...)` chains" — cleaner, extensible (third-party code
  can register new types without modifying the original function), and
  follows the open/closed principle.

### Code example

```python
from functools import singledispatch, singledispatchmethod

@singledispatch
def describe(arg):
    return f"Unknown type: {type(arg).__name__}"

@describe.register
def _(arg: int):
    return f"Integer: {arg}"

@describe.register
def _(arg: str):
    return f"String of length {len(arg)}"

@describe.register(list)
def _(arg):
    return f"List with {len(arg)} items"

print(describe(42))          # Integer: 42
print(describe("hello"))     # String of length 5
print(describe([1, 2, 3]))   # List with 3 items
print(describe(3.14))        # Unknown type: float

# Subclass dispatch follows MRO
class MyList(list):
    pass

print(describe(MyList([1, 2])))  # List with 2 items (falls back to list impl)

# singledispatchmethod inside a class
class Formatter:
    @singledispatchmethod
    def format(self, arg):
        raise NotImplementedError(f"Cannot format {type(arg)}")

    @format.register
    def _(self, arg: int):
        return f"{arg:,}"

    @format.register
    def _(self, arg: float):
        return f"{arg:.2f}"

f = Formatter()
print(f.format(1000000))  # 1,000,000
print(f.format(3.14159))  # 3.14

# Inspect registered implementations
print(describe.registry.keys())  # dict_keys([object, int, str, list])
```

### Interview questions / gotchas

- "How does dispatch behave for a subclass with no registered
  implementation?" — walks the MRO to find the nearest registered
  ancestor type; falls back to the base (`object`) implementation if
  none matches.
- "Can you dispatch on the second argument, or on multiple arguments?"
  — No, `singledispatch` only dispatches on the type of the *first*
  argument. For multiple-dispatch you'd need a third-party library
  (e.g., `multipledispatch`) or manual `isinstance` chains.
- "How is this different from method overloading in Java/C++?" — it's
  runtime dispatch based on a single argument's runtime type, resolved
  via a registry, not compile-time overload resolution.

### Pitfalls

- Forgetting that dispatch is on the **first argument only** — trying
  to `@register` based on a second parameter's type silently does
  nothing useful.
- Registering `None`/`NoneType` requires `@describe.register(type(None))`
  since you can't annotate cleanly with `None` as a type in older
  patterns — a common stumbling block.
- Overusing generic dispatch for trivial cases where a simple
  `isinstance` check would be clearer and avoid the indirection.

---

## functools.cached_property

### Explanation

`@cached_property` (3.8+) turns a method into a property whose value is
computed once, then **stored in the instance's `__dict__`** under the
same attribute name, so subsequent accesses skip the function entirely
and just do a normal attribute lookup.

### Why it matters / internals

- Implemented as a **non-data descriptor** (defines `__get__` but not
  `__set__`/`__delete__`). Because Python's attribute lookup checks
  instance `__dict__` *before* falling back to non-data descriptors on
  the class, once the value is cached in `instance.__dict__[name]`, the
  descriptor's `__get__` is never invoked again for that instance — a
  pure attribute lookup. This is the key mechanism distinguishing it
  from `@property` (a **data descriptor**, since it defines `__set__`,
  which *always* takes priority over instance `__dict__`, so a plain
  `@property` re-runs its getter every single access).
- Comparison: `@property` + separate `@lru_cache` on the getter method
  would key the cache off `self` (and any other args), keeping `self`
  alive forever in the global cache (same leak problem discussed
  above) and re-checking a hash/dict lookup every call. `cached_property`
  stores directly in the instance, so it's garbage-collected normally
  along with the instance, and after the first call it's just a dict
  lookup, not a function call.
- **Requires the instance to have a mutable `__dict__`** — classes
  using `__slots__` without explicitly including the cached attribute
  name (or `__dict__` itself) will raise `TypeError` at cache-set time,
  since there's nowhere to store the cached value.
- **Invalidation**: because it's just an instance dict entry, you
  invalidate by `del instance.__dict__['attr_name']` (or
  `del instance.attr_name`), after which the next access recomputes.
- **Thread-safety**: prior to Python 3.12, `cached_property` used an
  internal lock to guard against two threads computing the value
  simultaneously on first access. **Python 3.12 removed that lock**
  for performance reasons — meaning as of 3.12+, concurrent first
  access from multiple threads can trigger the underlying function
  multiple times (a race), and if the computation has side effects,
  this is a real behavioral change to be aware of. Always mention this
  version nuance in interviews — it is frequently tested.

### Code example

```python
from functools import cached_property, lru_cache
import time

class Report:
    def __init__(self, data):
        self.data = data

    @cached_property
    def summary(self):
        print("Computing summary...")
        time.sleep(0.1)  # simulate expensive work
        return sum(self.data)

r = Report([1, 2, 3, 4, 5])
print(r.summary)  # "Computing summary..." then 15
print(r.summary)  # 15 (no recompute, prints nothing)

# It's stored directly in instance __dict__
print(r.__dict__)  # {'data': [...], 'summary': 15}

# Manual invalidation
del r.__dict__['summary']
print(r.summary)  # recomputes: "Computing summary..." then 15

# Contrast with @property (always recomputes)
class ReportProperty:
    def __init__(self, data):
        self.data = data

    @property
    def summary(self):
        print("Computing (property)...")
        return sum(self.data)

rp = ReportProperty([1, 2, 3])
rp.summary  # prints "Computing (property)..."
rp.summary  # prints again -- no caching

# __slots__ pitfall: cached_property needs an instance __dict__
class SlottedBad:
    __slots__ = ("data",)

    @cached_property
    def total(self):
        return sum(self.data)

sb = SlottedBad()
sb.data = [1, 2, 3]
try:
    sb.total
except TypeError as e:
    print("Error:", e)  # No '__dict__' attribute to cache 'total' property.
```

### Interview questions / gotchas

- "Why does `cached_property` need `__dict__` but `property` doesn't?"
  — because `cached_property` writes the computed value directly into
  the instance `__dict__` to short-circuit future descriptor lookups;
  `property` never writes anywhere, it recomputes via `__get__` every
  time, so it works fine with `__slots__`.
- "What's the descriptor-protocol reason `cached_property` doesn't
  recompute after the first call, when `property` does?" — non-data
  descriptor (`cached_property`, no `__set__`) loses priority to
  instance `__dict__`; data descriptor (`property`, has `__set__`)
  always wins over instance `__dict__`.
  This is one of the most common "explain the descriptor protocol"
  interview questions.
- "How do you invalidate/refresh a cached_property?" — `del
  instance.__dict__[name]` or `del instance.name`.
  It is not reset automatically when dependent attributes (like
  `self.data` in the example) change — a very common bug: mutating
  `self.data` after `summary` has been accessed does *not* update
  `summary` until explicitly invalidated.
- "Is `cached_property` thread-safe?" — Was in <=3.11 (guarded by a
  lock during first computation); the lock was removed in 3.12, so as
  of 3.12 concurrent first-access is a data race for side-effecting
  computations. Mention this proactively; it signals depth.

### Pitfalls

- Using `cached_property` on a class with `__slots__` and forgetting to
  add the attribute (or `__dict__`) to slots — raises `TypeError` at
  first access, not at class definition time, which can be a nasty
  surprise found late.
- Assuming the cached value auto-invalidates when underlying data
  changes — it does not; stale-cache bugs are common when
  `cached_property` depends on mutable instance state that changes
  after first access.
- Relying on thread-safety guarantees across Python versions without
  checking — code written and tested thread-safely under 3.11 can
  develop races purely from upgrading to 3.12.
- Applying `cached_property` to something that legitimately needs to
  change per access (should be a normal method or `@property`).

---

## Honorable mentions (commonly asked alongside this module)

### functools.wraps

`@wraps(original_func)` is applied inside a decorator to copy
`__name__`, `__doc__`, `__module__`, `__qualname__`, and `__wrapped__`
(a reference back to the original function) from the wrapped function
onto the wrapper. Without it, decorated functions lose their identity
for introspection, debugging (`help()`, tracebacks), and tools relying
on `__name__` (e.g., Flask route registration, `pickle`).

```python
from functools import wraps

def logged(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logged
def greet(name):
    """Say hello."""
    return f"Hello, {name}"

print(greet.__name__)  # "greet" (would be "wrapper" without @wraps)
print(greet.__doc__)   # "Say hello."
```

Interview gotcha: "What breaks if you forget `@wraps`?" — stack traces,
`help()`, and any code that inspects `func.__name__` for
registration/dispatch (e.g., web framework routing by function name),
plus double-decoration/introspection tools like `functools.singledispatch`
relying on accurate signatures via `__wrapped__`.

### functools.total_ordering

Given a class that defines `__eq__` and *one* of `__lt__`, `__le__`,
`__gt__`, `__ge__`, `@total_ordering` fills in the rest automatically,
saving you from writing all six comparison dunders by hand.

```python
from functools import total_ordering

@total_ordering
class Version:
    def __init__(self, major, minor):
        self.major, self.minor = major, minor

    def __eq__(self, other):
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other):
        return (self.major, self.minor) < (other.major, other.minor)

v1, v2 = Version(1, 2), Version(1, 5)
print(v1 < v2, v1 <= v2, v1 > v2, v1 >= v2)  # True True False False
```

Gotcha: it trades a small runtime performance cost (extra indirection)
for reduced boilerplate — mention this trade-off if asked "why not just
write all six methods yourself?" Also, `total_ordering` does not
provide `__hash__`; defining `__eq__` sets `__hash__` to `None`
automatically unless you define it explicitly, which can silently make
instances unhashable.

### functools.cmp_to_key

Converts an old-style comparator function (`cmp(a, b) -> negative/zero/
positive`, like C's `qsort` comparator or Python 2's `cmp` argument) into
a `key` function usable with `sorted()`, `min()`, `max()`, `list.sort()`
in Python 3, which only accepts `key=`, not `cmp=`.

```python
from functools import cmp_to_key

def compare(a, b):
    if a[1] != b[1]:
        return a[1] - b[1]      # sort by second element ascending
    return b[0] - a[0]          # tie-break: first element descending

data = [(1, 2), (3, 1), (2, 2), (4, 1)]
result = sorted(data, key=cmp_to_key(compare))
print(result)  # [(4, 1), (3, 1), (2, 2), (1, 2)]
```

Gotcha: `cmp_to_key` is an escape hatch for legacy/complex multi-level
comparisons that are awkward to express as a simple `key=` extractor —
but whenever possible, prefer composing tuples for `key=` (as in
`key=lambda x: (x[1], -x[0])`) since it's faster (avoids O(n log n)
comparator calls with Python-level function overhead on every
comparison) and more idiomatic Python 3.
