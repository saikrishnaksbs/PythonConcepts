# Operators

Operators in Python are not just syntax — most of them are backed by dunder
methods that make them overridable, which is exactly why interviewers at
Google/Amazon/Microsoft/Atlassian/Uber/Flipkart/Walmart/Adobe like to probe
this topic. This file covers arithmetic, comparison, logical, assignment,
bitwise, identity, membership, walrus, precedence, and short-circuiting in
depth, with runnable examples and the gotchas that come up in SDE-2 rounds.

---

## Arithmetic Operators

Python supports `+ - * / // % **` for numeric types, and several of them are
overloaded for non-numeric types too (`+` and `*` work on sequences).

| Operator | Meaning | Dunder method |
|---|---|---|
| `+` | Addition | `__add__` / `__radd__` |
| `-` | Subtraction | `__sub__` / `__rsub__` |
| `*` | Multiplication | `__mul__` / `__rmul__` |
| `/` | True division (always float) | `__truediv__` |
| `//` | Floor division | `__floordiv__` |
| `%` | Modulo | `__mod__` |
| `**` | Exponentiation | `__pow__` |
| `-x` | Unary negation | `__neg__` |

### Why it matters / internals

- **`/` vs `//`**: `/` is *true division* and always returns a `float` in
  Python 3 (this was a deliberate break from Python 2, where `/` did integer
  division for two ints). `//` is *floor division* — it rounds **toward
  negative infinity**, not toward zero. This trips people up with negative
  numbers: `-7 // 2` is `-4`, not `-3`.
- **`%` follows floor division**: the identity `a == (a // b) * b + (a % b)`
  always holds, so the sign of `a % b` matches the sign of `b`, not of `a`.
  This differs from C/Java, where `%` takes the sign of the dividend.
- **Operator overloading**: `a + b` desugars to `type(a).__add__(a, b)`; if
  that returns `NotImplemented`, Python falls back to
  `type(b).__radd__(b, a)`. This is how libraries like NumPy/Pandas make
  `+` work on custom objects, and it's a very common "implement a class that
  supports arithmetic" interview exercise.
- `**` binds tighter than unary minus on its left operand: `-2 ** 2` is
  `-4`, not `4`, because it parses as `-(2 ** 2)`.

```python
print(7 / 2)     # 3.5   -> true division, always float
print(7 // 2)    # 3     -> floor division
print(-7 // 2)   # -4    -> rounds toward -infinity, not toward 0
print(-7 % 2)    # 1     -> result takes the sign of the divisor
print(7 % -2)    # -1
print(-2 ** 2)   # -4    -> unary minus has lower precedence than **
print(2 ** 3 ** 2)  # 512 -> ** is right-associative: 2 ** (3 ** 2)

class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return NotImplemented
    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

print(Vector(1, 2) + Vector(3, 4))  # Vector(4, 6)
```

### Common interview questions / gotchas

- "Why is `0.1 + 0.2 != 0.3`?" — floating point binary representation, not
  an operator issue per se, but always comes up under arithmetic.
- "Implement `__add__` and `__radd__` for a custom Money/Vector class."
- "What does `divmod(a, b)` return?" — a tuple `(a // b, a % b)` computed
  together, useful in coding-round math problems.
- "Why does `int / int` return a float in Python 3 but not Python 2?"

### Pitfalls

- Assuming `//` truncates toward zero like C's integer division — it floors.
- Forgetting `**` is right-associative.
- Mixing `int` and `float` silently promotes to `float`, which can hide
  precision bugs in financial code (use `decimal.Decimal` there instead).

---

## Comparison Operators

`== != < > <= >=` compare values. Each maps to a dunder method:
`__eq__`, `__ne__`, `__lt__`, `__gt__`, `__le__`, `__ge__`.

### Why it matters / internals

- `==` checks **value equality**, not identity. For custom classes without
  `__eq__` defined, it falls back to `object.__eq__`, which compares
  identity (same as `is`) — a frequent source of bugs ("why doesn't my
  object equal an identical one?").
- **Chained comparisons**: `a < b < c` is **not** `(a < b) < c`. Python
  evaluates it as `a < b and b < c`, but critically, `b` is only evaluated
  **once**. This is both a convenience and a gotcha if `b` has side effects.
- Rich comparison methods let classes fully customize ordering; `functools
  .total_ordering` can fill in the rest from just `__eq__` and one of
  `__lt__`/`__le__`/`__gt__`/`__ge__`.
- `sorted()`, `min()`, `max()`, and `list.sort()` all rely on `__lt__` under
  the hood (Python only uses `<` internally for sorting via TimSort).

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __eq__(self, other):
        return isinstance(other, Point) and (self.x, self.y) == (other.x, other.y)
    def __repr__(self):
        return f"Point({self.x},{self.y})"

print(Point(1, 2) == Point(1, 2))  # True, custom __eq__

# chained comparison, b evaluated once
def noisy():
    print("evaluating b")
    return 5

a, c = 1, 10
print(1 < noisy() < c)  # "evaluating b" printed once, then True

# comparing across types
print(1 == 1.0)      # True, numeric tower compares by value
print(1 == "1")       # False, no exception, just not equal
print([1, 2] == [1, 2])  # True, list __eq__ compares elementwise
```

### Common interview questions / gotchas

- "Is `a < b < c` equivalent to `(a < b) < c`?" — No; explain chained
  comparison semantics and single evaluation of the middle term.
- "Why does defining `__eq__` without `__hash__` make an object
  unhashable?" — Python sets `__hash__` to `None` automatically when you
  override `__eq__` unless you also define `__hash__`, because mutable
  equality would otherwise break hash invariants in sets/dicts.
- "What's the output of `float('nan') == float('nan')`?" — `False`, NaN is
  never equal to itself (IEEE 754), even though `nan is nan` can be `True`
  if it's the same object.

### Pitfalls

- Overriding `__eq__` without `__hash__` silently makes instances unusable
  as dict keys / set members.
- Using `==` when you actually meant `is` (e.g., checking for a sentinel
  like `None`) can cause subtle bugs if the object defines a custom
  `__eq__` that raises or behaves oddly.
- `NaN != NaN`, so `x == x` is not always a safe "is this valid" check.

---

## Logical Operators

`and`, `or`, `not` implement boolean logic but operate on **truthiness**,
not necessarily `bool` values, and `and`/`or` return one of their operands
rather than `True`/`False`.

### Why it matters / internals

- Every object has a truth value via `__bool__` (or `__len__` as a
  fallback — empty containers are falsy). `and`/`or` use this truthiness to
  decide which operand to return.
- `not` always returns an actual `bool` (`True`/`False`), unlike `and`/`or`.
- `and`/`or` are covered in more depth under **Short-Circuit Evaluation**
  below since that's their defining behavior.

```python
print(0 and "unreached")     # 0, falsy short-circuits, right side never evaluated
print(1 and "reached")       # "reached"
print([] or "default")       # "default", [] is falsy
print(not [])                # True
print(not 0)                 # True

class AlwaysFalse:
    def __bool__(self):
        return False

print(bool(AlwaysFalse()))   # False
print(AlwaysFalse() or "fallback")  # "fallback"
```

### Common interview questions / gotchas

- "What does `a and b` return if `a` is truthy?" — it returns `b` itself,
  not `True`.
- "How would you implement a default-value pattern using `or`?" — common
  idiom `value = user_input or default`, but call out the trap when
  `user_input` is a legitimately falsy value like `0` or `""`.
- "Difference between `not` and `!`?" — Python has no `!`; `not` is a
  keyword and lower precedence than comparisons.

### Pitfalls

- `x = user_input or default` silently replaces a legitimate falsy value
  (`0`, `""`, `[]`) with the default — use `if user_input is not None`
  instead when `None` is the only "missing" sentinel.
- Confusing `and`/`or` (return operands) with `&`/`|` (bitwise, return
  actual computed values, no short-circuit) — a very common bug when people
  try to use `and`/`or` element-wise on NumPy/Pandas arrays.

---

## Assignment Operators

Plain `=` and the augmented forms `+= -= *= /= //= %= **= &= |= ^= >>= <<=`.

### Why it matters / internals

- `x += y` is **not** always equivalent to `x = x + y`. For mutable types
  that define `__iadd__` (in-place add), `+=` mutates the object in place
  and rebinds the name to the same object. For immutable types (int, str,
  tuple) there's no `__iadd__`, so it falls back to `__add__` and creates a
  new object.
- This matters enormously when the variable is aliased elsewhere — mutating
  in place affects every reference, while rebinding does not.
- Python also supports chained assignment (`a = b = c = 0`, all bound to
  the same object) and tuple/iterable unpacking assignment
  (`a, b = b, a`, `a, *rest = [1,2,3]`).

```python
# lists define __iadd__ -> in-place mutation
a = [1, 2, 3]
b = a
a += [4]        # calls list.__iadd__, mutates in place
print(a, b)      # [1, 2, 3, 4] [1, 2, 3, 4]  -> b also changed!

# tuples have no __iadd__ -> += falls back to __add__, rebinds
t = (1, 2)
u = t
t += (3,)        # creates a NEW tuple, t rebound, u unchanged
print(t, u)       # (1, 2, 3) (1, 2)

# int is immutable -> += always creates a new int
x = 5
y = x
x += 1
print(x, y)       # 6 5

# swap via tuple unpacking, no temp variable needed
p, q = 1, 2
p, q = q, p
print(p, q)       # 2 1

# starred unpacking
first, *middle, last = [1, 2, 3, 4, 5]
print(first, middle, last)  # 1 [2, 3, 4] 5
```

### Common interview questions / gotchas

- "What's the classic mutable-default-argument bug and how does `+=`
  relate?" — `def f(x, acc=[]): acc += [x]; return acc` mutates the same
  default list across calls because `acc` (a list) uses in-place `+=`.
- "Does `x += 1` inside a function modify the caller's list argument?" —
  depends entirely on whether `x` is a mutable type with `__iadd__`.
- "Explain `a, b = b, a`" — the right-hand side tuple `(b, a)` is fully
  built before any assignment happens, so it works correctly as a swap.

### Pitfalls

- Assuming `+=` behaves identically for all types — always check mutability.
- Using a mutable default argument combined with `+=`/`.append()`, causing
  state to leak across function calls.
- Believing `a = b = []` creates two separate lists — it creates one list
  object referenced by both names.

---

## Bitwise Operators

`& | ^ ~ << >>` operate on the binary representation of integers.

| Operator | Meaning |
|---|---|
| `&` | AND |
| `\|` | OR |
| `^` | XOR |
| `~` | NOT (bitwise complement) |
| `<<` | Left shift |
| `>>` | Right shift |

### Why it matters / internals

- Python integers have **arbitrary precision** and are conceptually stored
  in **two's complement with an infinite sign extension**. This means `~x`
  is always `-x - 1` (flipping all bits of a two's-complement number
  negates it and subtracts one).
- `<<` and `>>` are equivalent to multiplying/dividing by `2**n`, but `>>`
  on negative numbers floors (consistent with `//`), it does not round
  toward zero.
- Bitwise ops on `bool` work because `bool` is a subclass of `int` — `True
  & False` is `0` (an `int`, not a `bool`... actually `bool & bool` returns
  `bool` since Python special-cases it, but `bool` mixed with `int` returns
  `int`).
- Sets in Python actually overload `& | ^ -` for set algebra (intersection,
  union, symmetric difference, difference) — another place these operators
  show up outside pure integer math.

```python
print(5 & 3)     # 0b101 & 0b011 = 0b001 = 1
print(5 | 3)     # 0b111 = 7
print(5 ^ 3)     # 0b110 = 6
print(~5)        # -6   ->  ~x == -x - 1
print(1 << 4)    # 16   ->  1 * 2**4
print(-8 >> 1)   # -4   ->  floors toward -infinity, like //
print(bin(5))     # '0b101'
print(bin(-5))    # '-0b101' (Python shows sign + magnitude in bin(), not raw two's complement)

# sets overload bitwise operators too
s1, s2 = {1, 2, 3}, {2, 3, 4}
print(s1 & s2)   # {2, 3} intersection
print(s1 | s2)   # {1, 2, 3, 4} union
print(s1 ^ s2)   # {1, 4} symmetric difference

# common trick: check if a number is a power of two
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

print(is_power_of_two(16), is_power_of_two(18))  # True False
```

### Common interview questions / gotchas

- "Why is `~5 == -6`?" — explain two's complement: `~x = -(x+1)`.
- "Find the single non-duplicate number in an array where every other
  number appears twice" — classic XOR trick, `functools.reduce(operator.xor, arr)`.
- "Check if a number is a power of two using bit tricks" —
  `n & (n - 1) == 0` (and `n > 0`).
- "Difference between `bin(-5)` output and actual bit storage" — Python's
  `bin()` for negative numbers prints a minus sign plus magnitude, not an
  infinite two's-complement string, since Python ints aren't fixed-width.

### Pitfalls

- Confusing `&`/`|` (bitwise, no short-circuit, work on ints/sets) with
  `and`/`or` (logical, short-circuit, work on truthiness) — using `&`/`|`
  on plain booleans in an `if` condition still works but doesn't
  short-circuit, which matters if operands have side effects.
- Assuming fixed-width integer overflow/wraparound like in C/Java — Python
  ints don't overflow, so bit tricks relying on wraparound need masking
  (e.g., `& 0xFFFFFFFF`) to simulate 32-bit behavior.
- Off-by-one errors with shift amounts, and forgetting `>>` floors instead
  of truncating for negative numbers.

---

## Identity Operators (`is`, `is not`)

`is` compares object **identity** — whether two references point to the
exact same object in memory — using `id(a) == id(b)` semantics.

### Why it matters / internals

- `id()` returns a unique integer for the object's lifetime (in CPython,
  it's the memory address). `is` is essentially `id(a) == id(b)`.
- `is` is **not** the same as `==`. `==` calls `__eq__` and checks value
  equality; `is` never calls any dunder and simply compares identity.
- **Small integer caching**: CPython pre-allocates and interns integers in
  range `[-5, 256]` as singletons, so `a is b` can be `True` for small ints
  purely as an implementation detail — this is **not guaranteed by the
  language spec** and should never be relied on.
- **String interning**: CPython interns some string literals (short,
  identifier-like strings) automatically, so `"abc" is "abc"` may be
  `True`, but this is also an implementation detail, not a guarantee.
- Correct use of `is`: comparing against singletons like `None`, `True`,
  `False`, or sentinel objects — `if x is None:` is the idiomatic and
  PEP 8–recommended form.

```python
a = 256
b = 256
print(a is b)     # True, small int caching (implementation detail)

c = 257
d = 257
print(c is d)     # False (usually) - outside the cached range, two separate objects
# (may be True if computed in the same compile-time constant-folded expression!)

x = [1, 2, 3]
y = [1, 2, 3]
print(x == y)     # True, same values
print(x is y)     # False, different objects

z = x
print(x is z)     # True, same object

print(None is None)  # True, None is a true singleton

s1 = "hello"
s2 = "hello"
print(s1 is s2)    # True, likely interned literal (implementation detail)
s3 = "".join(["h", "e", "l", "l", "o"])
print(s1 is s3)    # False, built at runtime, not interned
```

### Common interview questions / gotchas

- "Why does `a is b` return `True` for small ints but `False` for large
  ones?" — CPython caches ints -5 to 256; explain this is CPython-specific,
  not a language guarantee (Jython/PyPy may differ).
- "When should you use `is` vs `==`?" — `is` for identity/singleton checks
  (`None`, sentinels), `==` for value comparison.
- "What does `if x == None` vs `if x is None` imply?" — `== None` can be
  overridden by a custom `__eq__` and is discouraged; PEP 8 mandates `is
  None`.

### Pitfalls

- Relying on integer/string caching behavior in production code — it is an
  implementation detail of CPython and can differ across Python versions
  or implementations (PyPy, etc.).
- Using `is` to compare mutable containers or custom objects for value
  equality by mistake.
- `x is not None` vs `not x is None` — both work but the former is more
  idiomatic/readable.

---

## Membership Operators (`in`, `not in`)

`in` / `not in` test whether a value exists within a container, calling
`__contains__` if defined.

### Why it matters / internals

- Resolution order: Python first tries `__contains__`; if absent, it falls
  back to iterating via `__iter__`; if that's absent too, it falls back to
  the old-style sequence protocol using `__getitem__` with increasing
  indices until `IndexError`.
- **Time complexity matters a lot here**: `in` on a `list`/`tuple` is
  **O(n)** (linear scan), but `in` on a `set`/`dict` is **O(1)** average
  case (hash lookup). This is one of the most common "why is my code slow"
  interview/real-world questions — converting a list to a set before doing
  repeated membership checks is a textbook optimization.
- For `dict`, `in` checks **keys** by default, not values (`k in d` is
  `k in d.keys()`); use `value in d.values()` explicitly for value checks.
- `in` on a string checks substring containment, not just single-character
  membership.

```python
nums_list = [1, 2, 3, 4, 5]
nums_set = {1, 2, 3, 4, 5}

print(3 in nums_list)   # True, O(n) linear scan
print(3 in nums_set)    # True, O(1) average, hash lookup

d = {"a": 1, "b": 2}
print("a" in d)          # True, checks keys
print(1 in d)             # False, 1 is not a key
print(1 in d.values())    # True

print("ell" in "hello")   # True, substring check

class Range10:
    def __contains__(self, item):
        return 0 <= item < 10

print(5 in Range10())     # True, uses custom __contains__

import timeit
# demonstrating why set membership is preferred for repeated lookups
big_list = list(range(100_000))
big_set = set(big_list)
# 99999 in big_list  -> scans up to 100k elements
# 99999 in big_set   -> single hash lookup
```

### Common interview questions / gotchas

- "Why is checking membership in a list slow for large data, and how do
  you fix it?" — O(n) vs O(1); convert to `set`/`dict` when doing repeated
  lookups.
- "Does `in` on a dict check keys or values?" — keys by default.
- "How would you implement `__contains__` for a custom range-like class?"
- "What's the fallback chain if `__contains__` isn't defined?" —
  `__iter__`, then `__getitem__`.

### Pitfalls

- Using `in` on a `list` inside a loop (`O(n*m)` overall) when a `set`
  would make it `O(n)`.
- Forgetting `in` on a dict tests keys, leading to bugs when someone means
  to check values.
- Confusing `not in` precedence — `x not in y` is a single atomic operator,
  not `not (x in y)` written differently (though semantically equivalent,
  syntactically `not in` is its own token pair).

---

## Walrus Operator (`:=`)

Introduced in **PEP 572** (Python 3.8), the walrus operator performs
**assignment as part of an expression**, letting you bind a name and use
its value in the same expression.

### Why it matters / internals

- Ordinary `=` is a statement, not an expression — it cannot appear inside
  an `if` condition, a comprehension, or any other expression context.
  `:=` fixes this: `(x := expr)` both evaluates `expr`, assigns it to `x`,
  and evaluates to that value.
- **Scoping rule (PEP 572 special case)**: inside a comprehension, a walrus
  target **leaks into the enclosing scope**, unlike a regular `for` loop
  variable in a comprehension (which is scoped to the comprehension
  itself). This is a deliberate exception written into PEP 572 so that
  patterns like capturing the last-tested value work.
- `:=` requires parentheses in most contexts (e.g., bare `x := 5` as a
  statement is a `SyntaxError`; you need `(x := 5)` unless it's the sole
  top-level expression already permitted by the grammar, like directly in
  an `if`/`while` condition).
- Cannot be used to target attributes/subscripts directly the same way
  (`obj.attr := val` and `a[0] := val` are illegal) — walrus only binds
  simple names.

```python
# classic use: avoid calling a function twice
data = [1, 2, 3, 4, 5]

# without walrus - compute len(data) twice conceptually if reused
if (n := len(data)) > 3:
    print(f"list is long, n={n}")

# in a while loop - avoids the "initialize then check" boilerplate
import io
f = io.StringIO("line1\nline2\nline3\n")
while (line := f.readline()):
    print(line.strip())

# in a list comprehension - avoid recomputing an expensive call twice
def expensive(x):
    return x * x

results = [y for x in range(5) if (y := expensive(x)) > 4]
print(results)  # [9, 16]

# scoping leak: the walrus target escapes the comprehension scope
squares = [y := i * i for i in range(3)]
print(y)   # 4  -> y leaked out to the enclosing scope (unlike `i`, which does NOT leak)
# print(i)  # NameError -> the plain `for` loop variable `i` stays scoped to the comprehension
```

### Common interview questions / gotchas

- "What problem does the walrus operator solve?" — avoiding duplicated
  calls/boilerplate like `x = compute(); if x: ...` by inlining assignment
  into the condition.
- "Does the loop variable in a comprehension leak? Does a walrus target?"
  — regular `for` variables in comprehensions do **not** leak (Python 3
  gives comprehensions their own scope); walrus targets **deliberately
  do** leak into the enclosing scope, per PEP 572.
- "Why can't you write `x := 5` as a standalone statement?" — the grammar
  requires it to be parenthesized in most statement contexts to avoid
  ambiguity/readability issues; PEP 572 explicitly disallows unparenthesized
  bare walrus statements.
- "Where is walrus commonly used in real code?" — `while` loops reading
  chunks/lines, filtering-and-transforming in comprehensions, regex match
  reuse: `if (m := pattern.match(s)): use(m.group())`.

### Pitfalls

- Overusing `:=` for cleverness at the cost of readability — code review
  feedback often flags walrus misuse.
- Forgetting that a walrus target inside a comprehension pollutes the
  enclosing namespace, potentially shadowing an existing variable
  unexpectedly.
- Trying to use it in older codebases targeting Python < 3.8, causing a
  `SyntaxError`.

---

## Operator Precedence

When an expression mixes multiple operators, precedence determines
evaluation order (higher rows bind tighter). This table covers the
practically relevant operators from highest to lowest precedence:

| Precedence (high to low) | Operator(s) | Description |
|---|---|---|
| 1 | `()` | Parentheses / grouping |
| 2 | `f(args)`, `x[index]`, `x.attr` | Call, subscription, attribute access |
| 3 | `**` | Exponentiation (right-associative) |
| 4 | `+x`, `-x`, `~x` | Unary plus, minus, bitwise NOT |
| 5 | `* / // %` | Multiplication, division, floor div, modulo |
| 6 | `+ -` | Addition, subtraction (binary) |
| 7 | `<< >>` | Bitwise shifts |
| 8 | `&` | Bitwise AND |
| 9 | `^` | Bitwise XOR |
| 10 | `\|` | Bitwise OR |
| 11 | `in, not in, is, is not, <, <=, >, >=, !=, ==` | Comparisons, membership, identity (all same precedence, chain left-to-right) |
| 12 | `not x` | Boolean NOT |
| 13 | `and` | Boolean AND |
| 14 | `or` | Boolean OR |
| 15 | `x if cond else y` | Conditional (ternary) expression |
| 16 | `lambda` | Lambda expression |
| 17 | `:=` | Assignment expression (walrus) — lowest, evaluated last |

### Why it matters / internals

- `**` is special: it binds tighter than unary minus **on its left
  operand only** — `-2 ** 2 == -4` — but the base itself can be a unary
  expression when parenthesized: `(-2) ** 2 == 4`.
- Comparisons, `in`/`not in`, and `is`/`is not` all share the **same**
  precedence level and chain: `1 < 2 <= 2 < 3` evaluates left to right,
  each pair `and`-ed together implicitly.
- `not` binds tighter than `and`, which binds tighter than `or`. This
  means `not a and b` is `(not a) and b`, not `not (a and b)` — a classic
  gotcha in interview whiteboard questions about boolean expressions.
- `:=` and `lambda` sit at the very bottom, meaning they greedily consume
  everything to their right unless parenthesized.

```python
print(2 + 3 * 4)          # 14, * before +
print((2 + 3) * 4)        # 20, parens override
print(2 ** 3 ** 2)        # 512, ** right-associative: 2 ** (3 ** 2)
print(-2 ** 2)             # -4, unary minus lower than **
print((-2) ** 2)           # 4

print(not True and False)  # False -> (not True) and False = False and False
print(not (True and False))# True  -> explicit grouping changes result

print(1 < 2 < 3)           # True -> (1 < 2) and (2 < 3)
print(1 < 2 and 2 < 3)     # True -> same result, explicit form

print(5 | 2 == 2)          # tricky: == binds tighter than |
                             # -> 5 | (2 == 2) -> 5 | True -> 5 | 1 -> 5

a = True
b = False
print(a or b and False)     # True -> and before or: a or (b and False) -> True or False -> True
```

### Common interview questions / gotchas

- "Evaluate `-2 ** 2` and explain why it's `-4` not `4`." Tests precedence
  of unary minus vs `**`.
- "Evaluate `not a and b or c` for given truth values" — walk through
  `not` > `and` > `or`.
- "Why does `5 | 2 == 2` give `5` and not `True` or something else?" —
  comparisons bind tighter than bitwise `|`, so it's `5 | (2 == 2)`.
- "Is `a == b == c` the same as `(a == b) == c`?" — no, it's a chained
  comparison, `(a == b) and (b == c)`.

### Pitfalls

- Assuming bitwise operators (`& | ^`) have lower precedence than
  comparisons intuitively "feels" — they actually sit right below
  comparisons, causing surprising results when mixed without parens
  (always parenthesize bitwise-with-comparison expressions).
- Misreading `not a == b` as `(not a) == b` — actually `not` has *lower*
  precedence than `==`, so it's `not (a == b)`. Contrast this carefully
  with `not a and b`, where `not` has higher precedence than `and`.
- Relying on memorized precedence in production code instead of using
  parentheses for clarity — most style guides/reviewers prefer explicit
  grouping for anything beyond simple arithmetic.

---

## Short-Circuit Evaluation

`and` and `or` evaluate left to right and **stop as soon as the result is
determined**, skipping evaluation of the remaining operand(s) entirely.

### Why it matters / internals

- `a and b`: if `a` is falsy, `b` is **never evaluated**, and the falsy
  value of `a` is returned. If `a` is truthy, `b` is evaluated and
  returned (whatever `b` is, not necessarily a `bool`).
- `a or b`: if `a` is truthy, `b` is **never evaluated**, and `a` is
  returned. If `a` is falsy, `b` is evaluated and returned.
- This means `and`/`or` return **actual operand values**, not coerced
  booleans — a very common misconception for engineers coming from
  languages where `&&`/`||` always yield `bool`.
- Short-circuiting is essential for guarding against errors: `if x is not
  None and x.value > 0:` — the attribute access only happens if `x is not
  None` is `True`, preventing an `AttributeError`/`NoneType` crash.
- Contrast with `&`/`|` (bitwise/set/dataframe operators) which **always**
  evaluate both operands — no short-circuit — which matters when operands
  have side effects or can raise.

```python
def log_and_return(val, label):
    print(f"evaluating {label}")
    return val

# and short-circuits on first falsy value
result = log_and_return(0, "A") and log_and_return(1, "B")
print(result)   # prints "evaluating A" only, result = 0

# or short-circuits on first truthy value
result = log_and_return(5, "A") or log_and_return(1, "B")
print(result)   # prints "evaluating A" only, result = 5

# guarding against exceptions using short-circuit
x = None
if x is not None and x > 0:   # x > 0 never evaluated, no TypeError
    print("positive")
else:
    print("guarded safely")

# common idiom: default value fallback
name = "" 
display_name = name or "Anonymous"
print(display_name)   # "Anonymous", because "" is falsy

# chained and/or returns the actual last-evaluated operand
print(1 and 2 and 3)     # 3 -> all truthy, returns last operand
print(0 and 2 and 3)     # 0 -> short-circuits immediately
print(0 or "" or "final")# "final" -> skips falsy 0 and "", returns first truthy
print([] or {} or None)  # None -> all falsy, returns the very last operand
```

### Common interview questions / gotchas

- "What does `and`/`or` return — a boolean or the operand?" — the operand
  itself; this is a favorite "predict the output" question.
- "Write a null-safe guard clause using short-circuiting." —
  `if obj is not None and obj.attr:`.
- "Why use `and`/`or` instead of `&`/`|` when both operands might raise?"
  — short-circuiting avoids evaluating (and potentially crashing on) the
  second operand.
- "Predict the output" style questions chaining several `and`/`or` with
  mixed falsy values (`0`, `""`, `None`, `[]`) to test understanding of
  which operand gets returned.

### Pitfalls

- Assuming `and`/`or` always return `True`/`False` like in C/Java — they
  return operands, which can produce unexpected non-boolean values leaking
  into downstream logic.
- Relying on short-circuit order when both operands have side effects you
  actually need to run — use `&`/`|` (no short-circuit, both evaluate) or
  explicit separate statements instead if both side effects are required.
- Using `x or default` when `x` can legitimately be `0`/`""`/`[]` and you
  didn't intend to replace those with the default — prefer `x if x is not
  None else default` in that case.

---

## Summary Cheat Sheet

- `/` always float, `//` floors, `%` sign follows divisor.
- `==` compares value (`__eq__`); `is` compares identity (`id()`).
- Small int caching (`-5..256`) and string interning are CPython
  implementation details — never rely on them for correctness.
- `+=` mutates in place for types with `__iadd__` (list); rebinds for
  immutable types (int, str, tuple).
- `~x == -x - 1` (two's complement); Python ints have no fixed width, so
  no real overflow.
- `in` is O(1) on set/dict, O(n) on list/tuple — convert for repeated
  lookups.
- Walrus `:=` assigns within an expression; its target leaks out of
  comprehension scope (unlike the `for` variable).
- Precedence, high to low (essentials): `**` > unary `+-~` > `* / // %` >
  `+ -` > shifts > `&` > `^` > `|` > comparisons/`in`/`is` > `not` > `and`
  > `or` > ternary > `lambda` > `:=`.
- `and`/`or` short-circuit and return operands, not booleans; `&`/`|`
  always evaluate both sides.
