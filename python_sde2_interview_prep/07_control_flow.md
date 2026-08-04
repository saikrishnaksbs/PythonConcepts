# Control Flow

Control flow statements determine the order in which statements execute. Python's
control flow is deliberately minimal compared to languages like C++/Java — there is
no traditional `switch` statement (until `match`-`case` in 3.10), no do-while loop,
and no block-scoping for `if`/`for`/`while` (variables leak into the enclosing scope).
This file covers every control flow construct an SDE-2 candidate is expected to know
cold: `if`, `elif`, `else`, `match`-`case`, `while`, `for`, `break`, `continue`, `pass`,
and the `else` clause on loops.

---

## `if`

### Explanation

`if` evaluates a condition and executes the indented block only when the condition is
truthy. Python does not require parentheses around the condition (unlike C/Java), and
blocks are defined by indentation rather than braces.

```python
age = 20
if age >= 18:
    print("Adult")
```

### Why it matters / internals

Python conditions are not restricted to boolean expressions — **any object** can be
used as a condition because Python evaluates its "truthiness". The rules:

- `False`, `None`, numeric zero (`0`, `0.0`, `0j`), and empty collections
  (`''`, `[]`, `()`, `{}`, `set()`, `range(0)`) are **falsy**.
- Everything else is **truthy** by default.
- Custom objects can override this via `__bool__` (preferred) or `__len__` (fallback —
  if `__bool__` is not defined, Python calls `len(obj)` and treats `0` as falsy).
- If neither `__bool__` nor `__len__` is defined, the object is always truthy.

```python
class Empty:
    def __len__(self):
        return 0

class AlwaysTrue:
    pass

e = Empty()
a = AlwaysTrue()
print(bool(e), bool(a))  # False True
```

Internally, `if` compiles to bytecode using `POP_JUMP_IF_FALSE` (or similar,
version-dependent) — the interpreter calls `PyObject_IsTrue()` on the condition, which
checks `__bool__` then `__len__` then defaults to `True`.

### Code example

```python
def describe(value):
    if isinstance(value, str) and value:
        return f"Non-empty string: {value!r}"
    if value is None:
        return "It's None"
    return "Something else"

print(describe("hi"))
print(describe(""))
print(describe(None))
```

### Interview questions/gotchas

- "Is `if x:` the same as `if x == True:`?" No — `if x:` checks truthiness, while
  `if x == True:` fails for any truthy value that isn't literally `True` (e.g. `if 5 == True` is `False`).
- "What does `if []:` do vs `if [None]:`?" `[]` is falsy (empty), `[None]` is truthy
  (non-empty list, even though its single element is `None`).
- Watch for `is` vs `==` inside conditions — `if x is None` is idiomatic and faster
  than `if x == None` and avoids issues with objects overriding `__eq__`.

### Pitfalls

- Using mutable default truthiness checks like `if x == []:` instead of `if not x:`.
- Confusing `0`/`0.0` falsiness with `"0"` (string `"0"` is truthy — non-empty string).
- Chained comparisons: `if 0 < x < 10:` is valid Python and evaluates as
  `0 < x and x < 10`, not left-to-right like some other languages.

---

## `elif`

### Explanation

`elif` (short for "else if") lets you chain multiple conditions without nested `if`
blocks. Only the first matching branch executes; the rest are skipped.

```python
score = 72
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"
print(grade)  # C
```

### Why it matters / internals

An `if`/`elif`/`elif`/`else` chain is evaluated top-down and short-circuits at the
first true branch — later conditions are never evaluated even if they'd also be true.
This is functionally equivalent to nested `if ... else: if ...` but far more readable.
There is no fallthrough (unlike C `switch` without `break`).

### Code example

```python
def http_status_category(code):
    if 200 <= code < 300:
        return "Success"
    elif 300 <= code < 400:
        return "Redirect"
    elif 400 <= code < 500:
        return "Client Error"
    elif 500 <= code < 600:
        return "Server Error"
    else:
        return "Unknown"

for c in [201, 301, 404, 500, 999]:
    print(c, "->", http_status_category(c))
```

### Interview questions/gotchas

- "Rewrite a long `elif` chain using a dictionary dispatch." Classic SDE-2 refactor
  question — replacing `if/elif` chains keyed on a single value with a `dict` of
  functions (or `match`-`case` in 3.10+) for O(1) dispatch and better readability.
- Order matters: overlapping ranges must be ordered most-specific-first, otherwise a
  broader condition silently swallows narrower ones.

### Pitfalls

- Long `elif` chains checking the same variable are a code smell — often better
  expressed with `match`-`case` or a lookup table.
- Forgetting a final `else` can leave a variable unbound if none of the branches match,
  causing a `NameError`/`UnboundLocalError` later.

---

## `else` (on `if`)

### Explanation

`else` executes when none of the preceding `if`/`elif` conditions were true. It's
optional and always the last clause in the chain.

```python
x = -5
if x > 0:
    print("positive")
else:
    print("non-positive")
```

### Why it matters / internals

`else` on an `if` statement is unconditional relative to the preceding conditions —
it's the "everything else" catch-all. This differs from `else` on loops (`for`/`while`),
covered later, which has completely different, break-dependent semantics — a very
common interview trap.

### Code example

```python
def classify_triangle(a, b, c):
    if a == b == c:
        return "equilateral"
    elif a == b or b == c or a == c:
        return "isosceles"
    else:
        return "scalene"

print(classify_triangle(3, 3, 3))
print(classify_triangle(3, 3, 4))
print(classify_triangle(3, 4, 5))
```

### Interview questions/gotchas

- "Does every `if` need an `else`?" No — omitting `else` is common and fine; the
  interviewer may be probing whether you understand implicit `None` fallthrough for
  functions that don't return in all branches.
- A function with `if ...: return X` and no `else`/final `return` implicitly returns
  `None` on the untaken path — a frequent source of silent bugs.

### Pitfalls

- Assuming `else` is mandatory (it isn't) and adding a useless `else: pass`.
- Conflating `if`-`else` with the different loop-`else` semantics (see below).

---

## `match`-`case`

### Explanation

Introduced in **Python 3.10** ([PEP 634](https://peps.python.org/pep-0634/)),
`match`-`case` provides **structural pattern matching** — matching not just on value
equality but on the *shape* and *structure* of data (sequences, mappings, class
instances with attributes).

```python
def handle(command):
    match command.split():
        case ["go", direction]:
            return f"Moving {direction}"
        case ["look"]:
            return "Looking around"
        case ["take", *items]:
            return f"Taking {items}"
        case _:
            return "Unknown command"

print(handle("go north"))
print(handle("take sword shield"))
print(handle("dance"))
```

### Why it matters / internals

`match`-`case` is **not** a simple `switch`. Each `case` is a *pattern*, and matching
attempts structural decomposition, optionally binding variables:

- **Literal patterns**: `case 200:`, `case "GET":`, `case None:` — match by equality
  (well, `is` for singletons like `None`/`True`/`False`, `==` otherwise).
- **Capture patterns**: `case x:` binds whatever value is matched to name `x`
  (always matches — like a variable assignment).
- **Wildcard pattern**: `case _:` matches anything without binding (the catch-all;
  `_` is not treated as a real variable here).
- **Guard clauses**: `case x if x > 0:` — pattern must match *and* the guard
  expression must be truthy.
- **Sequence patterns**: `case [a, b]:`, `case [first, *rest]:` — match lists/tuples
  by structure/length, with star-unpacking.
- **Mapping patterns**: `case {"key": value}:` — matches dicts containing at least
  those keys (extra keys ignored unless `**rest` is used).
- **Class patterns**: `case Point(x=0, y=0):` — matches instances of a class and
  destructures attributes; works with `__match_args__` for positional matching
  (`case Point(0, 0):`).
- **Or patterns**: `case 1 | 2 | 3:` combines multiple literals in one branch.

Internally, `match` is compiled to specialized bytecode (not simply `if`/`elif`) that
uses pattern-matching opcodes; class patterns use `isinstance()` checks plus attribute
lookups, and sequence patterns check `__len__`/iterability. Because capture patterns
always match, **ordering matters** — a bare name pattern placed too early acts like
`_` and swallows everything after it.

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def where_is(point):
    match point:
        case Point(x=0, y=0):
            return "Origin"
        case Point(x=0, y=y):
            return f"Y-axis at {y}"
        case Point(x=x, y=0):
            return f"X-axis at {x}"
        case Point(x=x, y=y) if x == y:
            return "On diagonal"
        case Point():
            return "Somewhere else"
        case _:
            return "Not a point"

for p in [Point(0, 0), Point(0, 5), Point(3, 0), Point(2, 2), Point(1, 2)]:
    print(p, "->", where_is(p))
```

### Code example (dispatch replacing elif chain)

```python
def http_status_category(code):
    match code:
        case c if 200 <= c < 300:
            return "Success"
        case c if 300 <= c < 400:
            return "Redirect"
        case 404:
            return "Not Found"
        case c if 400 <= c < 500:
            return "Client Error"
        case c if 500 <= c < 600:
            return "Server Error"
        case _:
            return "Unknown"

print(http_status_category(404))
print(http_status_category(201))
```

### Interview questions/gotchas

- "Does Python have `switch`?" Trick question — Python had **no** switch statement
  until 3.10's `match`-`case`, and even then it's structural pattern matching, not a
  simple jump table like C's `switch`. Interviewers at Google/Amazon often probe
  whether candidates know this is a *recent* addition (many production codebases still
  target < 3.10 and use dict dispatch or `if`/`elif` instead).
- "When would you prefer `match`-`case` over `if`-`elif`?" When you need structural
  destructuring (unpacking nested data — JSON-like structures, ASTs, command parsers)
  — not just simple value comparisons, where `if`-`elif` or a dict lookup is often
  clearer and more backward-compatible.
- "What's wrong with `case x:` before other cases?" A bare name is a capture pattern
  — it matches *anything* and binds it, silently short-circuiting all subsequent
  cases, unlike constant literals which must match exactly.
- "How do you match a constant stored in a variable?" You must use a **dotted name**
  or value pattern (e.g. `case SomeClass.CONST:` or wrap in a class), because a bare
  `case my_var:` is interpreted as a capture pattern, not a comparison against
  `my_var`'s value. This is a well-known gotcha.
- `match` does **not** fall through between cases (no need for `break`), unlike C's
  `switch`.

### Pitfalls

- Forgetting `case _:` as a catch-all — unmatched values simply fall through with no
  error (no `MatchError`), which can hide bugs silently.
- Using `match` for simple linear numeric comparisons where `if`-`elif` is clearer.
- Assuming `match` is available in Python < 3.10 (it will raise a `SyntaxError`).
- Confusing `case [a, b]` (exact length 2) with `case [a, *b]` (2+ elements, `b` is a list of the rest).

---

## `while`

### Explanation

`while` repeats a block as long as its condition remains truthy, re-evaluating the
condition before every iteration (including the first).

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

### Why it matters / internals

Unlike `for`, `while` has no built-in iteration protocol — you are fully responsible
for updating state that affects the condition, which makes infinite loops a common
bug (forgetting to increment/update). `while True:` combined with `break` is an
idiomatic Python pattern for "loop until some internal condition triggers an exit",
especially useful when the exit condition is easier to check mid-body than up front
(e.g. reading input, retry logic, event loops).

### Code example

```python
import random

def guess_number(target, max_attempts=10):
    attempts = 0
    while attempts < max_attempts:
        guess = random.randint(1, 100)
        attempts += 1
        if guess == target:
            print(f"Found {target} in {attempts} attempts")
            return attempts
    print("Failed to find target")
    return -1

random.seed(42)
guess_number(50)
```

### Interview questions/gotchas

- "How do you implement a retry-with-backoff loop?" Classic `while` use case:

```python
import time

def call_with_retries(fn, max_retries=3, backoff=1):
    attempt = 0
    while attempt < max_retries:
        try:
            return fn()
        except Exception as e:
            attempt += 1
            if attempt == max_retries:
                raise
            time.sleep(backoff * attempt)
```

- "Difference between `while` and `do-while`?" Python has no `do-while` (execute at
  least once, then check). It's emulated with `while True: ...; if not cond: break`.
- Watch for off-by-one bugs when the condition depends on a counter that's mutated
  inside the loop body in multiple places.

### Pitfalls

- Infinite loops from forgetting to update the loop variable, or updating it on a
  branch that's skipped (e.g., inside an `if` that isn't always taken).
- Floating-point loop conditions (`while x != 1.0:`) that never terminate due to
  floating point imprecision — use range-based or epsilon comparisons instead.
- Busy-waiting without any sleep/backoff, wasting CPU.

---

## `for`

### Explanation

`for` iterates over any **iterable** — not just numeric ranges. It binds each yielded
item to the loop variable in turn.

```python
for fruit in ["apple", "banana", "cherry"]:
    print(fruit)
```

### Why it matters / internals

This is one of the most important internals questions for SDE-2 interviews: **`for`
in Python is built entirely on the iterator protocol.** Given `for x in obj:`, Python
effectively does:

```python
_iterator = iter(obj)          # calls obj.__iter__()
while True:
    try:
        x = next(_iterator)    # calls _iterator.__next__()
    except StopIteration:
        break
    # loop body
```

- `iter(obj)` calls `obj.__iter__()`, which must return an iterator object (one that
  implements `__next__`).
- Each call to `next()` calls the iterator's `__next__()`, which returns the next
  value or raises `StopIteration` to signal exhaustion — the `for` loop catches this
  automatically and stops.
- Objects can be *iterable* (have `__iter__`) without being *iterators* themselves
  (lists are iterable but not iterators — `iter([1,2,3])` returns a `list_iterator`).
- Generators (`yield`) and generator expressions automatically satisfy the iterator
  protocol.
- `for` also supports the legacy `__getitem__`-based iteration protocol (indexing
  from 0 until `IndexError`) for backward compatibility, though this is rarely used
  in modern code.

```python
class CountUp:
    """A custom iterable/iterator demonstrating the protocol."""
    def __init__(self, limit):
        self.limit = limit
        self.n = 0

    def __iter__(self):
        return self  # this object is its own iterator

    def __next__(self):
        if self.n >= self.limit:
            raise StopIteration
        self.n += 1
        return self.n

for i in CountUp(5):
    print(i, end=" ")
print()
```

### Code example

```python
# Iterating with enumerate for index+value
names = ["Alice", "Bob", "Carol"]
for idx, name in enumerate(names, start=1):
    print(f"{idx}: {name}")

# Iterating multiple sequences in lockstep with zip
scores = [90, 85, 77]
for name, score in zip(names, scores):
    print(f"{name} scored {score}")

# Dict iteration - keys by default, use .items() for pairs
inventory = {"apples": 10, "bananas": 5}
for item, qty in inventory.items():
    print(item, qty)
```

### Interview questions/gotchas

- "What does `for x in obj` require of `obj`?" It needs `__iter__` (or the fallback
  `__getitem__` protocol). Confusing "iterable" with "iterator" is a very common
  mixup — every iterator is iterable (its `__iter__` returns itself), but not every
  iterable is an iterator.
- "Can you iterate over a generator twice?" No — generators are single-use iterators;
  once exhausted (`StopIteration` raised), a second `for` loop over the same generator
  object does nothing, whereas re-iterating a list works fine each time because
  `iter(list)` produces a fresh iterator.
- "What happens if you modify a list while iterating over it with `for`?" Undefined/
  buggy behavior — items can be skipped or revisited because the iterator tracks a
  positional index into the mutating list. Classic Amazon/Microsoft gotcha:

```python
nums = [1, 2, 3, 4, 5]
for n in nums:
    if n % 2 == 0:
        nums.remove(n)   # BUG: skips elements due to index shifting
print(nums)  # [1, 3, 4, 5] -- 4 wasn't removed even though it's even!
```

  The fix: iterate over a copy (`for n in nums[:]:`) or build a new list via a
  comprehension.

### Pitfalls

- Mutating a collection during iteration (dict: raises `RuntimeError: dictionary
  changed size during iteration`; list: silent skipping as shown above).
- Assuming `for` on a dict iterates in insertion order pre-3.7 (it's guaranteed only
  from 3.7+ as an implementation detail turned language guarantee).
- Reusing an exhausted iterator/generator and getting an empty loop silently.
- Late-binding closures in loops: `[lambda: i for i in range(3)]` — all lambdas
  capture the same variable `i`, so calling all three after the loop gives `2, 2, 2`,
  not `0, 1, 2`. Fix with a default argument: `lambda i=i: i`.

---

## `break`

### Explanation

`break` immediately exits the **innermost** enclosing loop (`for` or `while`),
skipping any remaining iterations and the loop's `else` clause (if any).

```python
for n in range(100):
    if n == 5:
        break
    print(n)
# prints 0 1 2 3 4
```

### Why it matters / internals

`break` only affects the loop it's directly inside — it does **not** propagate out of
nested loops. This is a frequent interview trap: "how do you break out of two nested
loops at once?" Python has no labeled break (unlike Java's `break label;`). Common
solutions:

1. Extract the nested loops into a function and `return`.
2. Use a flag variable checked in the outer loop.
3. Use exceptions for control flow (less idiomatic, but works).
4. Refactor into a single loop over `itertools.product`.

```python
def find_pair(matrix, target):
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == target:
                return i, j          # 'return' escapes both loops cleanly
    return None

matrix = [[1, 2], [3, 4], [5, 6]]
print(find_pair(matrix, 4))  # (1, 1)
```

```python
# Flag-based approach when you can't use a function/return
found = False
for i, row in enumerate(matrix):
    for val in row:
        if val == 4:
            found = True
            break
    if found:
        break
print(i)  # 1
```

### Interview questions/gotchas

- "Does `break` inside a `for` inside a `while` exit the `while` too?" No — only the
  innermost loop (the `for`) is exited; the `while` continues normally.
- "How do you break out of nested loops?" See patterns above — this is a very common
  Amazon/Microsoft coding-round follow-up question.
- Combining `break` with loop `else`: `break` causes the loop's `else` clause to be
  **skipped** (detailed under "else on loops" below) — this is the core mechanism
  behind the for-else "search" idiom.

### Pitfalls

- Assuming `break` exits all levels of nested loops (it doesn't — must be handled
  explicitly).
- Using `break` inside a `try/finally` — the `finally` block still runs before the
  loop actually exits.
- Forgetting `break` in a `while True:` loop, causing an infinite loop.

---

## `continue`

### Explanation

`continue` skips the rest of the current iteration's body and jumps directly to the
next iteration's condition check (`while`) or next item fetch (`for`).

```python
for n in range(10):
    if n % 2 != 0:
        continue
    print(n)  # prints even numbers 0 2 4 6 8
```

### Why it matters / internals

`continue`, like `break`, only affects the innermost loop. Unlike `break`, `continue`
does **not** prevent the loop's `else` clause from running — the loop still needs to
complete normally (i.e., no `break` anywhere) for `else` to fire.

`continue` is often used to keep loop bodies flat by handling "skip" conditions early
(a "guard clause" pattern), avoiding deep nesting:

```python
# Instead of nesting:
for item in items:
    if is_valid(item):
        if not is_duplicate(item):
            process(item)

# Prefer early-exit with continue:
for item in items:
    if not is_valid(item):
        continue
    if is_duplicate(item):
        continue
    process(item)
```

### Code example

```python
def sum_positive_even(numbers):
    total = 0
    for n in numbers:
        if n <= 0:
            continue
        if n % 2 != 0:
            continue
        total += n
    return total

print(sum_positive_even([-2, 3, 4, -5, 6, 7, 8]))  # 18
```

### Interview questions/gotchas

- "Does `continue` in a `while` loop risk an infinite loop?" Yes, if the update
  statement (e.g., `i += 1`) sits *after* the `continue`'s trigger condition and
  never executes on that path:

```python
i = 0
while i < 5:
    if i == 2:
        continue   # BUG: 'i' never increments when i==2 -> infinite loop
    print(i)
    i += 1
```

  Fix: increment before `continue`, or restructure the update to always run
  (e.g., using a `for` loop over `range` instead, which auto-advances).
- "Does `continue` skip the loop's `else`?" No — only `break` skips `else`;
  `continue` just skips to the next iteration and the loop can still complete
  normally afterward.

### Pitfalls

- Placing state-mutation (counters, iterators) after a `continue` that can bypass it,
  causing infinite loops in `while`.
- Overusing `continue` to the point of making control flow hard to follow — for
  simple cases a single `if` without `continue` is often clearer.

---

## `pass`

### Explanation

`pass` is a null operation — a statement that does nothing. It exists purely to
satisfy Python's syntactic requirement that blocks (after `:`) cannot be empty.

```python
def not_implemented_yet():
    pass

class Marker:
    pass

if condition_not_ready_yet:
    pass
else:
    do_something()
```

### Why it matters / internals

`pass` is a true no-op at the bytecode level (compiles to nothing meaningful, unlike
`...` which pushes the `Ellipsis` singleton object onto the stack, or a docstring
which is stored as `__doc__`). It's commonly used as a placeholder:

- Stubbing out functions/classes/loop bodies during development (TDD skeletons).
- Explicitly no-op branches in conditionals for clarity.
- Empty exception handlers (though usually an anti-pattern unless deliberate):

```python
try:
    risky_operation()
except SomeExpectedError:
    pass  # intentionally ignore this specific, expected error
```

### `pass` vs `...` (Ellipsis)

Both are valid placeholders and are functionally interchangeable as "do nothing"
statements — but there are conventional/semantic differences interviewers may probe:

| | `pass` | `...` (Ellipsis) |
|---|---|---|
| Type | Statement (keyword) | Expression (an object, `Ellipsis` singleton) |
| Common use | Stub with **no** return value needed | Stub in **type stub files (`.pyi`)**, abstract method bodies, or as a slice placeholder (`arr[..., 0]`) |
| Can be assigned to a variable | No | Yes — `x = ...` is valid |
| Readability convention | "Nothing happens here" | "Implementation intentionally omitted" (common in typing stubs / protocols) |

```python
from typing import Protocol

class Comparable(Protocol):
    def __lt__(self, other) -> bool: ...   # Ellipsis - idiomatic in stubs/protocols

def todo_function():
    pass   # pass - idiomatic for "nothing happens" / TODO stub
```

### Code example

```python
def process(record):
    if record.get("deleted"):
        pass  # explicitly: do nothing for deleted records
    elif record.get("archived"):
        archive_handler(record)
    else:
        default_handler(record)

def archive_handler(r): print("archiving", r)
def default_handler(r): print("processing", r)

process({"deleted": True})
process({"archived": True})
```

### Interview questions/gotchas

- "What's the difference between `pass`, `continue`, and an empty function body?"
  `pass` is a no-op placeholder anywhere a statement is syntactically required;
  `continue` actively skips to the next loop iteration (only valid inside loops);
  they solve different problems and are not interchangeable.
- "Why doesn't Python allow empty blocks?" Because indentation *is* the block
  delimiter — an empty block after `:` would be ambiguous/unparsable, so `pass`
  exists to make "no operation" explicit and unambiguous.
- "Is `pass` needed in a function with only a docstring?" No — a docstring alone
  is a valid (non-empty) statement, so `def f(): """TODO"""` doesn't need `pass`.

### Pitfalls

- Leaving `pass` in exception handlers permanently, silently swallowing real errors
  in production (should at least log).
- Using `pass` where `continue` or `return` was actually intended, causing dead code
  paths that fall through to further statements.

---

## `else` on loops (`for-else` / `while-else`)

### Explanation

Both `for` and `while` loops accept an optional `else` clause. This is one of
Python's most misunderstood features because the name "`else`" is misleading for
newcomers coming from C-family languages.

**Semantics: the `else` block runs if and only if the loop completes normally —
i.e., it was NOT terminated early by a `break`.** It runs even if the loop body
executed zero times (e.g., `for x in []:` — the loop "completes" trivially).

```python
for n in range(5):
    print(n)
else:
    print("Loop completed without break")
# All 5 numbers print, then "Loop completed without break"

for n in range(5):
    if n == 3:
        break
    print(n)
else:
    print("This will NOT print, because we broke out")
```

### Why it matters / internals

A better mental model: think of loop-`else` as "**no-break**" rather than "else".
It's syntactic sugar that eliminates a common manual bookkeeping pattern (a
`found`/`broke` flag):

```python
# Without for-else (manual flag):
found = False
for item in items:
    if item == target:
        found = True
        break
if not found:
    handle_not_found()

# With for-else (idiomatic):
for item in items:
    if item == target:
        break
else:
    handle_not_found()
```

This "search" idiom — loop to find something, `break` when found, `else` to handle
the "not found" case — is the single most common legitimate use of loop-`else`, and
is a favorite Google/Amazon interview question ("what does `for-else` do, and when
would you use it?").

Internally, the interpreter tracks whether a `break` bytecode instruction was hit;
if the loop's iterator is exhausted (`StopIteration`) or the `while` condition
becomes false *without* a `break` ever executing, control falls into the `else`
block before proceeding to the code after the whole `for`/`else` construct.
`continue` and normal exceptions do not suppress the `else` — only `break` does.
(An uncaught exception propagates out and skips `else` too, but that's just normal
exception propagation, not special loop-`else` behavior.)

`while-else` behaves identically: `else` runs if the `while` condition becomes falsy
naturally, and is skipped if `break` fires.

```python
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            break
        i += 1
    else:
        return True   # loop finished without finding a divisor
    return False

for x in [2, 3, 4, 17, 18, 97]:
    print(x, is_prime(x))
```

### Code example

```python
def find_first_prime_factor(n):
    for candidate in range(2, int(n ** 0.5) + 1):
        if n % candidate == 0:
            print(f"Smallest prime factor of {n} is {candidate}")
            break
    else:
        print(f"{n} is prime (or 1)")

find_first_prime_factor(28)   # 2
find_first_prime_factor(29)   # prime
```

### Interview questions/gotchas

- "What does the `else` in a `for-else` actually mean?" Runs only when the loop is
  **not** terminated via `break`. This is the single highest-value gotcha question
  for this topic across Google/Amazon/Microsoft/Flipkart/Walmart interviews — many
  candidates guess (wrongly) that it behaves like `if-else` or runs "if the loop
  didn't execute".
- "Does `for-else` run if the loop body never executes (empty iterable)?" Yes —
  `for x in []: ... else: print("ran")` still prints "ran", since there was no
  `break`.
- "Does `continue` affect whether `else` runs?" No, only `break` does.
- "What if the loop exits via `return` inside a function?" `return` exits the whole
  function immediately, so neither the rest of the loop nor the `else` clause runs
  — but that's just normal function-return behavior, not loop-`else`-specific.
- "Rewrite a for-else without using else." Interviewers sometimes ask this to confirm
  you understand the flag-based equivalent shown above — good for demonstrating you
  understand what the sugar replaces.
- Real-world relevance: linear search, validating "all items satisfy X" patterns,
  and matrix/nested search early-exit combined with the outer-flag `break` pattern
  described in the `break` section.

### Pitfalls

- The most common pitfall: assuming `else` runs only when the loop *doesn't* execute
  or *fails* somehow — it's precisely the opposite intuition from `try-except-else`
  (which is again a different, unrelated `else` semantic for exceptions).
- Nesting confusion: an inner loop's `else` binds to the inner loop, not the outer
  one — indentation determines which loop the `else` belongs to, just like `if-else`.
- Many engineers avoid `for-else` entirely in production code because the semantics
  are non-obvious to readers unfamiliar with Python; it's common in interviews but
  many style guides (e.g., Google's) discourage it for readability, preferring an
  explicit flag or a `return`/helper-function approach instead. Knowing this
  trade-off is itself a good talking point in an SDE-2 interview.

---

## Summary table

| Construct | Purpose | Key gotcha |
|---|---|---|
| `if` | Conditional branch | Truthy/falsy evaluation via `__bool__`/`__len__` |
| `elif` | Chained conditions | No fallthrough; order matters for overlapping ranges |
| `else` (if) | Catch-all branch | Optional; omission can cause unbound variables |
| `match`-`case` | Structural pattern matching (3.10+) | Bare `case x:` always matches (capture, not compare) |
| `while` | Condition-driven loop | No native do-while; risk of infinite loops |
| `for` | Iterator-protocol-driven loop | Built on `__iter__`/`__next__`; mutating while iterating is buggy |
| `break` | Exit innermost loop | Doesn't escape nested/outer loops; skips loop `else` |
| `continue` | Skip to next iteration | Does not skip loop `else`; can cause infinite loops in `while` |
| `pass` | No-op placeholder | Different from `...` (Ellipsis), which is a real object |
| `else` (loop) | Runs if loop completes without `break` | Opposite of common intuition; think "no-break" |
