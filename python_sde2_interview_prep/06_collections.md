# Collections

Deep dive into Python's core built-in collection types — `list`, `tuple`, `set`, and `dict` — covering internals, common methods with time complexity, idioms, and the interview questions/gotchas that come up repeatedly at SDE-2 level bar raiser and coding rounds.

---

## Lists

### Dynamic arrays (internals)

A Python `list` is implemented in CPython as a **dynamic array of pointers** (`PyObject*`), not a linked list. The array stores references to objects, not the objects themselves — this is why a list can hold heterogeneous types (`[1, "a", 3.0]`), each element is just a pointer to a `PyObject` living elsewhere on the heap.

Key internals:

- The underlying C array (`ob_item`) has a fixed **allocated capacity** that is usually larger than the current length (`ob_size`).
- When you append and the array is full, CPython **over-allocates**: it doesn't grow by 1, it grows by a formula so that repeated appends are cheap on average.
- CPython's over-allocation formula (from `listobject.c`, roughly):

```
new_allocated = (size_t)newsize + (newsize >> 3) + (newsize < 9 ? 3 : 6)
```

This grows the array by roughly **1.125x plus a small constant**, which gives the classic growth pattern: `0, 4, 8, 16, 25, 35, 46, 58, 72, 88, ...`

- Because growth is geometric (multiplicative) rather than linear, the **amortized** cost of `append()` is **O(1)**, even though any individual append that triggers a resize costs O(n) to copy pointers into the new array.
- `list.pop()` from the end is O(1). Popping/inserting at the front or middle is O(n) because all subsequent elements must shift.
- Lists never shrink their allocation aggressively on `pop`/`del` — CPython only shrinks the underlying array when it becomes very over-sized relative to length, to avoid thrashing.

```python
import sys

lst = []
prev_size = sys.getsizeof(lst)
for i in range(10):
    lst.append(i)
    size = sys.getsizeof(lst)
    if size != prev_size:
        print(f"len={len(lst):2d}  bytes={size}  (grew)")
    prev_size = size
```

Typical output shows capacity jumps (allocation growth), not a jump on every single append — proof of over-allocation.

### Methods and their time complexities

| Operation | Example | Average Time Complexity |
|---|---|---|
| Index access | `lst[i]` | O(1) |
| Index assignment | `lst[i] = x` | O(1) |
| Append | `lst.append(x)` | O(1) amortized |
| Pop last | `lst.pop()` | O(1) |
| Pop arbitrary index | `lst.pop(i)` | O(n) |
| Insert | `lst.insert(i, x)` | O(n) |
| Remove (by value) | `lst.remove(x)` | O(n) (search + shift) |
| Extend | `lst.extend(iterable)` | O(k) for k new items, amortized |
| Membership test | `x in lst` | O(n) |
| Slice | `lst[a:b]` | O(b - a) |
| Copy (shallow) | `lst.copy()` / `lst[:]` | O(n) |
| Sort | `lst.sort()` | O(n log n) |
| Reverse | `lst.reverse()` | O(n) |
| Concatenate | `lst1 + lst2` | O(n + m) |
| `len(lst)` | | O(1) (length is cached) |
| Clear | `lst.clear()` | O(n) |
| Index of value | `lst.index(x)` | O(n) |
| Count | `lst.count(x)` | O(n) |

```python
nums = [5, 3, 8, 1]

nums.append(9)          # [5, 3, 8, 1, 9]        O(1) amortized
nums.extend([2, 7])      # [5, 3, 8, 1, 9, 2, 7]  O(k)
nums.insert(0, 100)      # [100, 5, 3, 8, 1, 9, 2, 7]  O(n)
nums.pop()                # removes 7, O(1)
nums.pop(0)                # removes 100, O(n)
nums.remove(8)              # removes first '8', O(n)
nums.sort()                  # in-place, O(n log n), Timsort
nums.sort(reverse=True)      # descending
nums.reverse()                 # in-place O(n) reversal
print(sorted(nums))              # returns a NEW list, doesn't mutate
```

`list.sort()` (and `sorted()`) use **Timsort**, a hybrid stable merge/insertion sort — O(n log n) worst case, O(n) best case (already-sorted or reverse-sorted runs), and it is **stable** (equal elements keep relative order — important for multi-key sorts using `key=`).

### Nested lists

A nested list is a list whose elements are themselves lists (or other containers). Each inner list is a separate object referenced by pointer from the outer list.

```python
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

# Access
print(matrix[1][2])   # 6

# Transpose using list comprehension + zip
transposed = [list(row) for row in zip(*matrix)]
print(transposed)     # [[1, 4, 7], [2, 5, 8], [3, 6, 9]]

# Flatten a nested list (one level)
flat = [x for row in matrix for x in row]
print(flat)            # [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

**Classic gotcha — creating a 2D grid with `*`:**

```python
# WRONG: all rows are the SAME list object
grid = [[0] * 3] * 3
grid[0][0] = 1
print(grid)   # [[1, 0, 0], [1, 0, 0], [1, 0, 0]]  <- all rows changed!

# CORRECT: each row is a distinct list
grid = [[0] * 3 for _ in range(3)]
grid[0][0] = 1
print(grid)   # [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
```

`[[0]*3]*3` replicates the **same inner list reference** three times; `[[0]*3 for _ in range(3)]` creates three independent lists. This is one of the most commonly asked "spot the bug" interview questions.

### Slicing

Slicing syntax: `lst[start:stop:step]`. All three are optional; negative indices count from the end.

```python
lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

print(lst[2:5])      # [2, 3, 4]
print(lst[:4])        # [0, 1, 2, 3]
print(lst[6:])         # [6, 7, 8, 9]
print(lst[::2])         # [0, 2, 4, 6, 8]      step 2
print(lst[::-1])         # [9, 8, ..., 0]       reversed copy
print(lst[-3:])           # [7, 8, 9]           last 3
print(lst[:-3])            # [0, ..., 6]         all but last 3

# Slice assignment can change length
lst[1:3] = [100, 200, 300]
print(lst)   # [0, 100, 200, 300, 3, 4, 5, 6, 7, 8, 9]

# Delete a slice
del lst[0:2]

# Slicing never raises IndexError even for out-of-range bounds
print([1, 2, 3][10:20])   # []
```

Slicing always returns a **new list** (shallow copy of that range) — it never returns a view like NumPy arrays do.

### Copying: shallow vs deep copy

```python
import copy

original = [1, 2, [3, 4]]

# Shallow copy — several equivalent ways
shallow1 = original.copy()
shallow2 = list(original)
shallow3 = original[:]
shallow4 = copy.copy(original)

# Deep copy
deep = copy.deepcopy(original)

original[2].append(999)
print(shallow1)   # [1, 2, [3, 4, 999]]  <- nested list is SHARED
print(deep)        # [1, 2, [3, 4]]       <- fully independent
```

- **Shallow copy** creates a new outer container, but the elements inside are the *same objects* (same references) as the original. Mutating a nested mutable object (list, dict, custom object) through either copy affects both.
- **Deep copy** (`copy.deepcopy`) recursively copies every nested object, producing a fully independent structure. It is slower and uses more memory, and it correctly handles circular references (it maintains a memo dict of already-copied objects to avoid infinite recursion).
- Immutable nested elements (ints, strings, tuples of immutables) are safe under shallow copy — mutation isn't possible, so sharing references doesn't matter.

```python
# copy.deepcopy handles cycles
a = [1, 2]
a.append(a)          # a now contains itself
b = copy.deepcopy(a)  # does NOT infinite loop, thanks to memoization
```

### List comprehension

```python
squares = [x * x for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
pairs = [(x, y) for x in range(3) for y in range(3) if x != y]

# Nested comprehension (equivalent to nested for-loops)
matrix = [[1, 2], [3, 4]]
flat = [val for row in matrix for val in row]

# With conditional expression (ternary) inside the mapped value
labels = ["even" if x % 2 == 0 else "odd" for x in range(5)]
```

List comprehensions are generally faster than the equivalent `for` loop with `.append()` because the iteration runs in a specialized bytecode loop (`LIST_APPEND`) without repeated attribute lookups for `.append`, and CPython can pre-size the list slightly better internally.

Comprehension variables (in Python 3) have their **own scope** — they do not leak into the enclosing scope, unlike `for` loops.

```python
x = 100
result = [x for x in range(5)]
print(x)   # 100 — unchanged, comprehension has its own scope

for x in range(5):
    pass
print(x)   # 4 — for-loop DOES leak the variable
```

### Common interview questions and gotchas (Lists)

1. **Mutable default argument gotcha (Google/Amazon favorite):**

```python
def add_item(item, basket=[]):   # BUG: default list created ONCE at def time
    basket.append(item)
    return basket

print(add_item("apple"))    # ['apple']
print(add_item("banana"))   # ['apple', 'banana']  <- unexpected! Same list reused.

# FIX: use None as sentinel
def add_item_fixed(item, basket=None):
    if basket is None:
        basket = []
    basket.append(item)
    return basket
```

Default argument values are evaluated **once**, at function definition time, and the same object is reused across calls. This is one of the most-asked Python gotcha questions across all these companies.

2. **`list.sort()` vs `sorted()`** — `sort()` mutates in place and returns `None`; `sorted()` returns a new list and works on any iterable. A very common bug: `lst = lst.sort()` sets `lst` to `None`.

3. **Removing items from a list while iterating over it** (Amazon/Microsoft):

```python
nums = [1, 2, 3, 4, 5, 6]
for n in nums:
    if n % 2 == 0:
        nums.remove(n)   # BUG: mutating while iterating skips elements
print(nums)   # [1, 3, 5]  -- looks right here but is NOT reliable in general

# SAFE approaches:
nums = [1, 2, 3, 4, 5, 6]
nums = [n for n in nums if n % 2 != 0]          # new list
# or iterate over a copy:
for n in nums[:]:
    if n % 2 == 0:
        nums.remove(n)
```

4. **List vs tuple performance/memory** (see Tuples section below for full comparison).

5. **`is` vs `==` for lists**: `list1 == list2` compares element-wise equality; `list1 is list2` checks identity. Two lists with identical contents are `==` but not `is` unless they're literally the same object.

6. **Why does `list.index()` raise instead of returning -1?** Interviewers sometimes probe understanding of Python's "explicit is better than implicit" — use `in` first or wrap in `try/except ValueError`.

7. **Flipkart/Walmart favorite: rotate a list in O(n) with O(1) extra space** using the reversal algorithm (reverse whole, then reverse parts) — tests understanding of in-place list manipulation.

### Pitfalls summary (Lists)

- Mutable default arguments persist across calls.
- `[[x]*n]*n` shares row references.
- Shallow copies share nested mutable objects.
- Removing/inserting while iterating causes skipped elements or `IndexError`.
- `list.pop(0)` / `list.insert(0, x)` are O(n) — use `collections.deque` if you need O(1) operations at both ends.
- Lists use more memory per element than arrays of primitives (`array` module or NumPy) because every element is a full `PyObject*` pointer plus the pointed-to object's overhead.

---

## Tuples

### Immutable sequences

A `tuple` is an ordered, **immutable** sequence. Once created, you cannot add, remove, or reassign elements. Internally, tuples are also stored as a contiguous array of pointers, but because the size is fixed at creation, CPython does **not** over-allocate — a tuple's memory footprint is exactly what's needed, making tuples generally smaller and slightly faster to construct than lists of the same length.

```python
t = (1, 2, 3)
t[0] = 100   # TypeError: 'tuple' object does not support item assignment

# Tuples ARE hashable if all their elements are hashable -> usable as dict keys / set members
point_counts = {(0, 0): "origin", (1, 1): "diagonal"}
```

Immutability is shallow: a tuple containing a mutable object (like a list) is itself hashable-looking but will actually raise `TypeError` if you try to hash it, and the contained mutable object can still be mutated in place.

```python
t = (1, [2, 3])
t[1].append(4)     # allowed! mutating the LIST inside the tuple
print(t)             # (1, [2, 3, 4])
# hash(t)              # TypeError: unhashable type: 'list'
```

### List vs tuple: performance and memory (interview staple)

| Aspect | List | Tuple |
|---|---|---|
| Mutability | Mutable | Immutable |
| Memory | Over-allocated (extra headroom) | Exact size, no headroom |
| Creation speed | Slower (dynamic growth machinery) | Faster (fixed size known upfront) |
| Hashable | No | Yes, if all elements are hashable |
| Use as dict key/set member | No | Yes |
| Suitable for | Homogeneous, growing collection | Fixed, heterogeneous record; "frozen" data |
| Caching by CPython | No | Small tuples may be cached/interned in some cases |

```python
import sys
print(sys.getsizeof([1, 2, 3]))   # e.g. 88 bytes
print(sys.getsizeof((1, 2, 3)))   # e.g. 64 bytes  -- tuple is smaller
```

### Packing and unpacking

```python
# Packing: multiple values implicitly become a tuple
point = 3, 4
print(type(point), point)   # <class 'tuple'> (3, 4)

# Unpacking
x, y = point
print(x, y)   # 3 4

# Swapping without a temp variable (packing + unpacking combined)
a, b = 1, 2
a, b = b, a
print(a, b)   # 2 1

# Function returning multiple values is just tuple packing
def divmod_manual(a, b):
    return a // b, a % b

q, r = divmod_manual(17, 5)
```

### Starred unpacking

```python
first, *middle, last = [1, 2, 3, 4, 5]
print(first, middle, last)   # 1 [2, 3, 4] 5

a, *rest = (10, 20, 30)
print(a, rest)   # 10 [20, 30]

*init, last = [1, 2, 3]
print(init, last)   # [1, 2] 3

# Ignoring values you don't care about
_, second, *_ = (1, 2, 3, 4, 5)

# In function calls / definitions (related but distinct usage)
def f(*args, **kwargs):
    print(args, kwargs)

f(1, 2, a=3)   # (1, 2) {'a': 3}
```

The starred target always collects into a **list**, even when unpacking a tuple. Only one starred expression is allowed per unpacking assignment.

### Named tuples

`collections.namedtuple` creates a lightweight, immutable class with named fields, still backed by a tuple (so it's memory-efficient and indexable), but far more readable than positional tuple access.

```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(p.x, p.y)      # 3 4
print(p[0], p[1])     # 3 4  -- still indexable like a normal tuple
print(p)                # Point(x=3, y=4)

# Immutable
# p.x = 10   # AttributeError

# Useful helpers
p2 = p._replace(x=100)      # returns a NEW namedtuple, original unchanged
print(p2)                     # Point(x=100, y=4)
print(p._asdict())              # {'x': 3, 'y': 4}
print(Point._fields)              # ('x', 'y')

# From an iterable
p3 = Point._make([7, 8])
```

`typing.NamedTuple` is the modern, type-annotated alternative, preferred in production code for readability and static-analysis support:

```python
from typing import NamedTuple

class PointT(NamedTuple):
    x: int
    y: int
    label: str = "unnamed"   # default values supported

pt = PointT(1, 2)
print(pt.label)   # 'unnamed'
print(isinstance(pt, tuple))   # True -- still a tuple under the hood
```

Both forms produce classes that are subclasses of `tuple`, so they support `len()`, iteration, unpacking, equality comparison by value, and hashing — while also giving named-attribute access. `typing.NamedTuple` additionally supports methods and class-level docstrings, which plain `namedtuple` also supports but less ergonomically.

### Common interview questions and gotchas (Tuples)

1. **"Are tuples always faster than lists?"** — Creation and iteration are marginally faster, and memory footprint is smaller, but indexing/element access speed is essentially the same O(1) for both. The real win is immutability guarantees + hashability.

2. **Single-element tuple trap** (very common gotcha, asked at Microsoft/Adobe):

```python
not_a_tuple = (5)     # this is just int 5 with parens!
print(type(not_a_tuple))   # <class 'int'>

actual_tuple = (5,)    # the trailing comma makes it a tuple
print(type(actual_tuple))   # <class 'tuple'>
```

3. **"Can a tuple be unhashable?"** — Yes, if it contains any unhashable element (list, dict, set). `hash((1, [2,3]))` raises `TypeError`.

4. **Why use namedtuple over a plain class or dict?** — Memory efficiency (no `__dict__` per instance, similar to `__slots__`), tuple-like behavior (comparable, iterable, unpackable), and immutability, while still giving readable field access. Good discussion point: contrast with `dataclass(frozen=True)`.

5. **Tuple concatenation creates a new tuple each time** — repeatedly doing `t = t + (x,)` in a loop is O(n) per operation, O(n^2) total — same pitfall as string concatenation in a loop.

### Pitfalls summary (Tuples)

- Forgetting the trailing comma for one-element tuples.
- Assuming tuples are always faster — the difference is usually negligible except at scale or in tight loops.
- Believing tuples are always hashable — only true if every element is hashable.
- Mutating a list nested inside a tuple (allowed, and can be surprising).

---

## Sets

### Hash-based collection (internals)

A `set` is an unordered collection of unique, hashable elements implemented as a **hash table** (open-addressing scheme, similar in spirit to `dict`'s implementation, though sets and dicts are separate C structures in CPython).

- Each element's `hash()` value determines its bucket/slot in the underlying table.
- **Average-case O(1)** for `add`, `remove`, and membership testing (`in`), because hashing jumps directly to the (probable) slot instead of scanning.
- **Worst case O(n)** if there are many hash collisions (pathological/adversarial input), though Python's hash randomization (`PYTHONHASHSEED`) for strings mitigates deliberate collision attacks.
- Like dicts, sets over-allocate their internal table and resize (roughly doubling, using a growth table) when the load factor gets too high, to keep operations close to O(1) amortized.
- All elements must be **hashable** — meaning they must implement `__hash__` and `__eq__` consistently, and typically must be immutable (or at least not mutated while stored in the set, since mutating would change its hash bucket without the set knowing).

```python
s = set()
s.add(1)
s.add(2)
s.add(2)          # no-op, duplicates are silently ignored
print(s)            # {1, 2}
print(3 in s)         # O(1) average -- False
```

### Unhashable types cannot go into sets or be dict keys

```python
s = set()
s.add([1, 2])       # TypeError: unhashable type: 'list'
s.add({1: 2})         # TypeError: unhashable type: 'dict'
s.add({1, 2})           # TypeError: unhashable type: 'set'
s.add((1, [2, 3]))        # TypeError: tuple contains unhashable list

s.add((1, 2))              # OK -- tuple of hashables is hashable
s.add(frozenset([1, 2]))     # OK -- frozenset is hashable
```

Rule of thumb: `list`, `dict`, `set` are unhashable (mutable); `int`, `float`, `str`, `bool`, `tuple` (of hashables), `frozenset` are hashable.

### Frozen sets

`frozenset` is the immutable counterpart to `set` — same hash-table-based membership performance, but cannot be modified after creation, and therefore **is itself hashable**, so it can be used as a dict key or a member of another set.

```python
fs = frozenset([1, 2, 3])
# fs.add(4)   # AttributeError: no add method

nested = {frozenset([1, 2]), frozenset([3, 4])}   # set of frozensets -- valid

cache_key = frozenset({"a": 1, "b": 2}.items())     # common pattern: hashable "dict" key
```

### Set operations

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

print(a.union(b))                 # {1, 2, 3, 4, 5, 6}
print(a | b)                        # same, operator form

print(a.intersection(b))              # {3, 4}
print(a & b)                            # same

print(a.difference(b))                    # {1, 2}  -- elements in a but not b
print(a - b)                                # same

print(a.symmetric_difference(b))              # {1, 2, 5, 6} -- in a or b, not both
print(a ^ b)                                    # same

# In-place variants (mutate the left operand)
a.update(b)              # a |= b   -- union in place
a.intersection_update(b)   # a &= b -- keep only common elements
a.difference_update(b)       # a -= b -- remove elements found in b
a.symmetric_difference_update(b)  # a ^= b

# Relational operators
print({1, 2}.issubset({1, 2, 3}))     # True
print({1, 2} <= {1, 2, 3})              # True (subset)
print({1, 2} < {1, 2, 3})                 # True (proper subset)
print({1, 2, 3}.issuperset({1, 2}))         # True
print({1, 2}.isdisjoint({3, 4}))              # True -- no overlap
```

Complexity of set operations (n = size of smaller set, m = size of larger, roughly):

| Operation | Average Complexity |
|---|---|
| `add` | O(1) |
| `remove` / `discard` | O(1) |
| `x in s` | O(1) |
| `union` | O(len(a) + len(b)) |
| `intersection` | O(min(len(a), len(b))) |
| `difference` | O(len(a)) |
| `copy` | O(n) |

Note: `remove(x)` raises `KeyError` if `x` is absent; `discard(x)` silently does nothing — a frequently tested distinction.

### Common interview questions and gotchas (Sets)

1. **Dedup while preserving order** (Amazon/Uber favorite): a plain `set()` loses order. Use `dict.fromkeys()` (dict preserves insertion order since 3.7) instead:

```python
items = [3, 1, 2, 3, 1, 4]
deduped_unordered = list(set(items))          # order not guaranteed
deduped_ordered = list(dict.fromkeys(items))    # [3, 1, 2, 4] -- preserves first occurrence
```

2. **`remove` vs `discard` vs `pop`**: `pop()` removes and returns an *arbitrary* element (sets are unordered — there is no "first" element), and raises `KeyError` on an empty set.

3. **Why can't you put a list in a set?** — Tests understanding of hashability and why mutability is fundamentally incompatible with a hash-table bucket assignment that must stay valid for the object's lifetime in the container.

4. **Set comprehension**:

```python
squares_set = {x * x for x in range(-3, 4)}   # {0, 1, 4, 9}
```

5. **Finding duplicates efficiently** (Flipkart/Walmart): use a set to track "seen" elements for O(n) duplicate detection instead of O(n^2) nested loops.

```python
def has_duplicate(nums):
    seen = set()
    for n in nums:
        if n in seen:
            return True
        seen.add(n)
    return False
```

### Pitfalls summary (Sets)

- Iteration order is not guaranteed/deterministic in the way list order is (though in practice, insertion order can appear stable for a given run — never rely on it).
- Unhashable elements cannot be added.
- `remove` throws, `discard` doesn't — mixing these up is a common bug.
- Sets can't contain other sets (must use `frozenset`).
- Building a large set via repeated `|` (creating new sets) instead of `update()`/`|=` is less efficient than in-place mutation.

---

## Dictionaries

### Hash maps (internals)

CPython's `dict` is a hash table using **open addressing** (specifically a variant with pseudo-random probing) to resolve collisions, rather than separate chaining (linked lists per bucket) used by some other languages' hash maps.

- Each key's hash determines an initial probe position; on collision, CPython computes a perturbed probe sequence to find the next candidate slot.
- Since Python 3.6 (as an implementation detail) / **guaranteed in the language spec since Python 3.7**, dicts **preserve insertion order** — this was achieved by splitting the hash table into two parts: a compact array of `(key, hash, value)` entries in insertion order, plus a sparser table of indices into that array used purely for hash lookups. This "compact dict" design (from PEP 468 / the dict implementation change) also reduced memory usage versus the old implementation.
- Average time complexity for `get`/`set`/`delete`/`in` is **O(1)**; worst case is O(n) under heavy hash collisions.
- Dicts resize (grow the underlying table, roughly doubling small tables and using different growth ratios at larger sizes) when the load factor exceeds a threshold, to keep probe sequences short.
- Keys must be hashable, same rule as set elements (in fact `dict` and `set` share much of their underlying hashing machinery in CPython).

```python
d = {}
d["a"] = 1
d["b"] = 2
d["c"] = 3
print(list(d.keys()))   # ['a', 'b', 'c'] -- guaranteed insertion order (3.7+)

print(d.get("z", "default"))   # O(1) average lookup with fallback
print("a" in d)                  # O(1) average membership test (checks KEYS)
```

### Dict operation complexity table

| Operation | Average | Worst Case |
|---|---|---|
| `d[key]` get | O(1) | O(n) |
| `d[key] = v` set | O(1) | O(n) |
| `del d[key]` | O(1) | O(n) |
| `key in d` | O(1) | O(n) |
| `d.get(key)` | O(1) | O(n) |
| `len(d)` | O(1) | O(1) |
| Iterate all items | O(n) | O(n) |
| `d.copy()` | O(n) | O(n) |
| `dict(d1, **d2)` merge | O(n + m) | O(n + m) |

### Dictionary views

`dict.keys()`, `dict.values()`, and `dict.items()` return **view objects** — dynamic, live windows onto the dict's data, not copies/snapshots.

```python
d = {"a": 1, "b": 2, "c": 3}
keys_view = d.keys()
items_view = d.items()

d["d"] = 4
print(keys_view)   # dict_keys(['a', 'b', 'c', 'd']) -- reflects the update automatically!

# Views are set-like (keys and items views support set operations because
# keys are guaranteed unique and hashable)
d2 = {"a": 1, "b": 99, "e": 5}
print(d.keys() & d2.keys())      # {'a', 'b'}  -- intersection
print(d.keys() | d2.keys())        # union of key sets
print(d.keys() - d2.keys())          # keys only in d
print(d.items() & d2.items())          # {('a', 1)} -- only exact (key, value) matches

# values() is NOT set-like (values need not be unique/hashable)
# d.values() & d2.values()   # TypeError
```

Views are also **iterable and support `len()`**, and iterating them while the dict is structurally modified (keys added/removed, not just value updates) raises `RuntimeError: dictionary changed size during iteration`.

```python
d = {"a": 1, "b": 2}
for k in d:
    d["c"] = 3   # RuntimeError: dictionary changed size during iteration
```

### Ordered dictionaries: OrderedDict vs plain dict

Before Python 3.7, if you needed guaranteed order, you used `collections.OrderedDict`. Since 3.7, plain `dict` also preserves insertion order as a language guarantee, so the two overlap significantly — but differences remain:

| Aspect | `dict` (3.7+) | `collections.OrderedDict` |
|---|---|---|
| Insertion order preserved | Yes (guaranteed) | Yes |
| Equality comparison | Order-insensitive (`{"a":1,"b":2} == {"b":2,"a":1}` -> True) | Order-sensitive (`OrderedDict` equality checks order too) |
| `move_to_end()` method | No | Yes -- O(1) move a key to either end |
| `popitem(last=True/False)` | Only pops last (`popitem()`), no `last` param | Supports popping from either end |
| Reordering support | Manual (rebuild) | Built-in, efficient (backed by a doubly linked list internally) |
| Memory | Slightly less overhead | Slightly more overhead (extra linked-list bookkeeping) |
| Use case | Default choice, general use | When you need explicit reordering (e.g., LRU cache) |

```python
from collections import OrderedDict

od = OrderedDict()
od["a"] = 1
od["b"] = 2
od["c"] = 3
od.move_to_end("a")           # a moves to the end
print(od)                       # OrderedDict([('b', 2), ('c', 3), ('a', 1)])
od.move_to_end("c", last=False)   # move c to the FRONT
print(od)                           # OrderedDict([('c', 3), ('b', 2), ('a', 1)])

# Classic use: LRU cache building block
od.popitem(last=False)   # pop the oldest (front) item -- O(1)

# Equality difference
d1 = {"a": 1, "b": 2}
d2 = {"b": 2, "a": 1}
print(d1 == d2)   # True -- plain dicts ignore order in equality

od1 = OrderedDict([("a", 1), ("b", 2)])
od2 = OrderedDict([("b", 2), ("a", 1)])
print(od1 == od2)   # False -- OrderedDict equality is order-sensitive
```

`functools.lru_cache` and modern `dict`-based LRU implementations often now use plain `dict` + `move_to_end`-like tricks are unavailable on plain dict, which is exactly why `OrderedDict` still matters for hand-rolled LRU cache interview questions (a very common Amazon/Google/Uber system-design-adjacent coding question).

### Dictionary comprehension

```python
squares = {x: x * x for x in range(6)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# Filtering with a comprehension
evens_only = {k: v for k, v in squares.items() if v % 2 == 0}

# Swapping keys and values (requires values to be hashable and unique)
original = {"a": 1, "b": 2}
inverted = {v: k for k, v in original.items()}
# {1: 'a', 2: 'b'}

# Building a frequency map -- extremely common interview pattern
from collections import Counter
text = "abracadabra"
freq = {}
for ch in text:
    freq[ch] = freq.get(ch, 0) + 1
# or simply: freq = Counter(text)
```

### Merge operators (PEP 584) and unpacking merge

Python 3.9 introduced the `|` (merge) and `|=` (update-in-place) operators for dicts, as cleaner alternatives to `{**d1, **d2}` or `dict.update()`.

```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 20, "c": 3}

merged = d1 | d2          # NEW dict: {'a': 1, 'b': 20, 'c': 3}  -- d2 wins on conflicts
print(d1)                   # unchanged: {'a': 1, 'b': 2}

d1 |= d2                      # in-place update, equivalent to d1.update(d2)
print(d1)                       # {'a': 1, 'b': 20, 'c': 3}

# Pre-3.9 equivalent using double-star unpacking (works on all Python 3 versions)
merged_old = {**d1, **d2}    # later dict's keys win on conflict
```

**Ordering rule for conflicts and key order in merges:** in both `d1 | d2` and `{**d1, **d2}`, when a key exists in both, the **rightmost** dict's value wins, but the key's **position** in the resulting dict follows wherever it first appeared (typically from `d1` if `d1` had it first) — a subtle detail interviewers sometimes probe.

```python
d1 = {"a": 1, "b": 2}
d2 = {"b": 99, "c": 3}
print(d1 | d2)   # {'a': 1, 'b': 99, 'c': 3}  -- 'b' stays in its original position, value updated
```

### Common interview questions and gotchas (Dictionaries)

1. **Mutable default argument, dict version** — same root cause as the list version:

```python
def add_entry(key, value, store={}):   # BUG
    store[key] = value
    return store
```

2. **`dict.get(key, default)` vs `dict[key]`** — `[]` raises `KeyError` if missing; `.get()` returns `None` or a specified default. Also `setdefault(key, default)` sets AND returns in one O(1) call — useful for building adjacency lists / grouping:

```python
graph = {}
edges = [("a", "b"), ("a", "c"), ("b", "c")]
for u, v in edges:
    graph.setdefault(u, []).append(v)
print(graph)   # {'a': ['b', 'c'], 'b': ['c']}

# collections.defaultdict is the cleaner alternative
from collections import defaultdict
graph2 = defaultdict(list)
for u, v in edges:
    graph2[u].append(v)
```

3. **"Since when does dict preserve order, and is it guaranteed or just an implementation detail?"** — Implementation detail in 3.6 (CPython-specific), became an official **language guarantee** in the 3.7 spec. Before 3.6, dicts were explicitly unordered — this is a frequently asked trivia/history question at Google and Microsoft.

4. **Why can't you use a list as a dict key?** — Same hashability reasoning as sets; tests whether the candidate connects dict-key rules to set-element rules (they're the same rule: must be hashable + `__eq__` consistent with `__hash__`).

5. **Iterating and mutating a dict at the same time**:

```python
d = {"a": 1, "b": 2, "c": 3}
for k in list(d.keys()):     # iterate over a COPY of keys to allow safe mutation
    if d[k] % 2 == 0:
        del d[k]
```

6. **Two dicts equal regardless of order, but hash(dict) is not defined** — dicts are unhashable themselves (mutable), which is exactly why you cannot nest a `dict` as a `dict` key or `set` member (only `frozenset`/tuple-of-hashables workarounds apply).

7. **Merging dicts: `update()` vs `|` vs `{**a, **b}`** — Walmart/Adobe frequently ask to explain all three and their Python-version availability (`|` requires 3.9+, `**` unpacking works on all Python 3, `.update()` is the oldest/most universal and mutates in place).

8. **Counting with `Counter` vs manual dict** — `collections.Counter` is a `dict` subclass specialized for counting, supports `.most_common(n)`, and arithmetic between counters (`+`, `-`, `&`, `|`).

```python
from collections import Counter
c1 = Counter("aabbbc")
print(c1)                  # Counter({'b': 3, 'a': 2, 'c': 1})
print(c1.most_common(2))     # [('b', 3), ('a', 2)]
```

### Pitfalls summary (Dictionaries)

- Mutable default argument for dicts, same as lists.
- Assuming dict order was always guaranteed (only since 3.7).
- Using `dict[key]` without checking existence -> `KeyError`; prefer `.get()` or `setdefault()`/`defaultdict` where appropriate.
- Mutating a dict's size while iterating over it directly (`RuntimeError`).
- Believing `dict.values()` supports set operations like `.keys()`/`.items()` do — it doesn't, since values aren't guaranteed unique/hashable.
- Confusing `OrderedDict` equality (order-sensitive) with plain `dict` equality (order-insensitive).
- Forgetting that `d1 | d2` creates a new dict (no mutation) while `d1 |= d2` mutates `d1` in place.
- Unhashable keys (lists, dicts, sets) raise `TypeError` immediately.

---

## Overall time-complexity cheat sheet

| Operation | list | tuple | set | dict |
|---|---|---|---|---|
| Index/key access | O(1) | O(1) | N/A | O(1) avg |
| Append/insert (end) | O(1) amortized | N/A (immutable) | O(1) avg (`add`) | O(1) avg (`d[k]=v`) |
| Insert at front/middle | O(n) | N/A | N/A | N/A |
| Delete | O(n) (by value) / O(1) (`pop()` end) | N/A | O(1) avg | O(1) avg |
| Membership test (`in`) | O(n) | O(n) | O(1) avg | O(1) avg (keys) |
| Iteration | O(n) | O(n) | O(n) | O(n) |
| Copy | O(n) | O(n) (often just returns same object since immutable) | O(n) | O(n) |
| Sort | O(n log n) | N/A (`sorted()` returns new list) | N/A (`sorted()` returns new list) | N/A |

This table is one of the most frequently requested "whiteboard from memory" items in SDE-2 interviews — being able to reproduce it and explain *why* (over-allocation for lists, hashing for sets/dicts) demonstrates real understanding rather than memorization.
