# Type Conversion

Python is dynamically typed but strongly typed: values have a fixed type at
runtime and the interpreter never silently reinterprets raw bytes across
unrelated types (unlike C's implicit pointer/int coercions). Every conversion
you see in Python — whether the interpreter does it for you or you ask for it
explicitly — goes through well-defined dunder-method protocols. Understanding
those protocols is what separates "I know the syntax" from "I know why it
works," which is exactly what SDE-2 interviewers probe for.

This file covers:

- Implicit Casting
- Explicit Casting
- Numeric Promotion
- Parsing Strings

---

## Implicit Casting

### Explanation

Implicit casting (a.k.a. implicit type coercion) is when Python automatically
converts one type to another *without you calling a conversion function*.
Python is conservative about this — far more conservative than JavaScript or
PHP. It happens in a small number of well-defined situations:

1. **Mixed-type arithmetic between numeric types** — `int + float`, `int +
   complex`, `bool + int`, etc. Python promotes the "narrower" type to the
   "wider" type before the operation (see the Numeric Promotion section for
   the full tower).
2. **Boolean contexts** — `if`, `while`, `and`, `or`, `not`, and the
   condition of a comprehension implicitly call `bool()` on the operand via
   `__bool__`/`__len__`. This is often called "truthiness" rather than
   casting, but mechanically it *is* an implicit conversion to `bool`.
3. **`bool` is a subclass of `int`** — so `True`/`False` are implicitly
   usable anywhere an `int` is expected, and arithmetic silently promotes
   them: `True + True == 2`.
4. **String concatenation with `+` is NOT implicit** — Python deliberately
   does **not** implicitly convert `int` to `str` in `"a" + 1`. This is a
   common contrast question: "Why does JavaScript give you `'a1'` but Python
   raises `TypeError`?" Python favors explicitness (PEP 20: "explicit is
   better than implicit") for anything that would be ambiguous or lossy.

### Why it matters / internals

Implicit numeric coercion is implemented via the binary operator protocol:
when you write `a + b`, Python tries `a.__add__(b)`; if that returns
`NotImplemented` (e.g., because the types differ), it tries
`b.__radd__(a)`. For built-in numeric types, CPython's C-level numeric
protocol (`nb_add` slots) knows how to widen `int` to `float` or `float` to
`complex` before performing the operation. No dunder-based explicit cast
(`__int__`, `__float__`) is invoked here — the promotion is baked into the
C implementation of the numeric types themselves.

Truthiness coercion internally calls `bool(x)`, which calls `type(x).__bool__(x)`
if defined, else falls back to `type(x).__len__(x) != 0`, else defaults to
`True`. This is why empty containers (`[]`, `{}`, `""`, `set()`) are falsy
even though they never define `__bool__` explicitly — they define `__len__`.

### Code example

```python
# 1. Numeric promotion in mixed arithmetic (implicit)
result = 3 + 4.5          # int + float -> float
print(result, type(result))          # 7.5 <class 'float'>

result2 = 2 + 3j          # int + complex -> complex
print(result2, type(result2))        # (2+3j) <class 'complex'>

# 2. bool is a subclass of int -> implicit promotion in arithmetic
print(True + True)                   # 2  (bool -> int)
print(True + 1.5)                    # 2.5 (bool -> int -> float)
print(isinstance(True, int))         # True

# 3. Truthiness / implicit bool() in conditions
values = [0, 1, "", "x", [], [1], None, 0.0]
for v in values:
    print(v, "->", bool(v))

# 4. What Python will NOT implicitly coerce
try:
    "age: " + 25
except TypeError as e:
    print("TypeError:", e)

# Contrast: this DOES work because both operands become the same
# numeric family through the numeric tower, not through str coercion.
print(1 == 1.0)                      # True: int compared with float
print(1 == True)                     # True: bool compared with int
```

### Common interview questions / gotchas

- **"Why does `1 == True` return `True`?"** Because `bool` subclasses `int`,
  and `True` is literally the int value `1` at the C level.
- **"Is `[] == False` True?"** No — `False`. Equality is not the same as
  truthiness. `bool([])` is `False`, but `[] == False` compares a list to a
  bool and returns `False` (different types, no special-cased equality).
- **"Why doesn't `"1" + 1` work but `1 + 1.0` does?"** Numeric types have a
  well-defined promotion order (the numeric tower); `str` and `int` do not,
  so combining them is ambiguous (concatenate? add numerically?), hence
  Python refuses and raises `TypeError` rather than guessing.
- **Gotcha:** `sum([True, True, False, True])` returns `3` — an easy trick
  question about counting `True` values in a list using `sum()`.
- **Gotcha:** In a dict, `{1: "int", True: "bool"}` collapses to a
  single key because `1 == True` and `hash(1) == hash(True)` — the second
  assignment overwrites the first: `{1: 'bool'}`.

### Pitfalls

- Assuming Python coerces types the way JS/PHP do (e.g., expecting
  `"5" + 5` to work) — it raises `TypeError` instead.
- Using `bool` values as dict/set keys interchangeably with `1`/`0` without
  realizing they collide.
- Relying on truthiness for numeric zero checks when `None` vs `0` vs `""`
  need to be distinguished — `if not x:` treats all of them the same;
  use `if x is None:` when that distinction matters.

---

## Explicit Casting

### Explanation

Explicit casting is when you call a constructor/conversion function yourself:
`int(x)`, `float(x)`, `str(x)`, `bool(x)`, `complex(x)`, `list(x)`,
`tuple(x)`, `dict(x)`, `set(x)`, `bytes(x)`, `bytearray(x)`. For the scope of
"type conversion" we focus on the scalar converters: `int`, `float`, `str`,
`bool`, `complex`.

Each of these constructors is not "magic" — it is a call to a type object
that internally consults dunder methods on the argument:

| Constructor | Dunder method(s) consulted (in rough priority) |
|---|---|
| `int(x)` | `__int__`, then `__index__` (for lossless integer-likes), then `__trunc__` as a fallback; for strings, its own text parser |
| `float(x)` | `__float__`, then `__index__`; for strings, its own text parser |
| `str(x)` | `__str__` (falls back to `__repr__` if `__str__` undefined) |
| `bool(x)` | `__bool__`, falls back to `__len__`, defaults to `True` |
| `complex(x)` | `__complex__`, then `__float__`/`__index__`; for strings, its own text parser |

### Why it matters / internals

Because `int()`, `float()`, etc. dispatch to dunder methods, **any custom
class can define how it converts** by implementing these methods. This is a
favorite SDE-2 interview probe: "How would you make your own class support
`int(myobj)`?"

```python
class Money:
    def __init__(self, cents):
        self.cents = cents

    def __int__(self):
        return self.cents // 100

    def __float__(self):
        return self.cents / 100

    def __str__(self):
        return f"${self.cents / 100:.2f}"

    def __repr__(self):
        return f"Money(cents={self.cents})"

    def __bool__(self):
        return self.cents != 0


m = Money(2599)
print(int(m))     # 25   -> calls __int__
print(float(m))   # 25.99 -> calls __float__
print(str(m))     # $25.99 -> calls __str__
print(bool(m))    # True -> calls __bool__
print(m)          # Money(cents=2599) -> print() uses __str__ too
print([m])        # [Money(cents=2599)] -> list repr uses __repr__ of elements
```

`__index__` deserves special mention: it is the protocol for "this object is
*losslessly* representable as a plain integer" and is what Python uses for
things like slice indices (`a[myobj:]`) and for `bin()`, `hex()`, `oct()`.
It's stricter than `__int__` — `__int__` can be lossy (e.g., `int(3.7)`
truncates), but `__index__` should only exist on things that are *exactly*
integral (e.g., `Decimal` does not define `__index__` but does define
`__int__`; `Fraction` with an integral value could).

### Code example

```python
# int() truncates toward zero for floats — NOT the same as round()
print(int(3.99))     # 3
print(int(-3.99))    # -3  (truncation toward zero, not floor!)
print(int(3.5))      # 3
print(round(3.5))    # 4  (banker's rounding, see gotchas)
print(round(-3.5))   # -4

# int() on bool
print(int(True), int(False))    # 1 0

# float() -> int is also truncation, not rounding
print(int(2.9999999))   # 2

# str() vs repr()
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __str__(self):
        return f"({self.x}, {self.y})"
    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"

p = Point(1, 2)
print(str(p))    # (1, 2)
print(repr(p))   # Point(x=1, y=2)
print(f"{p}")    # (1, 2)   f-strings use __format__ -> falls back to __str__
print(f"{p!r}")  # Point(x=1, y=2)  explicit repr conversion in f-string

# complex()
print(complex(3))         # (3+0j)
print(complex(3, 4))      # (3+4j)
print(complex("3+4j"))    # (3+4j)  NOTE: no spaces allowed around + inside the string!

try:
    complex("3 + 4j")
except ValueError as e:
    print("ValueError:", e)

# bool() explicit cast
print(bool(0), bool(0.0), bool(""), bool([]), bool({}), bool(None))  # all False
print(bool(0.0000001), bool("False"), bool(" "))  # all True (non-empty/non-zero)
```

### Common interview questions / gotchas

- **"Does `int(True)` equal 1?"** Yes, `1`.
- **"What's `int(-3.7)`?"** `-3`, because `int()` truncates toward zero
  (uses `__trunc__` semantics), it does *not* floor. Contrast with
  `math.floor(-3.7) == -4`.
- **"`round(0.5)` vs `round(1.5)` — what do you get?"** `0` and `2`
  respectively — Python 3's `round()` uses **banker's rounding**
  (round-half-to-even) to reduce cumulative bias in repeated rounding, not
  the "round half up" most people learn in school. This trips up a lot of
  candidates.
- **"Why is `bool("False")` `True`?"** Because `str.__bool__` (inherited
  generic truthiness via `__len__`) only checks whether the string is
  *empty*, not its textual content. Any non-empty string, including
  `"False"`, `"0"`, `"  "`, is truthy.
- **"How do you make a custom object work with `int()`?"** Implement
  `__int__` (and `__index__` if it's a true integral type).
- **"Difference between `__str__` and `__repr__`?"** `__str__` is meant for
  end-user-friendly display; `__repr__` is meant to be unambiguous /
  developer-facing (ideally `eval(repr(x)) == x`). `str()` falls back to
  `__repr__` if `__str__` is not defined; `repr()` never falls back to
  `__str__`.

### Pitfalls

- Using `int()` when you mean `round()` (or vice versa) — truncation silently
  discards the fractional part and can introduce off-by-one bugs, especially
  with negative numbers.
- Forgetting `complex("3+4j")` requires no internal whitespace — a common
  runtime surprise when parsing computed strings.
- Assuming `bool(some_string)` reflects the *meaning* of the string rather
  than merely whether it's non-empty.
- Defining `__int__` but forgetting `__index__` for a class meant to be used
  in slicing / bin()/hex() contexts — you'll get a confusing `TypeError:
  'MyClass' object cannot be interpreted as an integer`.

---

## Numeric Promotion

### Explanation

Numeric promotion is the automatic widening of one numeric type into a
"larger" one when mixing types in arithmetic, so no precision is lost that
could otherwise be avoided (with the notable exception of `int -> float`,
which *can* lose precision for very large ints — see below). Python's
informal "numeric tower" ordering is:

```
bool  ->  int  ->  float  ->  complex
```

`Decimal` and `Fraction` (from `decimal` and `fractions`) are *not* part of
this automatic tower — mixing `Decimal` with `float` directly raises
`TypeError` by design, because silently converting between them would hide
precision-loss bugs. You must convert explicitly.

### Why it matters / internals

When CPython evaluates `a op b` for numeric types:

1. It checks `type(a).__op__(a, b)`. Built-in numeric types implement mixed
   arithmetic by checking the other operand's type and promoting internally.
2. If `a`'s type doesn't know how to handle `b` (returns `NotImplemented`),
   Python tries `type(b).__rop__(b, a)`.
3. If both fail, `TypeError` is raised.

The promotion itself for built-ins (`int`, `float`, `complex`) is
implemented directly in C — not via calling `__int__`/`__float__` on each
other, since these are all "known" numeric types to each other's
implementations. For **user-defined numeric types**, this is precisely why
the `numbers` ABC hierarchy (`numbers.Integral`, `numbers.Rational`,
`numbers.Real`, `numbers.Complex`) and operator overloading
(`__add__`/`__radd__`, etc.) exist — you're expected to implement the
promotion logic yourself if you want your custom class to interoperate with
built-in numerics.

**Precision subtlety:** `int -> float` promotion is not always lossless.
Python's `int` is arbitrary precision, but `float` is a 64-bit IEEE-754
double with 53 bits of mantissa. So:

```python
big = 2**60 + 1
print(float(big) == big)   # False! precision lost above 2**53
```

This is a real gotcha in numeric code and a good "do you actually understand
floats" interview probe.

### Code example

```python
# Numeric tower widening
print(type(1 + 1))          # int
print(type(1 + 1.0))        # float  (int promoted to float)
print(type(1.0 + 1j))       # complex (float promoted to complex)
print(type(True + 1))       # int   (bool promoted to int)
print(type(True + 1.0))     # float (bool -> int -> float)

# Division always produces float, even int / int (true division)
print(type(4 / 2))          # float -> 2.0
print(4 / 2)                # 2.0
print(4 // 2)               # 2   (floor division keeps int if both int)
print(type(4 // 2))         # int
print(type(4.0 // 2))       # float (floor division of float is still float)

# Decimal/Fraction are NOT auto-promoted with float
from decimal import Decimal
from fractions import Fraction

try:
    Decimal("1.1") + 0.1
except TypeError as e:
    print("TypeError:", e)   # unsupported operand type(s)

# Explicit conversion required
print(Decimal("1.1") + Decimal(str(0.1)))   # Decimal('1.20')
print(Fraction(1, 3) + Fraction(1, 6))       # Fraction(1, 2)
print(float(Fraction(1, 3)))                 # 0.3333333333333333

# Precision loss going int -> float for very large ints
big = 2**60 + 1
print(big)                 # 1152921504606846977
print(float(big))          # 1.152921504606847e+18
print(int(float(big)) == big)  # False -- precision lost
```

### Common interview questions / gotchas

- **"What type does `1 + 1.0` produce, and why?"** `float`; Python widens
  `int` to `float` before adding, following the numeric tower.
- **"Does `4 / 2` give an int or a float?"** `float` (`2.0`) — Python 3's
  `/` is *true division* and always returns `float` (unlike Python 2 where
  `int / int` did floor division). `//` is floor division and preserves
  `int` if both operands are `int`.
- **"Why can't you add a `Decimal` and a `float` directly?"** Because
  `float` can't exactly represent most decimal fractions (e.g., `0.1`), so
  mixing them could silently introduce rounding errors that `Decimal` exists
  specifically to avoid. Python forces an explicit, deliberate conversion.
- **"Is `int -> float` conversion always safe?"** No — ints have arbitrary
  precision; floats only have 53 bits of integer precision. Converting very
  large ints to float loses precision silently unless you check for it.
- **"How does `complex` fit into comparisons?"** It doesn't — `complex`
  numbers don't support ordering (`<`, `>`); only `==`/`!=`. Trying
  `1+2j < 3+4j` raises `TypeError`.
- **Amazon/Microsoft favorite**: "Implement `__add__`/`__radd__` on a custom
  `Vector` class so `Vector(1,2) + 1` and `1 + Vector(1,2)` both work." Tests
  whether you understand promotion is a *protocol*, not magic.

### Pitfalls

- Assuming `Decimal`/`Fraction` participate in the same auto-promotion as
  built-in numerics — they don't, and mixing them with `float` raises.
- Silently losing precision converting big ints to float without realizing
  it (common in ID/hash-related bugs when accidentally casting IDs to float
  for some computation).
- Forgetting `//` on two floats still returns a `float` (e.g., `7.0 // 2 ==
  3.0`, not `3`).
- Comparing `complex` numbers with `<`/`>` and getting a `TypeError` at
  runtime instead of catching it via type checking earlier.

---

## Parsing Strings

### Explanation

"Parsing strings" means converting textual data into typed Python values.
This is distinct from casting a value you already hold (e.g., `float` ->
`int`); here the input is always `str`, and the output type must be
*inferred or specified* by you, because a string carries no type metadata.
The main tools:

- `int(s)`, `int(s, base)` — parse text as an integer, optionally in a given
  base (2, 8, 16, or 0 to auto-detect from a prefix like `0x`).
- `float(s)` — parse text as a float, including special values `"inf"`,
  `"-inf"`, `"nan"` (case-insensitive).
- `complex(s)` — parse text as a complex number (strict format, no spaces
  around the internal `+`/`-`).
- `bool(s)` — **does NOT parse** the textual meaning; only checks
  non-emptiness (a classic gotcha, covered above and again here because it's
  so relevant to "parsing").
- `ast.literal_eval(s)` — safely parse a string containing a Python literal
  (numbers, strings, tuples, lists, dicts, sets, booleans, `None`) into the
  corresponding Python object, without the security risk of `eval()`.
- `str.format()` / f-strings — these go the *other direction* (value ->
  string), not string -> value; worth contrasting explicitly since
  interviewers sometimes conflate "formatting" with "parsing."

### Why it matters / internals

`int(s)` and `float(s)` use CPython's dedicated string-to-number parsers
(implemented in C, e.g. `PyLong_FromString`/`PyOS_string_to_double`) — they
are **not** implemented by calling `__int__`/`__float__` on the string
(`str` doesn't define those). The parsers:

- Strip leading/trailing ASCII whitespace automatically.
- Accept a single optional leading `+`/`-` sign.
- For `int(s)`: reject decimal points and exponents entirely — `int("42.0")`
  raises `ValueError` even though `42.0` is "clearly" an integer value. You
  must go through `float` first: `int(float("42.0"))`.
  Also, `int(s)` (base 10, the default) rejects underscores at invalid
  positions but *does* accept PEP 515 digit-group underscores like
  `int("1_000")` -> `1000`.
- For `float(s)`: accepts decimal points, exponents (`"1e10"`), and the
  special tokens `"inf"`, `"-inf"`, `"nan"` (case-insensitive, optionally
  with sign).
- Both raise `ValueError` (not `TypeError`) on malformed input, since the
  types are compatible (`str`) but the *value* is invalid — a very common
  distinction interviewers check: "which exception, and why that one?"

`ast.literal_eval` walks a restricted AST grammar and only allows literal
node types — it cannot execute arbitrary code, unlike `eval()`, which makes
it the correct tool whenever you must parse "Python-looking" data (like a
list or dict literal) from an untrusted or semi-trusted source (e.g., a
config file or user input) instead of full JSON.

`int(s, base)`: base `0` means "infer from prefix" — `"0x1A"` -> hex,
`"0o17"` -> octal, `"0b101"` -> binary, otherwise decimal (but a string with
a leading `0` followed by digits like `"0123"` is invalid when base=0,
avoiding the old-style-octal ambiguity C had).

### Code example

```python
# --- int() parsing ---
print(int("  42  "))          # 42 -- whitespace stripped automatically
print(int("+42"))             # 42 -- leading + allowed
print(int("-42"))             # -42
print(int("1_000"))           # 1000 -- PEP 515 underscore grouping

try:
    int("42.0")                # ValueError: invalid literal for int() with base 10
except ValueError as e:
    print("ValueError:", e)

print(int(float("42.0")))     # 42 -- go through float() first

# int() with explicit base
print(int("1010", 2))         # 10   binary
print(int("ff", 16))          # 255  hex
print(int("0x1A", 16))        # 26   prefix optional when base matches
print(int("0x1A", 0))         # 26   base=0 infers from '0x' prefix
print(int("17", 8))           # 15   octal

# --- float() parsing ---
print(float("  3.14  "))      # 3.14
print(float("1e10"))          # 10000000000.0
print(float("inf"))           # inf
print(float("-Infinity"))     # -inf
n = float("nan")
print(n, n != n)              # nan True  (NaN never equals itself!)

try:
    float("abc")
except ValueError as e:
    print("ValueError:", e)

# --- complex() parsing ---
print(complex("3+4j"))        # (3+4j)
try:
    complex("3 + 4j")          # ValueError: spaces not allowed around the sign
except ValueError as e:
    print("ValueError:", e)

# --- bool() does NOT parse meaning ---
print(bool("False"), bool("0"), bool("true"))   # True True True (all non-empty!)

def str_to_bool(s: str) -> bool:
    """The correct way to parse a boolean-looking string."""
    return s.strip().lower() in ("true", "1", "yes", "y", "on")

print(str_to_bool("False"))   # False
print(str_to_bool("YES"))     # True

# --- ast.literal_eval for safe structured parsing ---
import ast

data = ast.literal_eval("[1, 2, {'a': 3.5, 'b': (True, None)}]")
print(data, type(data))       # [1, 2, {'a': 3.5, 'b': (True, None)}] <class 'list'>

try:
    ast.literal_eval("os.system('rm -rf /')")   # rejected: not a literal
except (ValueError, SyntaxError) as e:
    print("Rejected unsafe input:", type(e).__name__)

# eval() would actually execute arbitrary code -- never use it on untrusted input
# ast.literal_eval only permits literal nodes, so it's safe by construction

# --- Robust parsing pattern with exception handling ---
def safe_parse_int(s: str, default=None):
    try:
        return int(s.strip())
    except (ValueError, AttributeError):
        return default

print(safe_parse_int("  17"))     # 17
print(safe_parse_int("nope", -1)) # -1

# --- str.format / f-strings go value -> string, the opposite direction ---
pi = 3.14159265
print("{:.2f}".format(pi))    # 3.14
print(f"{pi:.2f}")             # 3.14
print(f"{1000000:,}")          # 1,000,000
# None of these "parse" a string into a number -- they format a number
# into a string. Don't confuse formatting with parsing in an interview.
```

### Common interview questions / gotchas

- **"Does `int('  42  ')` work?"** Yes — leading/trailing whitespace is
  stripped automatically by the parser.
- **"Does `int('42.0')` work?"** No — raises `ValueError`. `int()`'s string
  parser only accepts optional sign + digits (+ underscores between digits);
  it will not interpret a decimal point. You must `int(float('42.0'))`.
- **"What does `float('nan')` give you, and how do you test for NaN?"**
  It gives a float NaN object. Critically, `nan != nan` is `True` (NaN is
  never equal to anything, including itself, per IEEE-754), so you cannot
  test with `x == float('nan')`. Use `math.isnan(x)` instead.
- **"What exception type does invalid parsing raise — `TypeError` or
  `ValueError`?"** `ValueError`. The *type* is right (it's a string), the
  *value* is wrong (unparseable content). This distinction is a frequent
  "explain the difference" interview question in itself.
- **"Is `bool('False')` `False`?"** No — it's `True`, because `bool()` on a
  string only checks emptiness, not content. You must write your own
  parser (or use something like `distutils.util.strtobool`, though that's
  deprecated in 3.12 — prefer a small custom function or a library like
  `pydantic`).
- **"Why prefer `ast.literal_eval` over `eval`?"** `eval` executes arbitrary
  expressions including function calls and attribute access — a huge
  security hole with untrusted input (RCE risk). `literal_eval` only builds
  literal Python objects from a constrained grammar, so it can't execute
  code.
- **"Locale pitfalls?"** `float()`/`int()` always use the `C`/POSIX-style
  format regardless of the OS locale: decimal point `.` (not `,`), and they
  reject locale-specific thousands separators (e.g., `float("1,234.5")`
  raises `ValueError`; some locales write `"1.234,5"` for the same number).
  If you need locale-aware parsing, you must use the `locale` module
  (`locale.atof`) or a library, and set the locale explicitly — never rely
  on ambient system locale for correctness in production parsing code,
  since it's process-global, not thread-safe to mutate, and unpredictable
  across deployment environments. This is a classic "gotcha" at companies
  like Uber/Flipkart/Walmart that operate across many locales.
- **"How do you parse `'0x1A'` as hex safely without knowing the base ahead
  of time?"** `int(s, 0)` — base 0 infers from the `0x`/`0o`/`0b` prefix.
- **Flipkart/Walmart favorite**: parse a CSV field that might be `""`,
  `"N/A"`, `"42"`, or `"42.5"` into a typed value robustly — tests whether
  you reach for `try/except` blocks with sensible fallbacks rather than
  assuming clean input.

### Pitfalls

- Trusting `bool(some_string)` to reflect the string's semantic meaning.
- Using `eval()` to parse structured data from user/config input instead of
  `ast.literal_eval` or `json.loads` — a security vulnerability.
- Forgetting `int()` cannot parse `"42.0"`, `"1e3"`, or thousands-separated
  numbers like `"1,000"` — all raise `ValueError`.
- Comparing parsed NaN values with `==` instead of `math.isnan()`.
- Assuming `int(s, base)` prefixes are optional in all cases — when you pass
  an explicit non-zero base like `16`, the `0x` prefix is optional and
  accepted, but if you pass base `10` explicitly, a `0x` prefix is *not*
  accepted and raises `ValueError`.
- Ignoring locale differences in decimal/thousands separators when parsing
  user-facing numeric input in a global product.
- Not catching parsing exceptions at all, letting a single bad row of input
  crash a batch job instead of logging/skipping/defaulting gracefully.

---

## Quick Reference Summary

| Operation | Implicit? | Exceptions raised | Key dunder / mechanism |
|---|---|---|---|
| `int + float` | Yes (numeric tower) | — | C-level numeric promotion |
| `bool` used as `int` | Yes | — | `bool` subclasses `int` |
| `"a" + 1` | No — `TypeError` | `TypeError` | no implicit str<->int coercion |
| `int(x)` | No (explicit) | `TypeError`/`ValueError` | `__int__`/`__index__` |
| `float(x)` | No (explicit) | `TypeError`/`ValueError` | `__float__`/`__index__` |
| `str(x)` | No (explicit) | rarely raises | `__str__` (falls back to `__repr__`) |
| `bool(x)` | No (explicit) | never raises | `__bool__`/`__len__` |
| `int("42.0")` | No | `ValueError` | string parser rejects decimal point |
| `float("nan")` | No | — | returns NaN; compare with `math.isnan` |
| `ast.literal_eval` | No | `ValueError`/`SyntaxError` | restricted AST grammar |
| `Decimal + float` | No — `TypeError` | `TypeError` | not part of numeric tower |
