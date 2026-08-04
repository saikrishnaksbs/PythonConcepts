# Collections Module

Python's built-in collections (list, dict, set, tuple) are generic and versatile. The `collections` module provides specialized, high-performance container data types designed for specific use-cases. For SDE-2 roles, you should know the time complexities, applications, and internal structures of these collections.

## Table of Contents

- [`Counter`](#counter)
- [`defaultdict`](#defaultdict)
- [`OrderedDict`](#ordereddict)
- [`deque`](#deque)
- [`ChainMap`](#chainmap)
- [`namedtuple`](#namedtuple)

---

## `Counter`

### Explanation

`Counter` is a dictionary subclass designed to count hashable objects. It maps elements to their counts (integers).

### Code example

```python
from collections import Counter

counts = Counter("abracadabra")
print(counts)  # Counter({'a': 5, 'b': 2, 'r': 2, 'c': 1, 'd': 1})

# Get 2 most common elements (O(N log K) using heapq under the hood)
print(counts.most_common(2))  # [('a', 5), ('b', 2)]
```

---

## `defaultdict`

### Explanation

`defaultdict` is a dictionary subclass that calls a factory function (provided during instantiation) to supply a default value when a requested key is missing, avoiding `KeyError`.

### Code example

```python
from collections import defaultdict

# Factory function is 'list'
grouped = defaultdict(list)
grouped['a'].append(1)  # If 'a' is missing, calls list() to create an empty list first.
print(grouped)  # defaultdict(<class 'list'>, {'a': [1]})
```

---

## `OrderedDict`

### Explanation

`OrderedDict` is a dictionary subclass that remembers the order keys were first inserted.

### Why it matters / internals

- Since Python 3.7, the standard `dict` also maintains insertion order.
- However, `OrderedDict` remains useful because:
  - It supports reordering: `move_to_end(key, last=True)`.
  - Equality checks are order-sensitive (standard `dict` equality checks are order-insensitive).
  - It handles `popitem(last=True)` efficiently, supporting both LIFO and FIFO behavior.

---

## `deque`

### Explanation

A `deque` (double-ended queue) is a sequence container designed for fast $O(1)$ appends and pops from both ends.

### Why it matters / internals

- Standard Python `list` is a dynamic array. Appending/popping from the right is $O(1)$, but inserting/removing from the left is $O(N)$ because all other elements must be shifted in memory.
- `deque` is implemented as a **doubly linked list of blocks** (chunks of memory). This ensures $O(1)$ operations on both ends, though random access indexing ($O(K)$) is slower than a list ($O(1)$).

### Code example

```python
from collections import deque

q = deque()
q.append(1)      # Append right
q.appendleft(2)  # Append left (O(1))
q.pop()          # Pop right
q.popleft()      # Pop left (O(1))
```

---

## `ChainMap`

### Explanation

`ChainMap` groups multiple dictionaries into a single, logical view. When looking up a key, it searches each dictionary sequentially from first to last.

### Code example

```python
from collections import ChainMap

default_config = {"theme": "light", "verbose": False}
user_config = {"theme": "dark"}

config = ChainMap(user_config, default_config)
print(config["theme"])    # "dark" (Found in user_config)
print(config["verbose"])  # False (Found in default_config)
```

---

## `namedtuple`

### Explanation

`namedtuple` is a factory function that generates subclasses of `tuple` with named fields. It provides a lightweight, immutable object structure without the memory overhead of dicts or standard classes.

### Code example

```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(10, 20)

print(p.x, p.y)  # 10 20
print(p[0])      # 10 (Still behaves like a regular tuple!)
```

---

## Common Interview Questions

1. **"When would you use `deque` over `list` as a queue?"** Whenever you need FIFO behavior (`popleft`) — a plain list's `pop(0)` is O(n) because every remaining element shifts left in memory, whereas `deque.popleft()` is O(1).
2. **"`Counter` vs `defaultdict(int)` for counting?"** `Counter` is purpose-built: supports `.most_common()`, arithmetic between counters (`+`, `-`, `&`, `|`), and defaults missing keys to 0 automatically — `defaultdict(int)` is more general but lacks these conveniences.
3. **"Why does `ChainMap` avoid copying dictionaries?"** It keeps references to the original mappings and searches them in order on each lookup — writes go only to the first mapping, so updating `config` doesn't mutate `user_config` or `default_config` themselves, but any external mutation to those dicts is reflected live.
4. **Pitfall:** `deque(maxlen=n)` silently discards elements from the opposite end once full — useful for sliding windows/ring buffers but easy to misuse expecting unbounded growth.
5. **Pitfall:** `namedtuple` instances are still tuples — `==` compares by value/position, and they remain immutable, so any "modification" must go through `._replace()` and produce a new object.
