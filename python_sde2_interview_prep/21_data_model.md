# Data Model

This file covers the Python data model concepts that come up constantly in SDE-2 interviews at companies like Google, Amazon, Microsoft, Atlassian, Uber, Flipkart, Walmart, and Adobe: mutability, hashability, identity vs equality, references, and copy semantics. These topics are favorites because they expose whether a candidate actually understands CPython internals versus having only surface-level syntax knowledge.

## Mutable vs Immutable

### Explanation

In Python, every value is an object, and every object has an identity, a type, and a value. Whether an object's value can change after creation determines whether it is mutable or immutable.

**Immutable types**: `int`, `float`, `bool`, `complex`, `str`, `tuple`, `frozenset`, `bytes`, `NoneType`. Once created, their internal state can never change. Any operation that looks like it "modifies" them actually creates a new object and rebinds the name to it.

**Mutable types**: `list`, `dict`, `set`, `bytearray`, and most user-defined classes (unless you explicitly lock them down with `__slots__` + no setters, or use `frozen=True` dataclasses / `namedtuple`). Their internal state can be changed in place, and their `id()` stays the same across mutation.

CPython internals worth knowing:

- **`id()`** returns the memory address of the object in CPython (implementation detail, but commonly asked). `id()` is guaranteed unique and constant for the object's lifetime.
- **String interning**: CPython automatically interns (caches and reuses) certain strings — identifiers-like strings (matching `[a-zA-Z0-9_]*`), string literals in code that look like valid identifiers, and short strings created at compile time. This is a memory/performance optimization, not a language guarantee. You can force interning with `sys.intern()`.
- **Small integer caching**: CPython pre-allocates and caches integers in the range **-5 to 256** at interpreter startup. Any reference to an int in that range reuses the same cached object rather than allocating a new one. This is why `a = 100; b = 100; a is b` is `True`, but `a = 1000; b = 1000; a is b` is often `False` (though not guaranteed — compilers/peephole optimizers can still fold constants in the same code object).
- Tuples are immutable, but a tuple containing a mutable object (like a list) can appear to "change" because the *contained* mutable object changes, even though the tuple's own sequence of references never changes.

### Why it matters for SDE-2 interviews

- Determines default argument pitfalls (see mutable default argument section below).
- Determines whether an object can be a dict key / set member (must be hashable, and hashability is closely tied to immutability by convention).
- Affects function call semantics — "pass by object reference," not pass-by-value or pass-by-reference in the C/Java sense.
- Performance implications: immutable objects can be freely shared/cached; mutable objects need defensive copying.
- Concurrency implications: immutable objects are inherently thread-safe for reads; mutable objects require synchronization.

### Code Example

```python
# Immutability demo
a = "hello"
b = "hello"
print(a is b, id(a) == id(b))  # True True (interned literal)

s1 = "hello world!"  # contains a space -> not identifier-like, may not be interned
s2 = "hello world!"
print(s1 is s2)  # Often False (CPython, not guaranteed)

# Small integer caching
x = 100
y = 100
print(x is y)  # True (cached, -5 to 256)

x2 = 1000
y2 = 1000
print(x2 is y2)  # Typically False (outside cache range)

# Tuples are immutable, but can "contain" mutable state
t = (1, 2, [3, 4])
print(id(t))
t[2].append(5)          # allowed! we mutate the *list inside* the tuple
print(t)                # (1, 2, [3, 4, 5])
print(id(t))             # same id -- the tuple itself never changed

# Strings are immutable -- "mutating" creates a new object
s = "abc"
before_id = id(s)
s += "d"
print(id(s) == before_id)  # False, new object created

# sys.intern to force interning
import sys
a3 = sys.intern("hello world!")
b3 = sys.intern("hello world!")
print(a3 is b3)  # True, now guaranteed
```

### Common Interview Questions / Gotchas

- "Why does `a = 256; b = 256; a is b` return `True` but `a = 257; b = 257; a is b` sometimes return `False`?" — small int caching boundary.
- "Is a tuple truly immutable if it holds a list?" — yes, the tuple's references are fixed; the referenced object's mutability is separate.
- "What is string interning and why does CPython do it?" — memory optimization + faster `==`/`is` comparisons for dict keys like attribute names.
- "Name three immutable and three mutable built-in types."
- "Why are strings immutable in Python (design rationale)?" — enables hashability (safe dict keys), safety when shared across threads/functions, and interning optimizations.

### Pitfalls / Common Mistakes

- Relying on `is` for value comparison of small integers/strings — this is an implementation detail, not a language guarantee. Never write code that depends on interning behavior across the general case.
- Assuming a `tuple` is always deeply immutable — forgetting that it can hold mutable elements, causing hidden mutation bugs (e.g., using such a tuple as a dict key will still work syntactically but can lead to subtle "the value seems to change even though it's a key" confusion if someone mutates the inner list — though note this specific case would actually break hashing consistency, see next section).
- String concatenation in a loop (`s += chunk`) creates a new immutable string object every iteration — O(n^2) behavior; use `"".join(list_of_parts)` instead.

## Hashability

### Explanation

An object is **hashable** if it has a `__hash__()` method that returns a constant integer for its lifetime, and that integer is consistent with `__eq__()`. Hashable objects can be used as dictionary keys and set members because dicts/sets are implemented as hash tables — they use the hash value to bucket objects for O(1) average lookup, then use `__eq__` to resolve collisions within a bucket.

**The `__hash__` / `__eq__` contract**:
1. If `a == b`, then `hash(a) == hash(b)` must hold. (Required — violating this breaks dict/set correctness silently.)
2. If `hash(a) == hash(b)`, `a == b` is NOT required (hash collisions are allowed and expected).
3. `hash(a)` must return the same value every time for the same object, for the object's entire lifetime (this is why mutable objects are, by convention, unhashable — their value can change, which would change their hash, breaking the invariant that a key's bucket location stays stable).

**Default behavior of user-defined classes**: By default, every object inherits `__hash__` from `object`, which uses `id(self)` (identity-based hash), and inherits `__eq__` from `object`, which is also identity-based (`is`). So two distinct instances with identical attribute values are NOT equal and NOT the same hash by default.

**If you override `__eq__` without overriding `__hash__`**, Python automatically sets `__hash__` to `None` on that class, making instances unhashable. This is a deliberate safety mechanism, since a custom `__eq__` almost certainly breaks the identity-based hash contract.

**Built-in hashable types**: `int`, `float`, `str`, `bytes`, `frozenset`, `tuple` (only if every element is hashable), `bool`, `NoneType`, and functions/classes.
**Built-in unhashable types**: `list`, `dict`, `set`, `bytearray`.

### Why it matters for SDE-2 interviews

- Dict/set based algorithms (two-sum, memoization with `@lru_cache`, deduplication, graph adjacency using sets) require candidates to reason about what can be a key.
- Designing value objects / DTOs that need to live in sets or be dict keys (e.g., caching a function's results keyed by an argument tuple).
- Debugging "TypeError: unhashable type" bugs — a very common real-world bug when someone uses a list as a dict key or a class instance in a set without implementing `__hash__`.
- Distributed systems / caching questions: hashing is the basis of hash-based sharding, consistent hashing, cache key generation.

### Code Example

```python
class PointBad:
    def __init__(self, x, y):
        self.x, self.y = x, y

class PointGood:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __eq__(self, other):
        if not isinstance(other, PointGood):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"PointGood({self.x}, {self.y})"

p1 = PointBad(1, 2)
p2 = PointBad(1, 2)
print(p1 == p2)          # False (identity-based default __eq__)
print(hash(p1) == hash(p2))  # False (identity-based default __hash__)

g1 = PointGood(1, 2)
g2 = PointGood(1, 2)
print(g1 == g2)          # True (value-based __eq__)
print(hash(g1) == hash(g2))  # True (value-based __hash__)

s = {g1, g2}
print(len(s))  # 1 -- treated as duplicates in a set

d = {g1: "first"}
print(d[g2])   # "first" -- g2 can look up g1's entry because they're equal & same hash

# Unhashable: list, dict, set
try:
    bad_set = {[1, 2, 3]}
except TypeError as e:
    print(f"Error: {e}")  # unhashable type: 'list'

# Overriding __eq__ without __hash__ disables hashing
class NoHash:
    def __eq__(self, other):
        return True

print(NoHash.__hash__)  # None
try:
    hash(NoHash())
except TypeError as e:
    print(f"Error: {e}")  # unhashable type: 'NoHash'

# Tuple hashability depends on its contents
print(hash((1, 2, 3)))       # OK
try:
    hash((1, [2, 3]))
except TypeError as e:
    print(f"Error: {e}")     # unhashable type: 'list'
```

### Common Interview Questions / Gotchas

- "Why does overriding `__eq__` set `__hash__` to `None` automatically?" — Python protects you from breaking the hash/eq contract silently.
- "Can a tuple always be a dict key?" — only if all its elements are hashable, recursively.
- "What happens if two unequal objects have the same hash?" — collision; the hash table stores both in the same bucket, `__eq__` disambiguates. Performance degrades toward O(n) in adversarial cases (hash flooding), but correctness is preserved.
- "How would you make a mutable class safely usable as a dict key?" — either make it immutable (freeze fields, use `__slots__`, raise in setters) or compute the hash from an immutable snapshot and document that it must not be mutated while used as a key/in a set.
- "What's `functools.lru_cache` require of its arguments?" — all arguments must be hashable, since they become part of a cache key.

### Pitfalls / Common Mistakes

- Mutating an object's fields that were used to compute `__hash__` after inserting it into a set/dict — the object becomes "lost" (unfindable at its old bucket) even though it's still technically in the container. This is a classic silent-bug source.
- Forgetting to also override `__eq__` when overriding `__hash__` (or vice versa) — leads to inconsistent behavior violating the contract.
- Using mutable default objects (like lists) as dict keys and expecting it to "just work."
- Not returning `NotImplemented` (instead of `False`) from `__eq__` when types don't match, which can break reflected comparisons with other types.

## Identity vs Equality

### Explanation

`is` checks **identity** — whether two names refer to the exact same object in memory (equivalent to `id(a) == id(b)`). `==` checks **equality** — whether two objects are considered equal in value, which invokes `__eq__()` (falling back to identity comparison if `__eq__` isn't overridden).

- `is` is a language-level operator — cannot be overridden by user classes. It's essentially free (pointer comparison).
- `==` calls `a.__eq__(b)`; if that returns `NotImplemented`, Python tries `b.__eq__(a)`; if both fail, it falls back to identity comparison (`is`).
- `is None` is the idiomatic and recommended way to check for `None` (PEP 8), not `== None`, because `None` is a singleton and `is` avoids any possibility of a custom `__eq__` doing something unexpected.
- Similarly `is True` / `is False` should generally be avoided in favor of truthiness checks unless you specifically need to distinguish `True` from `1`.

### Why it matters for SDE-2 interviews

- Extremely common junior-vs-senior signal: candidates who use `==` and `is` interchangeably without understanding the difference get flagged quickly.
- Singleton pattern implementations rely on `is` checks.
- Sentinel value patterns (e.g., `_MISSING = object()`) rely on identity, not equality, to avoid collision with legitimate values like `None` or `0`.
- Cache/memoization correctness: using `is` mistakenly instead of `==` for value comparison causes subtle bugs when objects are equal in value but not identical in memory (e.g., across process boundaries or after deepcopy).

### Code Example

```python
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(a == b)  # True  -- same value
print(a is b)  # False -- different objects
print(a is c)  # True  -- same object

# None comparison
x = None
print(x is None)   # True -- idiomatic
print(x == None)    # True but discouraged; could be fooled by a custom __eq__

class Weird:
    def __eq__(self, other):
        return True  # equals everything, even None!

w = Weird()
print(w == None)  # True  <-- dangerous if you used == for a None-check
print(w is None)  # False <-- correct, identity can't be spoofed

# Overriding __eq__ for value semantics
class Money:
    def __init__(self, cents):
        self.cents = cents
    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return self.cents == other.cents
    def __repr__(self):
        return f"Money({self.cents})"

m1 = Money(500)
m2 = Money(500)
print(m1 == m2)  # True  -- custom __eq__
print(m1 is m2)  # False -- distinct objects

# Sentinel pattern using identity
_MISSING = object()

def get(d, key, default=_MISSING):
    if key in d:
        return d[key]
    if default is _MISSING:
        raise KeyError(key)
    return default

print(get({"a": 1}, "a"))       # 1
print(get({"a": 1}, "b", None))  # None (explicitly passed)
```

### Common Interview Questions / Gotchas

- "What's the difference between `is` and `==`? When would you use each?"
- "Why should you use `is None` instead of `== None`?"
- "Can `==` ever throw or behave unexpectedly? Give an example." — yes, via a custom `__eq__`, NaN comparisons (`float('nan') == float('nan')` is `False`!), or comparisons across incompatible types.
- "Is `1 == 1.0` True? Is `1 is 1.0` True?" — `==` True (value equal across numeric types), `is` False (different types/objects).
- "What does `NotImplemented` do in `__eq__`, and how is it different from `False`?"

### Pitfalls / Common Mistakes

- Using `==` when you actually need identity (e.g., sentinel/singleton detection) — allows a maliciously or accidentally crafted `__eq__` to spoof the check.
- Using `is` when you need value equality (e.g., comparing two separately-constructed but logically equal objects) — leads to false negatives.
- Forgetting `float('nan') != float('nan')` — NaN breaks reflexivity of `==`, a classic gotcha for numerical code and for anything using NaN as a dict/set member.
- Not handling `NotImplemented` correctly in custom `__eq__`, causing asymmetric comparison bugs (`a == b` differs from `b == a`).

## Object References

### Explanation

Every variable in Python is a **name bound to an object**, not a box holding a value. Assignment (`=`) never copies data — it just makes a name point to an existing object. This model is often described as "pass by object reference" (or "call by sharing") — distinct from both C's pass-by-value and C++/Java's pass-by-reference.

- When you pass an argument to a function, the parameter name is bound to the *same object* the caller's variable refers to. If the object is mutable and the function mutates it in place, the caller sees the change. If the function *rebinds* the parameter name to a new object, the caller's variable is unaffected (only the local name changed).
- CPython uses **reference counting** as its primary memory management mechanism (supplemented by a cyclic garbage collector for reference cycles). Every object has a refcount (`sys.getrefcount(obj)`) tracking how many references point to it; when it drops to zero, the object is immediately deallocated.
- `del x` doesn't delete the object — it removes the name `x` from the current namespace (decrementing the refcount of whatever it pointed to).

### Why it matters for SDE-2 interviews

- Explains a huge class of "why did my function's mutation/non-mutation surprise me" bugs.
- Foundational for understanding memory management, garbage collection, and why Python doesn't have manual `free()`.
- Comes up in system design discussions about memory efficiency (e.g., sharing large immutable objects across data structures is cheap because you're only copying a reference/pointer, not the data).
- Distinguishing pass-by-value vs pass-by-reference vs pass-by-object-reference is a common conceptual interview question, especially for candidates coming from Java/C++.

### Code Example

```python
import sys

def mutate_in_place(lst):
    lst.append(4)  # mutates the SAME object the caller sees

def rebind(lst):
    lst = [9, 9, 9]  # only rebinds the LOCAL name; caller's variable is untouched

original = [1, 2, 3]
mutate_in_place(original)
print(original)  # [1, 2, 3, 4] -- caller sees the mutation

rebind(original)
print(original)  # [1, 2, 3, 4] -- unchanged; rebind only affected local param

# Reference counting
a = [1, 2, 3]
print(sys.getrefcount(a))  # baseline count (includes the temp ref from getrefcount's own arg)
b = a
print(sys.getrefcount(a))  # count increases by 1
del b
print(sys.getrefcount(a))  # count decreases by 1

# Immutable objects "appear" copied because rebinding creates a new object
def increment(n):
    n += 1
    return n

x = 5
increment(x)
print(x)  # 5 -- ints are immutable; n += 1 rebinds n locally, doesn't affect x

# Multiple names, one object
p = {"key": "value"}
q = p
q["key"] = "changed"
print(p)  # {'key': 'changed'} -- p and q reference the same dict
print(p is q)  # True
```

### Common Interview Questions / Gotchas

- "Is Python pass-by-value or pass-by-reference?" — neither, precisely; it's "pass by object reference" / "call by sharing." Mutating a mutable object inside a function is visible to the caller; rebinding the parameter is not.
- "How does Python manage memory?" — reference counting (immediate deallocation at refcount 0) plus a generational cyclic garbage collector (`gc` module) to catch reference cycles that refcounting alone can't resolve.
- "What happens to `sys.getrefcount()` output and why is it always at least 1 higher than expected?" — the act of passing the object as an argument to `getrefcount` itself creates a temporary reference.
- "Why doesn't incrementing an int parameter inside a function affect the caller's variable?" — ints are immutable, so `+=` rebinds rather than mutates.
- "What causes a reference cycle, and how does Python detect/collect it?" — objects referencing each other (e.g., parent/child back-references) never hit refcount 0 via refcounting alone; the generational GC periodically scans for unreachable cycles.

### Pitfalls / Common Mistakes

- Assuming that passing a list/dict to a function is "safe" from mutation like it would be in a pass-by-value language — always be explicit about whether a function is expected to mutate its argument.
- Forgetting that reassigning a parameter inside a function never propagates back to the caller, regardless of mutability.
- Relying on `del` to free memory immediately when other references to the object still exist elsewhere — the object stays alive until refcount hits zero.
- Creating unintentional reference cycles (e.g., a `Node` with both `.parent` and `.children` back-references) without realizing the cyclic GC (not simple refcounting) is what eventually reclaims them, which can be less deterministic and touches on `__del__` finalizer ordering issues.

## Copy Semantics: Assignment vs Copy

### Explanation

- **Assignment (`b = a`)**: no copying at all. `b` and `a` become two names for the same object. Mutating through one is visible through the other.
- **Shallow copy**: creates a new outer object, but populates it with references to the *same* nested/child objects as the original. Changes to top-level structure (e.g., adding/removing an item from a list) don't affect the original, but mutating a nested mutable object (e.g., a list-of-lists) *does* affect both copies, since they share the inner objects.
- **Deep copy**: recursively copies the outer object and every object it references, all the way down, producing a fully independent object graph. Changes to nested structures in the deep copy do not affect the original at all.

Ways to shallow copy: `list(x)`, `x[:]`, `x.copy()`, `dict(x)`, `copy.copy(x)`. Ways to deep copy: `copy.deepcopy(x)`.

`copy.deepcopy` uses a `memo` dictionary internally to track already-copied objects by `id()`, so it correctly handles reference cycles and shared sub-objects (it won't infinitely recurse, and if two parts of the original point to the same sub-object, the deep copy preserves that sharing structure rather than duplicating it).

### Why it matters for SDE-2 interviews

- Directly tests understanding of the reference model above, applied to a very common real bug source: "I copied the list but the original still changed!"
- Comes up in caching layers, config object management, and anywhere you need isolated copies of complex nested state (e.g., simulation state, undo/redo stacks, test fixtures).
- Performance trade-off discussion: deep copy is more expensive (O(total nodes in object graph)) vs shallow copy O(top-level size) vs assignment O(1).

### Code Example

```python
import copy

# Assignment: no copy at all
original = [1, 2, 3]
alias = original
alias.append(4)
print(original)  # [1, 2, 3, 4] -- same object

# Shallow copy: new outer container, shared inner objects
matrix = [[1, 2], [3, 4]]
shallow = copy.copy(matrix)          # equivalently: matrix[:] or list(matrix)
print(shallow is matrix)              # False -- different outer list
print(shallow[0] is matrix[0])        # True  -- same inner list object!

shallow.append([5, 6])                # top-level change: doesn't affect original
print(matrix)                         # [[1, 2], [3, 4]] -- unaffected

shallow[0].append(99)                 # nested mutation: DOES affect original
print(matrix)                         # [[1, 2, 99], [3, 4]] -- original polluted!

# Deep copy: fully independent
matrix2 = [[1, 2], [3, 4]]
deep = copy.deepcopy(matrix2)
deep[0].append(99)
print(matrix2)  # [[1, 2], [3, 4]] -- unaffected, fully isolated
print(deep)      # [[1, 2, 99], [3, 4]]

# deepcopy handles cycles safely via its memo dict
node_a = {"name": "a"}
node_b = {"name": "b", "friend": node_a}
node_a["friend"] = node_b  # reference cycle: a -> b -> a

deep_copy = copy.deepcopy(node_a)
print(deep_copy["friend"]["friend"] is deep_copy)  # True -- cycle preserved, no infinite loop

# Shared sub-object structure is preserved by deepcopy (not duplicated)
shared = [1, 2]
container = [shared, shared]
dc = copy.deepcopy(container)
print(dc[0] is dc[1])  # True -- both copies still point to the SAME new shared object
```

### Common Interview Questions / Gotchas

- "What's the difference between `list(x)`, `x[:]`, `x.copy()`, `copy.copy(x)`, and `copy.deepcopy(x)`?" — the first four are all equivalent shallow copies for lists; `deepcopy` recursively copies everything.
- "If I shallow-copy a list of lists and mutate an inner list, does the original change?" — yes, because the inner lists are shared references.
- "How does `deepcopy` avoid infinite recursion on cyclic structures?" — it maintains a `memo` dict keyed by `id()` of already-copied objects, so it never revisits/recopies the same object twice.
- "Is `dict(d)` a shallow or deep copy?" — shallow: new dict, same value references.
- "What's the time/space complexity difference between shallow and deep copy?" — shallow is O(n) at the top level only; deep copy is O(total number of objects in the full nested structure), and also uses more memory since nothing is shared.
- "Can you deepcopy an object holding a file handle or a lock?" — often no / requires customizing `__deepcopy__`, since some resources (sockets, file handles, thread locks) cannot be meaningfully duplicated; you can define `__copy__`/`__deepcopy__` on a class to control this behavior.

### Pitfalls / Common Mistakes

- Assuming `list.copy()` or slicing gives you full independence from nested mutable structures — it only protects the top level.
- Using `copy.deepcopy` reflexively everywhere for "safety" without considering the performance cost on large or deeply nested object graphs.
- Forgetting that deepcopy on objects with custom `__reduce__`/`__deepcopy__`/unpicklable attributes (like open file handles, DB connections, locks, generators) can fail or behave unexpectedly unless explicitly handled.
- Not accounting for shared-reference preservation — assuming deepcopy always fully duplicates everything, when it actually preserves aliasing relationships that existed in the original (via the memo).

## Mutable Default Argument Pitfall

### Explanation

Python evaluates default argument values **exactly once**, at function *definition* time (when the `def` statement executes), not on every call. If the default value is a mutable object (list, dict, set), that *same* object is reused across every call that doesn't explicitly supply the argument — and if the function mutates it, the mutation persists and leaks into subsequent calls. This is arguably the most famous Python gotcha and a near-guaranteed interview question at every level, including SDE-2.

The idiomatic fix: use `None` as the default sentinel, and create a fresh mutable object inside the function body each call.

### Why it matters for SDE-2 interviews

- It's one of the highest-frequency "gotcha" questions across Google/Amazon/Microsoft/Meta-style interviews because it directly tests whether the candidate understands "default args evaluated once" + the reference/mutability model together.
- Real production bugs: caching functions, accumulator/builder functions, and config-merging functions are classic places this bug hides silently for a long time because it only manifests when the default path is hit more than once.
- Tests whether a candidate can explain *why*, not just recite "don't do this."

### Code Example

```python
# The bug
def append_item(item, target=[]):  # target=[] created ONCE at def time
    target.append(item)
    return target

print(append_item(1))  # [1]
print(append_item(2))  # [1, 2]  <-- unexpected! same list reused
print(append_item(3))  # [1, 2, 3]

# Proving it's the same object every call
a = append_item("x")
b = append_item("y")
print(a is b)  # True -- same underlying list every time

# The fix
def append_item_fixed(item, target=None):
    if target is None:
        target = []       # fresh list created every call that omits target
    target.append(item)
    return target

print(append_item_fixed(1))  # [1]
print(append_item_fixed(2))  # [2]  <-- correct, independent each time

# Same pitfall applies to dict/set defaults
def add_entry(key, value, store={}):
    store[key] = value
    return store

r1 = add_entry("a", 1)
r2 = add_entry("b", 2)
print(r1)  # {'a': 1, 'b': 2} -- leaked across calls!
print(r1 is r2)  # True

# Proof that defaults are bound once, at def-time, inspectable via __defaults__
print(append_item.__defaults__)  # shows the persistent mutated list, e.g. (['x', 'y'],)

# Immutable defaults are safe (no bug), since they can't be mutated in place
def greet(name, suffix="!"):
    return name + suffix
print(greet("hi"))  # 'hi!' every time, no shared-state issue possible
```

### Common Interview Questions / Gotchas

- "Why does calling a function with a mutable default argument twice produce unexpected accumulated state?"
- "How would you fix a function that uses a mutable default argument?" — sentinel `None` pattern.
- "Are default arguments evaluated at call time or def time?" — def time, exactly once.
- "Is this a bug in Python or intentional design?" — intentional (and arguably useful in niche cases like memoization caches embedded as default args), but a very common footgun for anyone unaware of it.
- "Give an example where someone might *intentionally* rely on this behavior." — using a mutable default as a poor-man's persistent cache across calls (generally discouraged in favor of `functools.lru_cache` or explicit module-level state, but it does exist in older codebases).

### Pitfalls / Common Mistakes

- Writing `def f(x, cache={})` intending a fresh cache per call — instead gets one cache shared across all callers/calls for the lifetime of the function object (which is usually the lifetime of the module/program).
- Not realizing this also applies to any mutable object as a default — not just list/dict, but any custom mutable class instance.
- "Fixing" it by copying the default inside the function without addressing the `None` sentinel pattern properly (e.g., `target = target.copy()` still starts from a shared base value that might have already been mutated by a previous call, which is subtly wrong if the shared default itself was mutated before the `.copy()` call runs).
- Missing this pattern during code review — mutable default arguments are a very common source of hard-to-reproduce, order-dependent bugs (test suites often reveal them because tests run in sequence and share the same function object's defaults).
