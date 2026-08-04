# Functional Programming

Functional programming in Python is not a pure paradigm the way Haskell is, but Python borrows heavily from it: first-class functions, higher-order functions, immutability idioms, and a rich standard library (`functools`, `operator`, `itertools`) for composing behavior without writing explicit loops. SDE-2 interviews frequently probe whether you can replace verbose imperative loops with idiomatic, efficient functional constructs, and whether you understand what happens under the hood (laziness, memory, time complexity).

## Table of Contents

1. map()
2. filter()
3. reduce()
4. zip()
5. enumerate()
6. any() and all()
7. sorted() (key functions, custom comparators)
8. functools module
9. operator module

---

## 1. map()

### Explanation

`map(function, iterable, ...)` applies `function` to every item of `iterable` and returns a **lazy iterator** (a `map` object) that yields results one at a time. It can take multiple iterables, in which case `function` must accept that many arguments, and iteration stops at the shortest iterable.

### Why it matters / internals

- `map` is implemented in C and is generally faster than an equivalent Python-level `for` loop because it avoids repeated bytecode dispatch for the loop control itself, though the function call overhead remains.
- It is lazy — nothing is computed until you iterate (via `list()`, a `for` loop, `next()`, etc.). This matters for memory: `map` over a huge/infinite iterable doesn't materialize a list.
- Since `map` returns an iterator, it is **single-use** — once exhausted, it cannot be reused or reset.

### Code Example

```python
# Basic usage
nums = [1, 2, 3, 4]
squares = map(lambda x: x ** 2, nums)
print(list(squares))  # [1, 4, 9, 16]

# Multiple iterables
a = [1, 2, 3]
b = [10, 20, 30]
sums = map(lambda x, y: x + y, a, b)
print(list(sums))  # [11, 22, 33]

# map with a named function (often faster than lambda due to no closure creation)
print(list(map(str, [1, 2, 3])))  # ['1', '2', '3']

# map is lazy and single-use
m = map(lambda x: x * 2, [1, 2, 3])
print(list(m))  # [2, 4, 6]
print(list(m))  # [] -- exhausted!

# map stops at the shortest iterable
print(list(map(lambda x, y: x + y, [1, 2], [1, 2, 3, 4])))  # [2, 4]
```

### Common Interview Questions / Gotchas

- "Why prefer `map` over a list comprehension?" — In practice, list comprehensions are usually equally fast or faster and more readable in Python; `map` shines when passing an existing function (`map(str, lst)`) without a lambda wrapper, and when laziness/memory matters.
- "Is `map` faster than a for loop?" — Yes for large data with a C-level function like `str` or `len`, because the loop runs in C; less true with a Python lambda since the call overhead dominates.
- Forgetting to wrap `map()` in `list()`/`tuple()` when you need to print/inspect results — you'll just see `<map object at 0x...>`.

### Pitfalls

- Re-iterating an exhausted `map` object silently yields nothing (no error), a common silent bug source.
- Using `map` with side-effecting functions for control flow (e.g., `map(print, items)`) works but is considered unpythonic — prefer explicit loops for side effects.

---

## 2. filter()

### Explanation

`filter(function, iterable)` returns a lazy iterator over items of `iterable` for which `function(item)` is truthy. If `function` is `None`, it filters out falsy values (equivalent to `filter(bool, iterable)`).

### Why it matters / internals

- Like `map`, it's a C-implemented, lazy, single-use iterator — useful for streaming pipelines and avoiding intermediate lists.
- `filter(None, iterable)` is a classic idiom to strip out `None`, `0`, `''`, `[]`, `False`, etc.

### Code Example

```python
nums = [1, -2, 3, -4, 5, 0]

positives = filter(lambda x: x > 0, nums)
print(list(positives))  # [1, 3, 5]

# filter(None, ...) removes falsy values
mixed = [0, 1, '', 'a', None, [], [1], False, True]
print(list(filter(None, mixed)))  # [1, 'a', [1], True]

# Combine with map to build a pipeline (lazy, streaming)
data = range(10)
pipeline = map(lambda x: x * x, filter(lambda x: x % 2 == 0, data))
print(list(pipeline))  # [0, 4, 16, 36, 64]

# filterfalse from itertools is the complement
from itertools import filterfalse
print(list(filterfalse(lambda x: x % 2 == 0, range(10))))  # odds
```

### Common Interview Questions / Gotchas

- "How would you remove all `None` from a list while keeping `0` and `''`?" — `filter(lambda x: x is not None, lst)`, NOT `filter(None, lst)` (which also drops `0`, `''`, etc.).
- "filter vs list comprehension with `if`?" — `[x for x in lst if pred(x)]` is the idiomatic replacement and often preferred for readability.

### Pitfalls

- Confusing `filter(None, ...)` with "remove None only" — it removes ALL falsy values.
- Chained `map`/`filter` pipelines can become unreadable; a generator expression is often clearer: `(x*x for x in data if x % 2 == 0)`.

---

## 3. reduce()

### Explanation

`functools.reduce(function, iterable, initializer=None)` cumulatively applies a binary `function` to the items of `iterable`, from left to right, reducing it to a single value. `function(acc, item) -> new_acc`.

### Why it matters / internals

- Unlike `map`/`filter`, `reduce` was moved out of builtins into `functools` in Python 3 specifically because Guido van Rossum felt explicit loops are usually more readable for accumulation logic.
- `reduce` is eager (not lazy) — it must consume the whole iterable to produce a result.
- With no `initializer`, the first element of the iterable is used as the initial accumulator, and `reduce` raises `TypeError` on an empty iterable — always safer to pass an explicit `initializer`.

### Code Example

```python
from functools import reduce

nums = [1, 2, 3, 4, 5]

total = reduce(lambda acc, x: acc + x, nums)
print(total)  # 15

# With initializer
product = reduce(lambda acc, x: acc * x, nums, 1)
print(product)  # 120

# Finding max manually
maximum = reduce(lambda a, b: a if a > b else b, nums)
print(maximum)  # 5

# Flattening a list of lists
lists = [[1, 2], [3, 4], [5]]
flat = reduce(lambda acc, l: acc + l, lists, [])
print(flat)  # [1, 2, 3, 4, 5]

# Empty iterable without initializer raises TypeError
try:
    reduce(lambda a, b: a + b, [])
except TypeError as e:
    print("Error:", e)

# Empty iterable WITH initializer is safe
print(reduce(lambda a, b: a + b, [], 0))  # 0
```

### Common Interview Questions / Gotchas

- "Implement `reduce` yourself" — a classic warm-up:
```python
def my_reduce(func, iterable, initializer=None):
    it = iter(iterable)
    if initializer is None:
        try:
            acc = next(it)
        except StopIteration:
            raise TypeError("reduce() of empty iterable with no initial value")
    else:
        acc = initializer
    for item in it:
        acc = func(acc, item)
    return acc
```
- "Why is `sum()` preferred over `reduce(lambda a,b: a+b, ...)`?" — `sum()` is implemented in C and is far faster; use built-ins (`sum`, `max`, `min`, `any`, `all`) instead of `reduce` when they exist.
- "reduce vs a for-loop accumulator" — functionally identical; `reduce` is more "functional style" but a for-loop is often more readable for non-trivial merge logic.

### Pitfalls

- Omitting `initializer` and calling on an empty iterable crashes.
- Overusing `reduce` for things with dedicated built-ins (`sum`, `max`, string `join`) hurts both readability and performance.
- Non-associative operations can give surprising results if you assume order doesn't matter — `reduce` is strictly left-to-right.

---

## 4. zip()

### Explanation

`zip(*iterables, strict=False)` returns a lazy iterator of tuples, pairing up elements at the same index across the given iterables. It stops at the shortest iterable unless `strict=True` (Python 3.10+), which raises `ValueError` on length mismatch.

### Why it matters / internals

- `zip` is the idiomatic way to iterate over multiple sequences in parallel — far better than `for i in range(len(a)): a[i], b[i]`.
- `zip(*matrix)` is a common trick to transpose a list of lists.
- `dict(zip(keys, values))` is the standard idiom for building a dict from two parallel lists.
- `strict=True` guards against silent truncation bugs when lengths are expected to match.

### Code Example

```python
names = ['Alice', 'Bob', 'Carol']
ages = [30, 25, 35]

for name, age in zip(names, ages):
    print(name, age)

# Building a dict
d = dict(zip(names, ages))
print(d)  # {'Alice': 30, 'Bob': 25, 'Carol': 35}

# Unequal lengths: stops at shortest (silent truncation!)
print(list(zip([1, 2, 3], ['a', 'b'])))  # [(1, 'a'), (2, 'b')]

# strict=True catches mismatches (Python 3.10+)
try:
    list(zip([1, 2, 3], ['a', 'b'], strict=True))
except ValueError as e:
    print("Error:", e)

# Unzipping with zip(*...)
pairs = [(1, 'a'), (2, 'b'), (3, 'c')]
nums, letters = zip(*pairs)
print(nums, letters)  # (1, 2, 3) ('a', 'b', 'c')

# Transposing a matrix
matrix = [[1, 2, 3], [4, 5, 6]]
transposed = list(zip(*matrix))
print(transposed)  # [(1, 4), (2, 5), (3, 6)]

# itertools.zip_longest for padding instead of truncating
from itertools import zip_longest
print(list(zip_longest([1, 2, 3], ['a'], fillvalue=None)))
# [(1, 'a'), (2, None), (3, None)]
```

### Common Interview Questions / Gotchas

- "How do you iterate two lists of different lengths without losing data?" — `itertools.zip_longest`.
- "Transpose a matrix in one line" — `list(zip(*matrix))`, and note it returns tuples, not lists (wrap with `[list(row) for row in zip(*matrix)]` if lists are required).
- "Why did `zip` silently drop data in my pipeline?" — because it truncates to the shortest input by default; use `strict=True` in production code where lengths must match.

### Pitfalls

- Silent truncation is the #1 real-world bug with `zip`.
- `zip` returns an iterator — exhausted after one pass, same caveat as `map`/`filter`.
- `zip(*matrix)` on a ragged (non-rectangular) list of lists truncates to the shortest row.

---

## 5. enumerate()

### Explanation

`enumerate(iterable, start=0)` returns a lazy iterator of `(index, value)` tuples. It replaces manual index tracking (`i = 0; for x in lst: ...; i += 1`).

### Why it matters / internals

- Implemented in C, avoids manual counter bugs, and works with any iterable (not just sequences), including generators.
- `start` parameter lets you offset the index (e.g., 1-based numbering for display).

### Code Example

```python
fruits = ['apple', 'banana', 'cherry']

for idx, fruit in enumerate(fruits):
    print(idx, fruit)

# Custom start
for idx, fruit in enumerate(fruits, start=1):
    print(f"{idx}. {fruit}")

# Building an index map (value -> first index)
index_map = {v: i for i, v in enumerate(fruits)}
print(index_map)  # {'apple': 0, 'banana': 1, 'cherry': 2}

# enumerate works on any iterable, including generators
def gen():
    yield 'x'
    yield 'y'

for i, v in enumerate(gen()):
    print(i, v)
```

### Common Interview Questions / Gotchas

- "Why is `enumerate(lst)` preferred over `range(len(lst))`?" — more Pythonic, avoids off-by-one errors, works on non-indexable iterables (generators, files).
- "Two Sum with indices" — a common use is `for i, num in enumerate(nums): ...` to track original positions while using a value as a dict key.

### Pitfalls

- Forgetting that `enumerate` returns an iterator (not a list) — cannot be indexed directly (`enumerate(lst)[0]` fails); must convert with `list()` first if random access is needed.
- Mixing up unpacking order — it's `(index, value)`, not `(value, index)`.

---

## 6. any() and all()

### Explanation

`any(iterable)` returns `True` if at least one element is truthy (returns `False` for an empty iterable). `all(iterable)` returns `True` if every element is truthy (returns `True` for an empty iterable — vacuous truth).

### Why it matters / internals

- Both **short-circuit**: `any` stops at the first truthy value, `all` stops at the first falsy value — critical for performance and for allowing infinite/expensive generators.
- Because they accept any iterable, they compose naturally with generator expressions to avoid building intermediate lists.

### Code Example

```python
nums = [2, 4, 6, 8]

print(all(x % 2 == 0 for x in nums))  # True
print(any(x > 7 for x in nums))       # True

# Short-circuiting demonstrated with side effects
def check(x):
    print(f"checking {x}")
    return x > 2

result = any(check(x) for x in [1, 2, 3, 4])
# prints "checking 1", "checking 2", "checking 3" then stops (short-circuit)
print(result)  # True

# Empty iterable edge cases
print(all([]))  # True  (vacuous truth)
print(any([]))  # False

# Validating all fields present in a dict
record = {"name": "Alice", "age": 30, "email": None}
required = ["name", "age", "email"]
print(all(record.get(f) is not None for f in required))  # False
```

### Common Interview Questions / Gotchas

- "Why does `all([])` return `True`?" — classic logic/math question: universally quantified statement over an empty set is vacuously true.
- "Use `any`/`all` with a generator, not a list comprehension, to avoid building the whole list" — demonstrates awareness of short-circuiting and memory.
- Validate matrix properties: `all(all(row) for row in matrix)` for "are all elements truthy in a 2D grid".

### Pitfalls

- Passing a list comprehension `any([f(x) for x in huge_iterable])` defeats short-circuiting benefits since the list is fully built first — use a generator expression `any(f(x) for x in huge_iterable)` instead.
- Confusing `all([])==True` and `any([])==False` in boundary-condition code (e.g., permission checks on an empty list of required roles).

---

## 7. sorted() (key functions, custom comparators)

### Explanation

`sorted(iterable, key=None, reverse=False)` returns a new sorted list; `list.sort()` sorts in place. Python's sort is **Timsort** — a stable, hybrid merge/insertion sort with O(n log n) worst case, O(n) best case (for nearly-sorted data).

### Why it matters / internals

- `key` function is called once per element and cached (Schwartzian transform under the hood, done in C) — much faster than a custom comparator called O(n log n) times.
- **Stability**: elements that compare equal retain their relative input order — essential for multi-key sorts (sort by secondary key first, then primary key).
- Python 3 removed the `cmp` parameter; use `functools.cmp_to_key` to adapt an old-style comparator.
- Sorting is a common building block for many algorithm interview problems (merge intervals, meeting rooms, custom string ordering, largest number formed by concatenation).

### Code Example

```python
words = ["banana", "kiwi", "apple", "fig"]

# Sort by length
print(sorted(words, key=len))  # ['fig', 'kiwi', 'apple', 'banana']

# Sort descending
print(sorted(words, key=len, reverse=True))

# Multi-key sort: by length, then alphabetically -- relies on stability
people = [("Bob", 25), ("Alice", 25), ("Eve", 20)]
print(sorted(people, key=lambda p: (p[1], p[0])))
# [('Eve', 20), ('Alice', 25), ('Bob', 25)]

# Stable sort demonstrated with two passes (secondary key first)
data = [("a", 2), ("b", 1), ("c", 2), ("d", 1)]
step1 = sorted(data, key=lambda x: x[0])       # sort by name
step2 = sorted(step1, key=lambda x: x[1])      # then stable-sort by number
print(step2)  # groups by number, preserving name order within each group

# Custom comparator via cmp_to_key -- classic "largest number from list" problem
from functools import cmp_to_key

def compare(a, b):
    # place a before b if a+b > b+a as numbers
    if a + b > b + a:
        return -1
    elif a + b < b + a:
        return 1
    return 0

nums = ["3", "30", "34", "5", "9"]
result = sorted(nums, key=cmp_to_key(compare))
print("".join(result))  # "9534330"

# sorted() on dict by value
scores = {"a": 3, "b": 1, "c": 2}
print(sorted(scores.items(), key=lambda kv: kv[1]))  # [('b',1), ('c',2), ('a',3)]

# operator.itemgetter / attrgetter as faster key functions
from operator import itemgetter, attrgetter
print(sorted(people, key=itemgetter(1)))

class Person:
    def __init__(self, name, age):
        self.name, self.age = name, age
    def __repr__(self):
        return f"Person({self.name!r}, {self.age})"

persons = [Person("Bob", 25), Person("Alice", 30)]
print(sorted(persons, key=attrgetter("age")))
```

### Common Interview Questions / Gotchas

- "Why is `key=` preferred over a custom comparator?" — O(n) key computations vs O(n log n) comparator calls; simpler to reason about.
- "Is Python's sort stable? Why does it matter?" — Yes (Timsort); it enables multi-pass sorting by different keys and guarantees deterministic tie-breaking.
- "Sort a list of tuples by the second element descending, then first ascending" — `sorted(lst, key=lambda x: (-x[1], x[0]))` — the negation trick avoids needing `cmp_to_key` when one key is numeric.
- "What's the time/space complexity of Timsort?" — O(n log n) time worst case, O(n) space, O(n) best case for nearly sorted runs.

### Pitfalls

- Using `cmp_to_key` unnecessarily when a tuple key with negation would suffice — slower and more code.
- Negating non-numeric keys (e.g., strings) doesn't work directly — must use `reverse=True` per sort pass or `cmp_to_key`.
- Forgetting `sorted()` returns a new list, while `.sort()` mutates in place and returns `None` (a classic bug: `x = lst.sort()` gives `x = None`).

---

## 8. functools module

### 8.1 functools.partial

**Explanation**: `partial(func, *args, **kwargs)` creates a new callable with some arguments pre-filled, useful for adapting function signatures (e.g., for callbacks) without writing a wrapper lambda/def.

**Why it matters**: Avoids repetitive lambdas, is introspectable (`.func`, `.args`, `.keywords`), and is commonly used with `map`, event handlers, and dependency injection patterns.

```python
from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube = partial(power, exponent=3)
print(square(5), cube(2))  # 25 8

# Partial with positional pre-fill
add = lambda a, b, c: a + b + c
add_5 = partial(add, 5)
print(add_5(10, 20))  # 35

# Used with map
nums = [1, 2, 3, 4]
print(list(map(partial(power, exponent=2), nums)))  # [1, 4, 9, 16]
```

### 8.2 functools.lru_cache

**Explanation**: `@lru_cache(maxsize=128)` memoizes a function's return value keyed on its (hashable) arguments, evicting least-recently-used entries once `maxsize` is exceeded. `@cache` (3.9+) is an unbounded shorthand.

**Why it matters / internals**: Backed by a doubly linked list + dict for O(1) get/put and LRU eviction. Massively speeds up recursive algorithms (Fibonacci, DP) by avoiding recomputation. Arguments must be hashable — unhashable args (lists, dicts) raise `TypeError`.

```python
from functools import lru_cache
import time

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

start = time.time()
print(fib(35))
print("elapsed:", time.time() - start)  # fast, thanks to memoization

print(fib.cache_info())  # CacheInfo(hits=..., misses=..., maxsize=None, currsize=...)
fib.cache_clear()

# Unhashable arguments fail
@lru_cache()
def process(data):
    return sum(data)

try:
    process([1, 2, 3])  # list is unhashable
except TypeError as e:
    print("Error:", e)
process((1, 2, 3))  # tuples work fine
```

### 8.3 functools.reduce

Covered in section 3 above.

### 8.4 functools.wraps

**Explanation**: `@wraps(func)` is used inside a decorator to copy `__name__`, `__doc__`, `__module__`, and `__wrapped__` from the original function onto the wrapper, so introspection tools (help(), debuggers, other decorators) see the correct metadata.

**Why it matters**: Without `wraps`, every decorated function looks like `wrapper` in stack traces, `help()`, and `functools`-based tooling — a real debugging pain point.

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def greet(name):
    """Greet someone by name."""
    return f"Hello, {name}"

print(greet("Alice"))
print(greet.__name__)  # 'greet'  (would be 'wrapper' without @wraps)
print(greet.__doc__)   # 'Greet someone by name.'
```

### 8.5 functools.singledispatch

**Explanation**: `@singledispatch` implements function overloading based on the type of the first argument, mimicking generic functions from languages like Java/C++. Register type-specific implementations with `@func.register`.

**Why it matters**: Avoids long `isinstance` if/elif chains; extensible by third parties without modifying the original function (open/closed principle).

```python
from functools import singledispatch

@singledispatch
def describe(obj):
    return f"Object: {obj}"

@describe.register
def _(obj: int):
    return f"Integer: {obj}"

@describe.register
def _(obj: list):
    return f"List of {len(obj)} items"

@describe.register(str)
def _(obj):
    return f"String of length {len(obj)}"

print(describe(42))         # Integer: 42
print(describe([1, 2, 3]))  # List of 3 items
print(describe("hello"))    # String of length 5
print(describe(3.14))       # Object: 3.14  (falls back to default)
```

### Common Interview Questions / Gotchas (functools)

- "Implement your own `lru_cache` using a dict + OrderedDict" — tests understanding of LRU eviction mechanics.
- "Why does mutable default state in `lru_cache`d functions cause bugs?" — cached results are shared across calls; if the returned object is mutated by the caller, subsequent cached calls return the mutated object.
- "Difference between `partial` and a lambda?" — `partial` is introspectable, picklable (if func/args are picklable), and slightly more efficient; lambdas are more flexible for arbitrary logic.

### Pitfalls

- Using `lru_cache` on methods (not just functions) keeps `self` alive as part of the cache key, potentially causing memory leaks in long-lived apps (instances never get garbage collected while cached).
- Forgetting `@wraps` breaks introspection-dependent code (e.g., Flask route naming, pytest fixture names).
- `lru_cache` results are shared globally per-decorated-function — dangerous for non-pure functions (functions with side effects or that depend on external mutable state).

---

## 9. operator module

### Explanation

The `operator` module exposes built-in operators (`+`, `-`, `[]`, attribute access, comparisons) as regular functions, letting you pass them to higher-order functions like `reduce`, `sorted`, and `map` without writing lambdas.

### Why it matters / internals

- Operator functions are implemented in C and are faster than an equivalent lambda (skips a Python-level function call/frame creation for the wrapping).
- `itemgetter`/`attrgetter`/`methodcaller` are especially common as `key=` arguments for `sorted`/`min`/`max` and are the idiomatic, most efficient choice.

### Code Example

```python
import operator
from functools import reduce

print(operator.add(3, 4))       # 7
print(operator.mul(3, 4))       # 12
print(operator.gt(5, 3))        # True

# reduce with operator instead of lambda
nums = [1, 2, 3, 4, 5]
print(reduce(operator.add, nums))  # 15
print(reduce(operator.mul, nums))  # 120

# itemgetter: extract items by index/key
data = [("a", 3), ("b", 1), ("c", 2)]
print(sorted(data, key=operator.itemgetter(1)))  # sort by 2nd tuple element

records = [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
print(sorted(records, key=operator.itemgetter("age")))

# attrgetter: extract attributes
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

points = [Point(3, 1), Point(1, 2)]
print(sorted(points, key=operator.attrgetter("x")))

# methodcaller: call a method by name
words = ["Banana", "apple", "Cherry"]
print(sorted(words, key=operator.methodcaller("lower")))

# operator.itemgetter with multiple keys (multi-key sort in one call)
print(sorted(records, key=operator.itemgetter("age", "name")))
```

### Common Interview Questions / Gotchas

- "Why use `operator.add` instead of `lambda a, b: a + b`?" — marginally faster (C implementation), more readable intent, avoids lambda closures.
- "How does `itemgetter` support multiple keys?" — `itemgetter(1, 2)` returns a tuple `(item[1], item[2])`, letting you do a compound sort key in one call, equivalent to `key=lambda x: (x[1], x[2])`.
- "Use `operator` for functional composition" — e.g., building a small expression evaluator that maps operator strings ("+", "-") to `operator.add`, `operator.sub`.

### Pitfalls

- `attrgetter`/`itemgetter` return a single value when given one argument, but a tuple when given multiple — this changes downstream code shape (`key=itemgetter(0)` gives scalar, `key=itemgetter(0,1)` gives tuple).
- `methodcaller` binds the method name at creation time; passing extra arguments requires `methodcaller("method", arg1, arg2)`.
- Confusing `operator.eq` (function form of `==`) with `is` semantics — `operator.eq` still uses `__eq__`, not identity.

---

## Summary Cheat Sheet

| Tool | Laziness | Typical use | Interview signal |
|---|---|---|---|
| `map` | Lazy | Transform each element | Know it's single-use, C-speed |
| `filter` | Lazy | Keep matching elements | `filter(None, ...)` gotcha |
| `reduce` | Eager | Fold to single value | Prefer built-ins when available |
| `zip` | Lazy | Parallel iteration | Truncation vs `strict=True` |
| `enumerate` | Lazy | Index + value | Avoids manual counters |
| `any`/`all` | Short-circuit | Boolean aggregation | Empty-iterable edge cases |
| `sorted` | Eager (returns list) | Ordering | Stability, `key` vs `cmp_to_key` |
| `functools` | — | Composition, caching, dispatch | `lru_cache` internals, `wraps` |
| `operator` | — | Functional operator access | `itemgetter`/`attrgetter` for sort keys |
