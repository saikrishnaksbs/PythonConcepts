# Data Types

Python's built-in data type system is the foundation of nearly every interview question you will
face. This file covers the core numeric, textual, binary, and null types in depth: what they are,
how CPython implements them under the hood, runnable examples, and the specific gotchas that
Google/Amazon/Microsoft/Atlassian/Uber/Flipkart/Walmart/Adobe interviewers love to probe.

---

## int

### Explanation

Python's `int` is an arbitrary-precision (bignum) integer type. Unlike C/Java `int`/`long`, which
are fixed-width (32/64-bit) and overflow silently or wrap around, Python integers grow
automatically to hold values of any size, limited only by available memory.

```python
x = 2 ** 1000  # a 302-digit number, no overflow, no special type needed
print(x)
```

### Internals

- CPython implements `int` as a variable-length array of "digits" in base 2**30 (on 64-bit
  builds) — see `longobject.h`/`longintrepr.h`. Each `PyLongObject` stores a sign and an array of
  30-bit limbs.
- Small integers, and integer arithmetic in general, are heap-allocated `PyLongObject`s (except
  for the small-int cache described below), which is why integer math in Python is slower than in
  statically typed, fixed-width languages.
- **Integer caching**: CPython pre-allocates and caches integer objects in the range **-5 to 256**
  at startup. Any reference to an int in this range reuses the same object rather than allocating
  a new one. This is a CPython implementation detail, not part of the language spec (do not rely
  on it in production code).
- Division: `/` always produces a `float` (true division), `//` is floor division and returns an
  `int` when both operands are `int`, `%` is modulo (result has the sign of the divisor, unlike
  C).
- `int` supports arbitrary bases via `int(str, base)` and introspection via `.bit_length()`,
  `.bit_count()` (3.10+), `.to_bytes()` / `int.from_bytes()`.

### Code Example

```python
a = 10
b = 3
print(a / b)    # 3.3333333333333335 (true division -> float)
print(a // b)   # 3   (floor division)
print(a % b)    # 1   (modulo)
print(-7 // 2)  # -4  (floors toward negative infinity, not toward zero)
print(-7 % 2)   # 1   (result takes sign of divisor)

big = 123456789012345678901234567890 * 2
print(big)  # no overflow

print((300).bit_length())      # 9
print((5).to_bytes(2, "big"))  # b'\x00\x05'
print(int.from_bytes(b"\x00\x05", "big"))  # 5

print(int("1010", 2))   # 10  (parse binary string)
print(int("ff", 16))    # 255 (parse hex string)
```

### Interview Questions / Gotchas

- **Integer caching (-5 to 256)**: Classic FAANG identity-vs-equality trap.
  ```python
  a = 100
  b = 100
  print(a is b)  # True  -- both point to the cached int object

  c = 1000
  d = 1000
  print(c is d)  # False (usually) -- outside the cache range, separate objects
  # (CPython may sometimes fold same-literal constants within one code object
  # via "constant folding" at compile time, which can make this True inside a
  # single function/module — never rely on `is` for int comparisons.)
  ```
  The correct interview answer: **never use `is` to compare integer values** — always use `==`.
  `is` checks object identity, `==` checks value equality.
- **`-7 // 2` is `-4`, not `-3`** — Python floor division always rounds toward negative infinity.
  This trips up candidates who assume truncation like C.
- **Integer overflow does not exist** in pure Python `int`, but *does* exist in NumPy fixed-width
  types (`numpy.int32`, etc.) — a common Amazon/Flipkart follow-up to test if you know the
  difference.
- Why is Python integer arithmetic slower than C? Because of heap allocation and the "digit array"
  representation for arbitrary precision — no native machine-word fast path (though CPython does
  have internal small-int optimizations).

### Pitfalls

- Assuming `is` on ints outside -5..256 behaves the same as inside — it usually doesn't, and it's
  an implementation detail that could change between CPython versions.
- Forgetting `%` follows the divisor's sign, causing bugs when porting modulo logic from C/Java.
- Using floats for money/counters where big integers or `Decimal` would avoid precision loss.

---

## float

### Explanation

Python's `float` is a double-precision (64-bit) IEEE-754 binary floating-point number — the same
representation as a C `double` or Java `double`. It is *not* arbitrary precision and *cannot*
exactly represent most decimal fractions.

### Internals: IEEE-754 and precision

IEEE-754 double precision uses 1 sign bit, 11 exponent bits, and 52 mantissa (fraction) bits,
giving roughly 15-17 significant decimal digits of precision. Fractions whose denominator is not a
power of 2 (like `0.1` = 1/10) cannot be represented exactly in binary, so they are stored as the
*closest representable double*, leading to tiny rounding errors that compound in arithmetic.

```python
print(0.1 + 0.2)          # 0.30000000000000004
print(0.1 + 0.2 == 0.3)   # False
```

### Code Example

```python
import math
import sys

print(0.1 + 0.2)                     # 0.30000000000000004
print(round(0.1 + 0.2, 10) == 0.3)   # True (rounding masks the error)
print(math.isclose(0.1 + 0.2, 0.3))  # True (proper way to compare floats)
print(math.isclose(0.1 + 0.2, 0.3, rel_tol=1e-9, abs_tol=0.0))  # True

print(sys.float_info.epsilon)  # smallest diff representable near 1.0, ~2.22e-16
print(sys.float_info.max)      # ~1.7976931348623157e+308
print(sys.float_info.min)      # smallest positive normalized float

print(float("inf"), float("-inf"), float("nan"))
print(float("nan") == float("nan"))  # False -- NaN is never equal to anything, even itself
print(math.isnan(float("nan")))      # True -- correct way to test for NaN

# Special values behave per IEEE-754
print(1.0 / 0.0 if False else "avoid ZeroDivisionError")
try:
    1.0 / 0.0
except ZeroDivisionError:
    print("Python raises ZeroDivisionError, unlike C which gives inf")
```

### Interview Questions / Gotchas

- **"Why does `0.1 + 0.2 != 0.3`?"** — THE classic float question at every company on this list.
  Answer: binary floating point cannot exactly represent 0.1 or 0.2 (they're repeating fractions
  in base 2), so both are stored as the nearest representable double, and their sum's rounding
  error doesn't match 0.3's rounding error. Solution: use `math.isclose()`, round to a fixed
  number of decimals, or use `decimal.Decimal` for exact decimal arithmetic (e.g. money).
- **`float('nan') == float('nan')` is `False`** — NaN never compares equal to anything per
  IEEE-754, including itself. Use `math.isnan(x)` instead of `x == float('nan')`.
- Unlike C, `1.0 / 0.0` raises `ZeroDivisionError` in Python rather than returning `inf` (though
  `float('inf') - float('inf')` does give `nan`, and `1.0 / float('inf')` gives `0.0`).
- Sorting/comparing floats after accumulation (e.g., summing many small floats) can silently
  accumulate error — interviewers sometimes ask you to design a running-average or financial
  calculation to test if you know to use `Decimal` or integer cents.
- `float` has a fixed ~15-17 significant digit precision — asking a candidate to represent very
  large exact integers as float (e.g. `float(2**60)`) exposes precision loss silently.

### Pitfalls

- Using `==` to compare computed floats.
- Assuming decimal literals are stored exactly (`0.1` is really
  `0.1000000000000000055511151231257827021181583404541015625` internally).
- Forgetting `Decimal` needs to be constructed from strings (`Decimal("0.1")`), not floats
  (`Decimal(0.1)` reproduces the float's imprecision).

---

## complex

### Explanation

Python has a built-in `complex` type for complex numbers, written as `a + bj` (Python uses `j` for
the imaginary unit, following electrical-engineering convention, not `i`). Each component
(`.real`, `.imag`) is stored as a `float`.

### Use cases / why it matters

Complex numbers show up in signal processing (FFTs), scientific computing, electrical engineering
simulations, and some graphics/geometry algorithms (e.g., representing 2D rotations/points as
complex numbers simplifies math). Interviewers rarely deep-dive complex numbers at SDE-2 level,
but they do expect you to know it's a first-class built-in type and not confuse it with `bool`
truthiness or think you need a library for basic complex arithmetic.

### Code Example

```python
z1 = 3 + 4j
z2 = complex(1, -2)

print(z1.real, z1.imag)     # 3.0 4.0  (always stored as floats)
print(z1 + z2)               # (4+2j)
print(z1 * z2)               # (11-2j)
print(abs(z1))                # 5.0  -- magnitude: sqrt(3**2 + 4**2)
print(z1.conjugate())          # (3-4j)

import cmath
print(cmath.phase(z1))        # 0.9272952180016122 radians
print(cmath.polar(z1))        # (5.0, 0.9272952180016122)  -> (r, theta)
print(cmath.sqrt(-1))          # 1j  -- math.sqrt(-1) would raise ValueError
```

### Interview Questions / Gotchas

- `math.sqrt(-1)` raises `ValueError: math domain error`, but `cmath.sqrt(-1)` returns `1j` —
  know which module to use.
- `complex` numbers are **unordered** — `<`/`>` raise `TypeError`, since there is no natural total
  order on the complex plane. `==` and `!=` work.
- `abs()` on a complex number gives the magnitude (Euclidean norm), not the "absolute value" in
  the real-number sense.
- `1j * 1j == -1` (as a complex number `(-1+0j)`), demonstrating `j**2 = -1`.

### Pitfalls

- Trying to sort or compare complex numbers with `<`/`>`.
- Confusing `j` with a variable name (`j = 5; z = 3 + j` is valid syntax but doesn't create a
  complex number the way `3 + 5j` does — `3 + j` is just integer addition here).

---

## bool

### Explanation

`bool` is a subclass of `int` with exactly two instances: `True` and `False`, which behave as `1`
and `0` respectively in arithmetic contexts.

### Internals: bool as an int subclass

```python
print(issubclass(bool, int))  # True
print(isinstance(True, int))  # True
print(True == 1)               # True
print(True is 1)               # False -- True and 1 are different objects
print(True + True)             # 2  (bool arithmetic promotes to int)
print(type(True + True))       # <class 'int'>
```

This design choice dates back to Python 2.3 when `bool` was retrofitted onto the language;
`True`/`False` needed to remain backward compatible with code that used `0`/`1` as booleans.

### Code Example

```python
print(bool(0), bool(1), bool(-1))         # False True True
print(bool(""), bool("a"))                 # False True
print(bool([]), bool([0]))                 # False True
print(bool(None))                            # False
print(bool({}), bool({"a": 1}))              # False True

# Truthiness of custom objects: controlled by __bool__ or __len__
class Empty:
    def __len__(self):
        return 0

print(bool(Empty()))  # False -- falls back to __len__ when __bool__ isn't defined

# bool in arithmetic / indexing
values = [10, 20]
flag = True
print(values[flag])   # 20 -- True acts as index 1
print(sum([True, True, False, True]))  # 3 -- counts True values directly
```

### Interview Questions / Gotchas

- **"Is `bool(-1)` True or False?"** — `True`. Only `0` (and `0.0`, `0j`, empty containers, `None`,
  empty strings) are falsy; *every* nonzero number, including negative numbers, is truthy. This
  is a very common "gotcha" question at Amazon/Microsoft interviews.
- `True + True == 2` and `type(True + True) is int` — booleans participate fully in integer
  arithmetic because `bool` subclasses `int`.
- `True == 1` is `True`, but `True is 1` is `False` — value equality vs identity again.
- `isinstance(True, int)` is `True`, which can break naive type-checking code that does
  `if isinstance(x, int) and not isinstance(x, bool):` — this explicit dual-check is a known
  idiom interviewers expect you to produce when asked "how do you distinguish an int input from a
  bool input in a type-checked function?"
- `sum([True, False, True, True])` is a legitimate/idiomatic way to count `True` values in a list
  because bools sum as ints — good to know for "count elements matching a condition" questions.

### Pitfalls

- Writing `if isinstance(x, int):` when you actually mean "is this an int and not a bool" (since
  `bool` passes `isinstance(x, int)`).
- Assuming `bool(-1)` is `False` because "-1 is falsy" in some other languages — it is not in
  Python.
- Using `is True` / `is False` for comparisons in general code (works because `True`/`False` are
  singletons, but `== True` is usually preferred/more idiomatic; PEP 8 actually recommends against
  both — just use the value directly: `if flag:` not `if flag == True:`).

---

## str

### Explanation

`str` represents an immutable sequence of **Unicode code points** (not bytes). Since Python 3,
all `str` objects are Unicode by default — there is a hard, explicit split between text (`str`)
and binary data (`bytes`), unlike Python 2 where `str` was a byte string.

### Internals: immutability and the flexible string representation

- `str` objects are immutable: once created, their contents cannot change in place. Every
  "modifying" string operation (`+`, `.upper()`, `.replace()`, slicing, etc.) creates and returns a
  **new** `str` object.
- Since PEP 393 (Python 3.3+), CPython uses a **flexible string representation**: each string is
  internally stored using the smallest fixed-width encoding that fits all its code points — 1 byte
  per char (Latin-1) for strings with only code points ≤ 0xFF, 2 bytes per char (UCS-2) if the max
  code point is ≤ 0xFFFF, or 4 bytes per char (UCS-4) if it contains code points beyond the Basic
  Multilingual Plane (e.g. many emoji). This makes indexing O(1) while saving memory for
  ASCII-heavy text, at the cost of needing to re-scan on creation to determine the width.
- **String interning**: CPython automatically interns (caches and reuses) string literals that
  look like identifiers (e.g. `"hello"`, variable names) and short strings created at compile
  time, for memory and comparison efficiency. You can force interning manually with
  `sys.intern()`.
- A `str`'s length (`len()`) is the number of Unicode **code points**, not bytes, not
  grapheme clusters, and not necessarily the number of "visible characters" a human would count
  (combining characters, emoji with modifiers, etc. can be multiple code points that render as one
  glyph).

### Code Example

```python
s = "hello"
s2 = s.upper()
print(s, s2)          # 'hello' 'HELLO' -- original unchanged (immutability)
print(s is s2)         # False -- new object created

# Interning
a = "hello"
b = "hello"
print(a is b)          # True -- literal strings are typically interned

c = "hello world!"
d = "hello world!"
print(c is d)          # often False -- strings with spaces/punctuation aren't always interned
print(c == d)           # True -- always compare strings with ==

# Unicode code points
text = "café"
print(len(text))        # 4 -- 4 code points (c, a, f, é)
print(text.encode("utf-8"))  # b'caf\xc3\xa9' -- 5 bytes, since é is 2 bytes in UTF-8

emoji = "👍"
print(len(emoji))        # 1 -- one code point (U+1F44D)
print(len(emoji.encode("utf-8")))  # 4 bytes in UTF-8

# String formatting
name, age = "Sai", 30
print(f"{name} is {age}")            # f-strings (preferred, fastest)
print("{} is {}".format(name, age))  # str.format
print("%s is %d" % (name, age))       # old-style % formatting

# Common methods
print("  padded  ".strip())     # 'padded'
print("a,b,,c".split(","))       # ['a', 'b', '', 'c']
print("-".join(["a", "b", "c"])) # 'a-b-c'
print("Hello"[::-1])              # 'olleH' -- reverse via slicing
```

### Interview Questions / Gotchas

- **"Why are strings immutable in Python?"** — Enables safe hashing (so strings can be dict keys /
  set members), safe sharing/interning across references without defensive copying, and thread
  safety.
- **String concatenation in a loop is O(n^2)**: `result = ""; for x in items: result += x`
  reallocates a new string object each iteration. Prefer `"".join(items)`, which is O(n). This is
  a very common efficiency question at Amazon/Uber/Walmart.
  ```python
  # Bad: O(n^2)
  result = ""
  for word in ["a", "b", "c"]:
      result += word
  # Good: O(n)
  result = "".join(["a", "b", "c"])
  ```
- **`is` vs `==` for strings**: `==` compares value, `is` compares identity. Small/simple literal
  strings are often interned so `is` may return `True` by coincidence, but this is *not*
  guaranteed by the language spec — never rely on `is` for string equality.
- **`len()` counts code points, not bytes or visual characters** — a frequent Unicode-handling
  trick question, especially at companies with global user bases (Uber, Flipkart, Adobe).
- Slicing out of range never raises (`"abc"[10:20]` returns `''`), unlike indexing
  (`"abc"[10]` raises `IndexError`) — a common "what happens" gotcha.
- `str.strip()` strips whitespace by default but can strip an arbitrary *set* of characters if
  given an argument (`"xxhixx".strip("x")` -> `'hi'`), which surprises people expecting a prefix
  match instead of a character-set match.

### Pitfalls

- Relying on `is` for string comparisons.
- Building large strings with repeated `+=` instead of `.join()`.
- Assuming 1 character == 1 byte (breaks for any non-ASCII text).
- Forgetting `str.format`/`%`/f-strings all coexist; know f-strings are generally fastest and most
  readable in modern Python (3.6+).

---

## bytes

### Explanation

`bytes` is an **immutable** sequence of integers in range 0-255, representing raw binary data.
It's the type you get from reading a binary file, network sockets, or encoding a `str`.

### Internals

- `bytes` literal syntax: `b"..."`. Each element, when indexed, yields an `int` (0-255), not a
  length-1 `bytes` object — a common surprise for people coming from `str` semantics.
- Encoding text to bytes and decoding bytes to text is an explicit, symmetric operation:
  `str.encode(encoding) -> bytes` and `bytes.decode(encoding) -> str`. UTF-8 is the near-universal
  default.
- Because `bytes` is immutable, operations like concatenation (`b1 + b2`) create new objects,
  same efficiency caveat as `str` concatenation in loops.

### Code Example

```python
data = b"hello"
print(data[0])          # 104 -- an int, not b'h'
print(data[0:1])         # b'h' -- slicing still returns bytes

s = "café"
encoded = s.encode("utf-8")
print(encoded)             # b'caf\xc3\xa9'
decoded = encoded.decode("utf-8")
print(decoded)              # 'café'

try:
    data[0] = 100  # attempt to mutate
except TypeError as e:
    print(f"Error: {e}")  # 'bytes' object does not support item assignment

# Common constructors
print(bytes(5))              # b'\x00\x00\x00\x00\x00' -- 5 zero bytes
print(bytes([65, 66, 67]))    # b'ABC' -- from a list of ints
print(bytes.fromhex("48656c6c6f"))  # b'Hello'
print(data.hex())              # '68656c6c6f'
```

### Interview Questions / Gotchas

- **`bytes` is immutable, `bytearray` is mutable** — this is the headline distinction interviewers
  ask about (see bytearray section for the mutable counterpart and full comparison).
- Indexing a `bytes` object returns an `int`, but slicing returns `bytes` — a frequent "what does
  this print" trick question.
- Encoding/decoding mismatches (e.g., encoding as UTF-8 but decoding as Latin-1, or vice versa)
  cause `UnicodeDecodeError` or silent mojibake — expect a "why did this text get garbled" style
  question, especially at companies dealing with internationalization (Uber, Flipkart, Adobe).
- `bytes` vs `str` confusion in Python 3: You cannot concatenate `bytes` and `str` directly
  (`b"a" + "b"` raises `TypeError`), which is by design to prevent Python-2-style silent encoding
  bugs.

### Pitfalls

- Trying to mutate a `bytes` object in place.
- Forgetting to specify an encoding explicitly (relying on platform default encoding can cause
  cross-platform bugs — always pass `encoding="utf-8"` explicitly).
- Mixing up `.hex()` output with actual byte values.

---

## bytearray

### Explanation

`bytearray` is the **mutable** counterpart to `bytes` — a resizable sequence of integers in the
range 0-255. It supports the same indexing/slicing semantics as `bytes` but allows in-place
modification, making it efficient for building up or modifying binary data incrementally (e.g.,
buffers, streaming parsers, in-place binary transformations).

### Code Example

```python
ba = bytearray(b"hello")
print(ba)             # bytearray(b'hello')

ba[0] = 72             # mutate in place: 'h' (104) -> 'H' (72)
print(ba)              # bytearray(b'Hello')

ba.append(33)           # append a byte (int 0-255)
print(ba)               # bytearray(b'Hello!')

ba.extend(b" world")
print(ba)               # bytearray(b'Hello! world')

# Convert to/from bytes and str
print(bytes(ba))         # b'Hello! world' -- immutable snapshot
print(ba.decode("utf-8")) # 'Hello! world'

# Building a buffer incrementally (efficient, no re-allocation-heavy pattern needed)
buf = bytearray()
for chunk in [b"abc", b"def", b"ghi"]:
    buf.extend(chunk)
print(buf)  # bytearray(b'abcdefghi')

# In-place binary transformation, e.g. XOR "encryption"
key = 0x5A
data = bytearray(b"secret")
for i in range(len(data)):
    data[i] ^= key
print(data)  # scrambled bytes, done in place with no extra allocation
```

### bytes vs bytearray vs memoryview — comparison table

| Feature              | `bytes`            | `bytearray`         | `memoryview`               |
|-----------------------|---------------------|-----------------------|-------------------------------|
| Mutable                | No                   | Yes                     | Depends on underlying buffer  |
| Owns its data           | Yes                  | Yes                     | No (view into another buffer) |
| Copies on slice          | Yes                  | Yes                     | No (zero-copy slice)          |
| Hashable                 | Yes                  | No                       | No                             |
| Typical use               | Immutable binary payloads, dict keys | Mutable buffers, incremental building | Zero-copy access to large binary data |

### Interview Questions / Gotchas

- **"When would you use `bytearray` over `bytes`?"** — Whenever you need to mutate binary data in
  place without the overhead of allocating a new object each time (e.g., streaming/parsing
  network protocols, image/audio buffer manipulation, building a payload byte-by-byte).
- `bytearray` is **not hashable** (because it's mutable) — cannot be used as a dict key or set
  element, unlike `bytes`.
- Appending to a `bytearray` in a loop is efficient (amortized O(1) like `list.append`), unlike
  repeatedly concatenating immutable `bytes` objects with `+=` in a loop (O(n^2)).

### Pitfalls

- Trying to use a `bytearray` as a dict key (`TypeError: unhashable type`).
- Forgetting `bytearray` slicing still returns a *new* `bytearray` (a copy), not a view — for
  zero-copy views you need `memoryview`.

---

## memoryview

### Explanation

`memoryview` provides a **zero-copy** view over the internal data of any object that supports the
**buffer protocol** (e.g. `bytes`, `bytearray`, `array.array`, NumPy arrays). It lets you access
and even slice/modify (if the underlying buffer is mutable) large binary data **without copying
it**, which matters enormously for performance-sensitive or memory-constrained code.

### Internals: the buffer protocol and zero-copy slicing

- The buffer protocol (`PyObject_GetBuffer` / `Py_buffer` in the C API) is a mechanism that lets
  objects expose their raw memory layout directly to other code, avoiding the cost of copying data
  into a new object. `memoryview` is the pure-Python-visible face of this protocol.
- Regular slicing of `bytes`/`bytearray`/`list` **always copies** the sliced portion into a brand
  new object. Slicing a `memoryview`, in contrast, produces **another `memoryview`** that
  references the *same* underlying memory — no bytes are copied. This is why `memoryview` is the
  go-to tool for high-performance binary/network/file I/O code that processes large payloads:
  slicing a multi-megabyte buffer becomes O(1) instead of O(n).
- If the underlying object is mutable (e.g., a `bytearray`), a `memoryview` slice can be used to
  mutate the original buffer in place, since it's a real view, not a copy.

### Code Example

```python
data = bytearray(b"HelloWorld")
mv = memoryview(data)

# Zero-copy slice: no new buffer is allocated
chunk = mv[0:5]
print(bytes(chunk))   # b'Hello'

# Mutating through the memoryview mutates the original bytearray
mv[0] = ord("J")
print(data)  # bytearray(b'JelloWorld')

# Demonstrating zero-copy: mutating a slice view also affects the original
sub = mv[5:10]
sub[0] = ord("w")
print(data)  # bytearray(b'JellowWorld')  -- 'W' became 'w' via the sub-view

# Performance-relevant use case: processing a huge buffer without copying
big_buffer = bytearray(10_000_000)  # 10 MB buffer
view = memoryview(big_buffer)
# Process in 1 MB windows with NO extra memory allocated per window:
chunk_size = 1_000_000
for i in range(0, len(view), chunk_size):
    window = view[i:i + chunk_size]  # zero-copy
    # ... process window in place ...

# memoryview also exposes buffer metadata
print(mv.format)    # 'B' -- unsigned char
print(mv.itemsize)  # 1
print(mv.nbytes)    # 10
print(mv.readonly)  # False (bytearray is mutable; would be True for bytes)

b = b"immutable"
mv_bytes = memoryview(b)
print(mv_bytes.readonly)  # True
try:
    mv_bytes[0] = 65
except TypeError as e:
    print(f"Error: {e}")  # cannot modify read-only memory
```

### Interview Questions / Gotchas

- **"How would you process a large binary file/network payload efficiently in Python?"** — This is
  the canonical `memoryview` interview question at performance-sensitive shops (Uber, Adobe,
  Walmart's high-throughput systems). Answer: use `memoryview` to slice/process chunks without
  copying, especially inside loops, instead of slicing `bytes`/`bytearray` directly (which copies
  every time).
- `memoryview` over a `bytes` object is read-only (`.readonly == True`); over a `bytearray` it's
  writable.
- `memoryview` is not itself the data — it's a *view*. Keeping a `memoryview` alive keeps the
  underlying buffer alive too, and in some cases (e.g. `bytearray.resize()`) you cannot resize the
  underlying mutable buffer while a `memoryview` on it is exported/alive
  (`BufferError: Existing exports of data: object cannot be re-sized`).
- `memoryview` supports multi-dimensional and typed views (via `.cast()`) for interpreting raw
  bytes as, say, an array of 4-byte integers instead of individual bytes — useful when
  interfacing with C extensions, struct-packed data, or NumPy without copying.

### Pitfalls

- Forgetting that a live `memoryview` can prevent resizing the underlying `bytearray`.
- Assuming `memoryview` slicing behaves like `bytes` slicing (copy) — it does not; mutating a
  memoryview slice mutates the original buffer, which can cause surprising aliasing bugs if not
  intended.
- Not releasing a `memoryview` (`.release()`) when done with large data in tight memory
  environments, keeping the backing buffer pinned longer than necessary.

---

## NoneType

### Explanation

`None` is the sole instance of the type `NoneType`, representing the deliberate absence of a
value. It is Python's equivalent of `null`/`nil` in other languages, but with cleaner, singleton
semantics enforced by the language itself.

### Internals: singleton and identity

- `None` is a true singleton: there is exactly **one** `None` object in a running Python process,
  created once by the interpreter at startup. `NoneType` cannot be subclassed or instantiated
  again (`type(None)()` raises `TypeError`).
- Because of this guarantee, `is None` / `is not None` is not just idiomatic, it's the *correct
  and only fully safe* way to check for "no value" — it avoids ambiguity with custom `__eq__`
  implementations on other objects and is faster (identity check is O(1) pointer comparison vs
  potentially invoking `__eq__`).
- `None` is falsy in boolean contexts (`bool(None) is False`), and it is the implicit return value
  of any function that doesn't explicitly `return` something.

### Code Example

```python
x = None
print(x is None)      # True -- the idiomatic, PEP 8-recommended check
print(x == None)       # True too, but not recommended (invokes __eq__, can be overridden)

def f():
    pass  # no explicit return

print(f())  # None -- implicit return

print(type(None))          # <class 'NoneType'>
print(None is None)         # True -- singleton, always the same object
try:
    type(None)()
except TypeError as e:
    print(f"Error: {e}")  # cannot create 'NoneType' instances

# Common pattern: using None as a "not provided" sentinel for mutable default args
def append_item(item, container=None):
    if container is None:       # avoid the mutable-default-argument trap
        container = []
    container.append(item)
    return container

print(append_item(1))  # [1]
print(append_item(2))  # [2]  -- NOT [1, 2], because we didn't reuse a shared default list

# A custom class that overrides __eq__ can break `== None` in surprising ways:
class Weird:
    def __eq__(self, other):
        return True  # always "equal" to everything, including None

w = Weird()
print(w == None)   # True  -- misleading! Weird.__eq__ says it equals anything
print(w is None)    # False -- correctly reveals w is not actually None
```

### Interview Questions / Gotchas

- **"Why should you use `is None` instead of `== None`?"** — `is None` checks identity against the
  unique `NoneType` singleton and cannot be fooled by a class overriding `__eq__`. `== None` calls
  `__eq__`, which any class can override to return `True` even when the object is not `None`
  (shown above), making it an unreliable check. `is None` is also marginally faster since identity
  comparison skips method dispatch. PEP 8 explicitly recommends `is`/`is not` for `None`
  comparisons.
- **Mutable default argument trap**: `def f(x, container=[]):` — the default list is created
  **once** at function definition time and shared across all calls that don't pass `container`
  explicitly, causing state to leak between calls. The idiomatic fix is `container=None` with an
  `if container is None: container = []` guard inside the function body, as shown above. This is
  one of the most commonly asked Python gotcha questions across Google/Amazon/Microsoft.
- Functions with no `return` statement (or a bare `return`) implicitly return `None` — candidates
  are often asked to predict output of a function used in an expression when they forgot a
  `return`.
- `None` cannot be used in most arithmetic/ordering comparisons (`None < 5` raises `TypeError` in
  Python 3, unlike Python 2 where all objects were orderable) — expect a "what does this raise"
  question when sorting a list that might contain `None`.
- `NoneType` cannot be instantiated or subclassed — asked sometimes as a quick sanity/trivia
  check to see if you understand what "singleton enforced by the interpreter" really means versus
  just "singleton by convention."

### Pitfalls

- Using `== None` in code review-sensitive codebases (linters like `flake8`/`pylint` will flag
  `E711: comparison to None should be 'if cond is None:'`).
- Mutable default arguments (`def f(x=[])`) — one of the most notorious real-world Python bugs.
- Assuming `None` sorts predictably with other types — mixed-type comparisons involving `None`
  raise `TypeError` in Python 3.
- Confusing "a function returns `None`" with "a function raised an exception" — they are very
  different failure modes and interviewers often ask you to distinguish them in error-handling
  design questions.

---

## Summary Table

| Type          | Mutable | Hashable | Typical Interview Hook                                      |
|----------------|-----------|-------------|------------------------------------------------------------------|
| `int`           | No          | Yes           | Arbitrary precision, integer caching -5..256, floor division      |
| `float`         | No          | Yes           | IEEE-754, `0.1 + 0.2 != 0.3`, NaN comparisons                       |
| `complex`       | No          | Yes           | `cmath` vs `math`, unorderable                                      |
| `bool`          | No          | Yes           | Subclass of `int`, `bool(-1) is True`, `True + True == 2`           |
| `str`           | No          | Yes           | Immutability, Unicode code points, `.join()` vs `+=`                |
| `bytes`         | No          | Yes           | Binary data, encode/decode, indexing returns int                     |
| `bytearray`     | Yes         | No            | Mutable binary buffer, unhashable                                     |
| `memoryview`    | Depends     | No            | Buffer protocol, zero-copy slicing, performance on large binary data  |
| `NoneType`      | No          | Yes           | Singleton, `is None` vs `== None`, mutable default argument trap       |
