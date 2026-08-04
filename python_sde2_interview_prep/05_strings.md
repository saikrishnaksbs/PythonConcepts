# Strings

Strings are one of the most heavily tested topics in SDE-2 interviews because
they sit at the intersection of language internals (immutability, interning,
memory layout), algorithmic thinking (sliding window, two pointers, hashing),
and practical engineering (encoding bugs, performance of concatenation). This
file covers CPython string internals as well as the practical API surface you
need for interviews at Google, Amazon, Microsoft, Atlassian, Uber, Flipkart,
Walmart, and Adobe.

## String Creation

Strings in Python are sequences of Unicode code points. You can create them
with single quotes, double quotes, triple quotes (for multi-line strings), or
the `str()` constructor.

```python
s1 = 'hello'
s2 = "hello"
s3 = '''multi
line'''
s4 = """also
multi line"""
s5 = str(123)          # '123'
s6 = str([1, 2, 3])    # '[1, 2, 3]'
s7 = ""                # empty string
s8 = str()              # empty string, same thing

# Mixing quotes to avoid escaping
s9 = "He said 'hi'"
s10 = 'She said "hi"'

# Implicit concatenation of adjacent literals (compile-time)
s11 = ("This is a long string "
       "split across multiple lines")
```

**Why it matters:** Python does not have a separate `char` type — a single
character is just a string of length 1. Adjacent string literals are
concatenated by the compiler (not at runtime), which is useful for long SQL
queries, regex patterns, or docstrings without needing `+` or `\` line
continuations.

**Interview gotcha:** `str()` calls `__str__`, while `repr()` calls
`__repr__`. Know the difference — `__repr__` should be unambiguous and
ideally `eval`-able, `__str__` is for human-readable display.

## Immutability

Strings in Python are **immutable** — once created, a string object's content
can never be changed in place. Every operation that appears to "modify" a
string (`upper()`, `replace()`, `+=`, slicing) actually creates and returns a
**new** string object.

```python
s = "hello"
s_upper = s.upper()
print(s, s_upper)      # hello HELLO  (original unchanged)

s = "hello"
original_id = id(s)
s += " world"
print(id(s) == original_id)   # False - new object created

# You cannot do this:
# s[0] = 'H'   -> TypeError: 'str' object does not support item assignment
```

**Why immutability exists (internals/rationale):**
1. **Hashability** — immutable objects can be safely hashed once and cached
   (CPython caches the hash of a `str` object after first computation), which
   makes strings usable as dict keys / set members. A mutable string could
   corrupt hash-based containers if changed after insertion.
2. **Safety for interning and sharing** — since strings can't change, CPython
   can safely let multiple variables point to the same string object (see
   Interning below) without fear that mutating one reference corrupts
   another.
3. **Thread-safety** — immutable objects can be freely shared between threads
   without locks.
4. **Predictability** — passing a string to a function guarantees the caller's
   copy is never mutated (no defensive copying needed).

**Pitfall:** Because strings are immutable, naive concatenation in a loop
creates a new object on every iteration — this is the classic O(n^2)
performance trap (see "String Performance" below).

## Interning

**Interning** is an optimization where CPython keeps a single shared copy of
certain string objects so that multiple references to "the same" string value
point to the same object in memory, saving memory and speeding up equality
checks (`is` becomes valid for identity where it would otherwise only be
valid via `==`).

```python
a = "hello"
b = "hello"
print(a is b)     # True - both literals interned automatically

a = "hello world!"      # contains a space and punctuation
b = "hello world!"
print(a is b)      # Often True at module level due to compile-time folding,
                    # but NOT guaranteed - implementation detail

# Identifier-like strings (valid Python identifiers: letters, digits, underscore)
# are automatically interned by CPython
a = "hello_world"
b = "hello_world"
print(a is b)      # True

a = "hello world"   # has a space -> not identifier-like
b = "hello world"
print(a is b)       # Often True for literals compiled together, but not a guarantee

# Strings built at runtime are usually NOT interned automatically
a = "hello"
b = "".join(["h", "e", "l", "l", "o"])
print(a == b)   # True
print(a is b)   # False - different objects, built dynamically

# Force interning manually
import sys
a = sys.intern("hello world")
b = sys.intern("hello world")
print(a is b)   # True - both point to the same interned object
```

**Why it matters / internals:** CPython automatically interns:
- All string literals that look like identifiers (`[a-zA-Z_][a-zA-Z0-9_]*`)
  at compile time, because these are extremely common as dict keys,
  attribute names, and variable names.
- Single-character strings (in the Latin-1 range) are cached globally.
- Small integers -5 to 256 follow a similar caching pattern (not strings, but
  the same idea applies — interviewers sometimes conflate the two).

`sys.intern()` lets you explicitly opt into interning for strings you know
will be compared or used as dict keys frequently (e.g., parser tokens,
compiler symbol tables) — this turns `==` comparisons effectively into
pointer comparisons in tight loops, a real performance optimization used
inside CPython itself (e.g., attribute name lookup).

**Interview gotcha:** `'a' * 3 is 'a' * 3` behavior is implementation-defined
and depends on constant folding at compile time — this is a classic trick
question. **Never rely on `is` for string equality**; always use `==`. `is`
compares identity (same object in memory), `==` compares value.

```python
# Classic interview trap
print('a' * 20 is 'a' * 20)   # True in CPython REPL (constant folded)
x = 20
print('a' * x is 'a' * x)     # Often False - computed at runtime, not folded
```

## Indexing

Strings support zero-based indexing, and negative indexing to count from the
end.

```python
s = "Python"
print(s[0])      # 'P'  (first character)
print(s[5])      # 'n'  (last character)
print(s[-1])     # 'n'  (last character, negative indexing)
print(s[-6])     # 'P'  (first character via negative index)

# Out of range raises IndexError
try:
    s[10]
except IndexError as e:
    print("IndexError:", e)
```

**Why it matters:** Negative indexing (`s[-1]`) is idiomatic Python for
"last element" and is O(1) because CPython strings support direct random
access (they are stored as contiguous arrays of fixed-width code units, not
linked lists). This is different from many other languages where you'd need
`s.length() - 1`.

**Interview gotcha:** Indexing out of bounds **raises `IndexError`**, but
**slicing** out of bounds does **not** raise — it just clamps to valid range
(see Slicing below). This asymmetry trips up a lot of candidates.

## Slicing

Slicing extracts a substring using `s[start:stop:step]`. All three parts are
optional and slicing never raises an error for out-of-range bounds — it
simply clamps.

```python
s = "Hello, World!"

print(s[0:5])     # 'Hello'
print(s[7:])      # 'World!'
print(s[:5])      # 'Hello'
print(s[:])       # 'Hello, World!' (full copy)
print(s[-6:])     # 'World!'
print(s[::2])     # 'Hlo ol!'   every 2nd character
print(s[::-1])    # '!dlroW ,olleH'  reversed string (very common idiom)
print(s[100:200]) # ''  - no error, just empty

# The slice() object
sl = slice(0, 5)
print(s[sl])       # 'Hello'

sl2 = slice(None, None, -1)
print(s[sl2])       # reversed
```

**Why it matters / internals:** `s[a:b:c]` is syntactic sugar for
`s.__getitem__(slice(a, b, c))`. Python resolves out-of-range slice bounds by
clamping to `[0, len(s)]` rather than raising, which makes slicing safe to
use defensively (e.g., `s[:100]` to get "up to 100 chars" without checking
length first). Because strings are immutable, `s[:]` still creates a shallow
"copy" reference — but since strings are immutable this is essentially free
either way in CPython.

**Interview gotcha:** `s[::-1]` is the standard Pythonic idiom for reversing
a string — expect to be asked to reverse a string or check palindromes using
slicing. Also know that `step=0` raises `ValueError: slice step cannot be
zero`.

## Escape Characters

Escape sequences let you embed special characters (newlines, tabs, quotes,
unicode) inside string literals using a backslash.

| Escape | Meaning |
|---|---|
| `\n` | newline |
| `\t` | tab |
| `\\` | literal backslash |
| `\'` | single quote |
| `\"` | double quote |
| `\r` | carriage return |
| `\b` | backspace |
| `\f` | form feed |
| `\0` | null character |
| `\xhh` | character with hex value hh |
| `\uxxxx` | Unicode char with 16-bit hex value |
| `\Uxxxxxxxx` | Unicode char with 32-bit hex value |
| `\N{NAME}` | Unicode char by name |
| `\ooo` | character with octal value ooo |

```python
print("Line1\nLine2")        # newline
print("Col1\tCol2")          # tab
print("She said \"hi\"")     # escaped double quote
print('It\'s here')          # escaped single quote
print("Backslash: \\")       # literal backslash
print("\x41")                # 'A' (hex 41)
print("\u00e9")               # 'é'
print("\N{BULLET}")           # '•'
```

**Why it matters:** Interviewers sometimes ask you to debug why a
Windows-style file path like `"C:\newfolder"` behaves unexpectedly —
`\n` is interpreted as a newline escape, producing `C:` + newline +
`ewfolder`. This is a real-world bug source and motivates raw strings.

## Raw Strings

A raw string literal, prefixed with `r` or `R`, tells Python to treat
backslashes as literal characters rather than the start of an escape
sequence.

```python
path = r"C:\newfolder\test"
print(path)     # C:\newfolder\test  (no newline interpreted)

normal = "C:\newfolder\test"
print(normal)   # C:  (newline)  ewfolder	est  (tab interpreted!)

# Extremely common for regex patterns
import re
pattern = r"\d+\.\d+"     # matches things like "3.14"
print(re.findall(pattern, "pi is 3.14 and e is 2.71"))

# Gotcha: raw strings cannot end with an odd number of backslashes
# r"C:\path\"   -> SyntaxError, because \" is still treated as escaping the quote
ok = r"C:\path" + "\\"    # workaround
```

**Why it matters:** Raw strings are essential for regular expressions (regex
metacharacters like `\d`, `\w`, `\b` would otherwise need double escaping:
`"\\d+"` vs `r"\d+"`) and for Windows file paths. This is a very common
"why does my regex/path break" interview/debugging question.

**Gotcha:** A raw string literal still cannot end in a single backslash
because the parser needs to know whether the following quote is escaped —
`r"\"` is invalid syntax.

## Unicode

Python 3 strings (`str`) are sequences of **Unicode code points** — abstract
integers, not bytes. This is different from Python 2, where `str` was a byte
string by default.

```python
s = "café"          # contains a non-ASCII character
print(len(s))         # 4 - counted as 4 code points, not bytes
print(ord('é'))       # 233 - the Unicode code point (integer)
print(chr(233))        # 'é' - code point back to character

# Emoji and astral-plane characters
emoji = "😀"
print(len(emoji))     # 1 in Python 3 (uses "wide" internal representation)
print(ord(emoji))     # 128512

# Unicode normalization (important for comparing "equivalent" strings)
import unicodedata
s1 = "café"                       # é as a single code point (U+00E9)
s2 = "cafe\u0301"                 # e + combining acute accent (U+0065 U+0301)
print(s1 == s2)                    # False! Visually identical, different code points
print(unicodedata.normalize('NFC', s1) == unicodedata.normalize('NFC', s2))  # True
```

**Why it matters / internals:** Since PEP 393 (Python 3.3+), CPython uses a
**flexible string representation**: each string is internally stored using
the smallest fixed-width encoding that fits all its characters —
1 byte/char (Latin-1) if all code points fit in 0-255, 2 bytes/char (UCS-2)
if the max code point fits in 16 bits, or 4 bytes/char (UCS-4) if any
character requires a full 32-bit code point (e.g., emoji, rare CJK
characters, astral plane). This makes `len()` and indexing O(1) while
staying memory-efficient for the common ASCII/Latin-1 case.

**Interview gotcha:** Unicode normalization forms (NFC, NFD, NFKC, NFKD)
matter for "are these two strings equal" questions when accented characters
or diacritics are involved — visually identical strings can compare unequal
if built from different code point sequences. This is a real bug source in
search/dedup systems (e.g., usernames from different input methods).

## Encoding/Decoding

**Encoding** converts a `str` (Unicode code points) into `bytes` using a
specific scheme (UTF-8, UTF-16, ASCII, etc.). **Decoding** converts `bytes`
back into a `str`.

```python
s = "café"

b_utf8 = s.encode('utf-8')
print(b_utf8)             # b'caf\xc3\xa9'  - é takes 2 bytes in UTF-8
print(len(b_utf8))        # 5 bytes (c-a-f-é(2 bytes))

b_utf16 = s.encode('utf-16')
print(b_utf16)             # includes BOM + 2 bytes per char typically

b_ascii_fail = None
try:
    s.encode('ascii')     # 'é' is not representable in ASCII
except UnicodeEncodeError as e:
    print("UnicodeEncodeError:", e)

# Handle it gracefully
print(s.encode('ascii', errors='ignore'))     # b'caf' - drops non-ascii
print(s.encode('ascii', errors='replace'))    # b'caf?' - replaces with '?'
print(s.encode('utf-8', errors='replace'))

# Decoding
b = b'caf\xc3\xa9'
print(b.decode('utf-8'))    # 'café'

try:
    b.decode('ascii')
except UnicodeDecodeError as e:
    print("UnicodeDecodeError:", e)

# Reading files - always specify encoding explicitly
with open('example.txt', 'w', encoding='utf-8') as f:
    f.write("café ☕")
with open('example.txt', 'r', encoding='utf-8') as f:
    print(f.read())
```

**Why it matters:** UTF-8 is the dominant encoding on the web and in most
modern systems because it's backward-compatible with ASCII (1 byte for
ASCII chars) and variable-width (1-4 bytes per code point), making it
compact for English text while still supporting all Unicode. UTF-16 uses 2
or 4 bytes per code point and is common in Windows APIs and Java/JS internal
string representation. UTF-32 uses a fixed 4 bytes per code point (simple
but memory-heavy).

**Interview gotcha:** `UnicodeDecodeError` is one of the most common
production bugs — e.g., reading a file that's actually Latin-1/Windows-1252
encoded using `open(..., encoding='utf-8')` (or relying on platform default
encoding, which differs between Linux and Windows). Always be explicit about
encoding when reading/writing files or sockets. Know the difference between
`errors='strict'` (default, raises), `'ignore'`, `'replace'`, and
`'backslashreplace'`.

## String Formatting

Python has evolved through multiple formatting mechanisms. Know all three
and their tradeoffs.

```python
name, age = "Alice", 30

# 1. % formatting (old-style, C-like) - least preferred today
print("Name: %s, Age: %d" % (name, age))

# 2. str.format() - more flexible, introduced in Python 2.6/3.0
print("Name: {}, Age: {}".format(name, age))
print("Name: {0}, Age: {1}, again: {0}".format(name, age))   # positional reuse
print("Name: {n}, Age: {a}".format(n=name, a=age))             # keyword
print("{:.2f}".format(3.14159))          # '3.14'
print("{:>10}".format("hi"))              # right-align in width 10
print("{:,}".format(1234567))              # '1,234,567'

# 3. f-strings (Python 3.6+) - fastest, most readable, preferred
print(f"Name: {name}, Age: {age}")
print(f"Next year: {age + 1}")             # expressions allowed
print(f"{3.14159:.2f}")                     # formatted inline
print(f"{name!r}")                          # calls repr(): 'Alice'
```

**Why it matters:** `%`-formatting is a thin wrapper around C's `printf`
style and is limited (no method calls inside easily, harder to read with
many args). `str.format()` is more powerful (supports reordering, named
args, nested attribute/index access) but verbose. f-strings, added in PEP
498, are compiled directly into bytecode that evaluates the embedded
expression and formats it — making them both the fastest and most readable
option in modern Python. Interviewers commonly ask you to justify why you'd
choose one over another in code review.

## f-Strings

f-strings (formatted string literals) let you embed Python expressions
directly inside string literals, prefixed with `f`.

```python
x, y = 10, 20
print(f"{x} + {y} = {x + y}")     # expressions evaluated inline

name = "bob"
print(f"{name.upper()}")           # method calls work: 'BOB'

data = {"key": "value"}
print(f"{data['key']}")             # dict access works

# Format specs (same mini-language as str.format)
pi = 3.14159265
print(f"{pi:.3f}")                  # '3.142'
print(f"{1000000:,}")                # '1,000,000'
print(f"{0.25:.1%}")                 # '25.0%'
print(f"{42:08b}")                    # '00101010' - binary, zero-padded

# Debugging shortcut (Python 3.8+): self-documenting expressions
value = 42
print(f"{value=}")                   # 'value=42'
print(f"{value=:.2f}")               # for numeric formatting too

# Nested f-strings / dynamic width & precision
width = 10
print(f"{name:>{width}}")             # dynamic width from variable

# Multi-line f-strings
report = (
    f"Name: {name}\n"
    f"Value: {value}"
)
```

**Internals:** f-strings are **not** evaluated at runtime the way `%` or
`.format()` template strings are parsed — they are compiled by the Python
parser into bytecode at compile time. Each `{expr}` becomes actual bytecode
that evaluates `expr` and calls `format()` on the result, concatenated with
`BUILD_STRING`. This is why f-strings are the fastest formatting mechanism —
there's no runtime parsing of a template string, no attribute-lookup
mini-interpreter like `.format()` uses.

**Interview gotcha:** f-strings cannot use backslashes directly inside the
`{}` expression part in Python versions before 3.12 (`f"{'\n'}"` was a
SyntaxError pre-3.12); assign the value to a variable first as a workaround
in older versions. Also, f-strings evaluate expressions at the point the
literal is executed, not lazily — don't confuse them with logging's lazy
`%s` formatting (using f-strings in `logging.debug(f"...")` calls always
evaluates the expression even if the log level suppresses output, which is
wasteful — prefer `logging.debug("%s", value)` in hot paths).

## format()

`format()` is both a built-in function and a string method, driven by the
**Format Specification Mini-Language**.

```python
# Built-in format() function -> calls obj.__format__(spec)
print(format(3.14159, '.2f'))    # '3.14'
print(format(42, 'x'))            # '2a' - hex
print(format(42, 'o'))            # '52' - octal
print(format(42, 'b'))            # '101010' - binary
print(format(1234567, ','))       # '1,234,567'
print(format(0.5, '.0%'))         # '50%'

# str.format() method
print("{:<10}|".format("left"))    # left-align, width 10
print("{:>10}|".format("right"))   # right-align
print("{:^10}|".format("mid"))     # center-align
print("{:*^10}|".format("mid"))    # center, pad with '*'

# Custom __format__ for user-defined classes
class Money:
    def __init__(self, amount):
        self.amount = amount
    def __format__(self, spec):
        if spec == 'usd':
            return f"${self.amount:,.2f}"
        return str(self.amount)

m = Money(1234.5)
print(f"{m:usd}")     # '$1,234.50'
print(format(m, 'usd'))
```

**Why it matters:** Understanding that `format()`/`f"{x:spec}"`/`"{}".format(x)`
all ultimately dispatch to `type(x).__format__(x, spec)` explains why you
can make your own classes formattable, and is a common "how would you make
this custom object print nicely" interview question.

## Common String Methods

These are the bread-and-butter methods used constantly in interviews (string
manipulation, parsing, validation).

```python
s = "  Hello, World!  "

# Whitespace
print(s.strip())         # 'Hello, World!' - removes leading/trailing whitespace
print(s.lstrip())        # removes leading only
print(s.rstrip())        # removes trailing only
print("xxhelloxx".strip('x'))   # 'hello' - strips given chars, not substring

# Case
print("hello".upper())          # 'HELLO'
print("HELLO".lower())          # 'hello'
print("hello world".title())    # 'Hello World'
print("Hello".swapcase())       # 'hELLO'
print("Hello".capitalize())     # 'Hello'

# Search
print("hello world".find("world"))     # 11 (index, -1 if not found)
print("hello world".index("world"))    # 11 (raises ValueError if not found)
print("hello world".rfind("o"))         # 7 - search from the right
print("hello world".count("o"))         # 2
print("hello".startswith("he"))          # True
print("hello".endswith("lo"))            # True
print("world" in "hello world")           # True - membership test

# Split / Join
print("a,b,c".split(","))            # ['a', 'b', 'c']
print("a  b   c".split())             # ['a', 'b', 'c'] - splits on any whitespace, no empties
print("a,b,,c".split(","))            # ['a', 'b', '', 'c'] - keeps empty strings
print("a,b,c".rsplit(",", 1))         # ['a,b', 'c'] - split from the right, maxsplit
print("line1\nline2\nline3".splitlines())  # ['line1', 'line2', 'line3']
print(",".join(["a", "b", "c"]))       # 'a,b,c'
print("".join(["h", "i"]))              # 'hi'

# Replace
print("hello world".replace("world", "there"))     # 'hello there'
print("aaa".replace("a", "b", 2))                    # 'bba' - maxcount

# Predicates (is-checks)
print("abc123".isalnum())    # True
print("abc".isalpha())       # True
print("123".isdigit())        # True
print("   ".isspace())        # True
print("Hello World".istitle())  # True
print("HELLO".isupper())        # True
print("hello".islower())        # True
print("hello".isidentifier())   # True - valid Python identifier

# Padding / alignment
print("42".zfill(5))            # '00042'
print("hi".ljust(5, '-'))        # 'hi---'
print("hi".rjust(5, '-'))        # '---hi'
print("hi".center(6, '*'))        # '**hi**'

# Translation tables (fast bulk char replace)
table = str.maketrans("abc", "xyz")
print("aabbcc".translate(table))    # 'xxyyzz'

# Removing prefix/suffix (Python 3.9+)
print("test.py".removesuffix(".py"))     # 'test'
print("test.py".removeprefix("test"))    # '.py'
```

**Common interview idioms built from these methods:**

```python
# Palindrome check
def is_palindrome(s: str) -> bool:
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

print(is_palindrome("A man, a plan, a canal: Panama"))   # True

# Anagram check
def is_anagram(a: str, b: str) -> bool:
    return sorted(a.lower().replace(" ", "")) == sorted(b.lower().replace(" ", ""))

print(is_anagram("listen", "silent"))   # True

# Anagram via Counter (more efficient, O(n) vs O(n log n) for sort)
from collections import Counter
def is_anagram_fast(a: str, b: str) -> bool:
    return Counter(a) == Counter(b)

# Reverse words in a sentence
def reverse_words(s: str) -> str:
    return " ".join(reversed(s.split()))

print(reverse_words("the sky is blue"))   # 'blue is sky the'
```

## String Performance

Because strings are immutable, every "modification" allocates a new string
object and copies data. This has real performance consequences that
interviewers love to probe, especially for candidates coming from
mutable-string languages like C++/Java.

```python
# ANTI-PATTERN: O(n^2) concatenation in a loop
def build_bad(n):
    s = ""
    for i in range(n):
        s += str(i)     # each += creates a brand new string, copying all prior chars
    return s

# GOOD: O(n) using join
def build_good(n):
    parts = [str(i) for i in range(n)]
    return "".join(parts)          # single allocation, one pass to copy

# GOOD: io.StringIO for incremental building (stream-like)
import io
def build_with_stringio(n):
    buf = io.StringIO()
    for i in range(n):
        buf.write(str(i))
    return buf.getvalue()

import time
n = 20000
start = time.perf_counter()
build_bad(n)
print("concat +=:", time.perf_counter() - start)

start = time.perf_counter()
build_good(n)
print("join:", time.perf_counter() - start)
```

**Why `+=` is O(n^2) in theory (and sometimes fast in practice):**
Each `s += chunk` must allocate a new buffer of size `len(s) + len(chunk)`
and copy the entire existing content into it, because `s` cannot be resized
in place (it's immutable). Doing this `n` times, where the string grows by a
roughly constant amount each time, means total work is
`1 + 2 + 3 + ... + n = O(n^2)`.

**CPython optimization caveat:** CPython has a specific optimization for the
pattern `s = s + x` / `s += x` when the string has a reference count of 1
(i.e., nothing else refers to the old string) — in that case, CPython may
resize the string object in place via `PyUnicode_Resize`/`PyUnicode_Append`
rather than allocating fully fresh memory and copying, making single-threaded
`+=` loops in the CPython interpreter often much faster in practice than the
theoretical worst case suggests. **However, this is a CPython implementation
detail, not a language guarantee** — it doesn't apply in other
implementations (PyPy, Jython), doesn't apply if the string has other
references, and doesn't apply to `str.join`-free concatenation patterns like
`s = s + a + b + c` (creates multiple intermediates). For interviews, always
state the correct algorithmic answer: **use `str.join()` for building strings
from many pieces**, and mention the CPython optimization as a footnote, not
as a reason to write `+=` loops in code review.

**Other performance notes:**
- `str.join()` is O(n) because it first computes the total needed length by
  scanning all pieces once, allocates a single buffer, then copies each piece
  in — one allocation total.
- Comparing strings with `==` is O(n) in general but O(1) in the best case
  because CPython first checks length and (for interned strings) identity
  before doing a full character comparison.
- `in` membership tests (`substr in s`) use an efficient substring search
  (a variant of Crochemore & Perrin's "two-way" string matching algorithm in
  modern CPython), which is much faster than a naive O(n*m) approach in the
  average case.
- f-strings are generally the fastest formatting mechanism because they
  compile to direct bytecode; `%` formatting and `.format()` involve extra
  parsing/dispatch overhead at runtime.
- Avoid repeatedly slicing large strings in a loop (each slice copies) when
  an index-based or generator-based approach would avoid the copies.

## Pitfalls Summary

- Never use `is` to compare string values — always use `==`. Interning
  behavior is a CPython implementation detail and not guaranteed by the
  language spec.
- Indexing out of range raises `IndexError`; slicing out of range does not
  raise and silently clamps — don't assume slicing validates bounds.
- `str.split()` with no args collapses consecutive whitespace and strips
  leading/trailing whitespace; `str.split(",")` with an explicit separator
  does not collapse — `"a,,b".split(",")` keeps the empty string.
- `.strip(chars)` strips any combination of the given characters from both
  ends, not a substring — `"xyxhelloxyx".strip("xy")` strips all leading and
  trailing `x`/`y` characters, which surprises people expecting substring
  removal.
- String concatenation in a loop with `+=` is an anti-pattern — use
  `"".join(list_of_pieces)` instead, especially for large `n` or in library
  code where you don't control the input size.
- Always specify `encoding` explicitly when opening files or encoding/
  decoding bytes — relying on the platform default encoding causes bugs that
  only appear on certain OSes (classic Windows vs Linux discrepancy).
- Unicode-equivalent strings (different code point sequences, same visual
  glyph) can compare unequal — normalize with `unicodedata.normalize()`
  before comparing/deduplicating user-supplied text (usernames, search
  queries).
- f-strings evaluate their expressions eagerly, at the point the literal
  runs — don't use them in `logging.*` calls in hot paths where the log
  level might suppress the message; prefer the lazy `%s`-style logging API.
- `str.format()` and f-strings share the same format-spec mini-language, so
  learning one (`.2f`, `,`, `>10`, `^10`, `%`) benefits both.
- Mutable default arguments aren't a string-specific issue, but building up
  a string via a mutable default list parameter and `join`-ing later is a
  common pattern — don't forget strings themselves are always safe as
  default arguments precisely because they're immutable.
