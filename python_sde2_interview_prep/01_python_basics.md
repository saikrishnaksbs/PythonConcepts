# Python Basics

A deep, interview-focused reference covering the foundations every SDE-2 candidate is expected
to know cold: how Python came to be, what makes it distinctive as a language, how source code
actually turns into running code, and the lexical building blocks (tokens, identifiers, keywords,
comments, indentation, I/O) used to write it.

---

## Python History

### Explanation

Python was created by **Guido van Rossum** and first released in **1991**. It grew out of the
ABC language (which Guido worked on at CWI in the Netherlands) with influences from Modula-3,
C, and Unix shell scripting. The name comes from *Monty Python's Flying Circus*, not the snake.

Key milestones:

| Version | Year | Notes |
|---|---|---|
| Python 0.9.0 | 1991 | First public release; had functions, exception handling, classes with inheritance |
| Python 1.0 | 1994 | Added `lambda`, `map`, `filter`, `reduce` |
| Python 2.0 | 2000 | List comprehensions, garbage collection (cycle detector), unicode support |
| Python 3.0 | 2008 | Backward-incompatible redesign: `print` as function, integer division changes, unicode-by-default strings, `range()` returns an iterator |
| Python 2.7 EOL | Jan 1, 2020 | Python 2 officially sunset |
| Python 3.9 - 3.13 | 2020-2024 | Structural pattern matching (3.10), better error messages, performance work (Faster CPython project), free-threaded / no-GIL builds (3.13 experimental) |

Python is developed as an open-source project governed by the **Python Software Foundation (PSF)**
and changes go through **PEPs (Python Enhancement Proposals)** — e.g., PEP 8 (style guide),
PEP 20 (Zen of Python), PEP 484 (type hints), PEP 572 (walrus operator).

### Why it matters

Interviewers use this to gauge whether you understand *why* certain quirks exist (e.g., why
`print` became a function, why `/` does true division in Python 3 but `//` is floor division,
why 2-to-3 migration was such a big industry event). It also signals whether you know the
release cadence matters for which language features (e.g., `match` statement only exists 3.10+).

### Code Example

```python
import sys
import platform

# Inspecting the interpreter itself is a common "warm up" interview ask
print(sys.version)          # e.g. 3.12.3 (main, ...)
print(sys.version_info)     # sys.version_info(major=3, minor=12, micro=3, ...)
print(platform.python_implementation())  # CPython / PyPy / Jython / IronPython
```

### Common Interview Questions

- Why was Python 3 not backward compatible with Python 2? (Unicode strings by default, `print`
  as a function, integer division semantics, `xrange` -> `range`.)
- Name 3 features introduced after Python 3.8 that you actually use (walrus `:=`, positional-only
  params `/`, `match` statement, `TypedDict`, `zoneinfo`).
- What is a PEP, and can you name PEP 8 and PEP 20's purpose?
- Difference between CPython, PyPy, Jython, IronPython (implementations vs. the language spec).

### Pitfalls

- Assuming Python 2 syntax/semantics still apply (`print "x"`, old-style classes, `/` doing
  integer division for two ints).
- Confusing "Python" the language spec with **CPython** the reference implementation — most
  companies run CPython, but GIL discussions, `.pyc` details, etc. are CPython-specific, not
  language guarantees.

---

## Python Features

### Explanation

Core characteristics that interviewers expect you to be able to explain, not just list:

1. **Interpreted (and compiled to bytecode)** — Python source is compiled to an intermediate
   bytecode (`.pyc`) which is then run by the Python Virtual Machine (PVM). It's not "purely
   interpreted" line by line like a shell script, nor natively compiled like C.
2. **Dynamically typed** — variable types are checked at runtime, not compile time. A name can
   be rebound to any type (`x = 5; x = "str"` is legal).
3. **Strongly typed** — despite being dynamic, Python does not silently coerce incompatible
   types (`"2" + 2` raises `TypeError`, unlike JS's `"2" + 2 -> "22"`).
4. **High-level & garbage collected** — automatic memory management via reference counting +
   a generational cyclic garbage collector.
5. **Multi-paradigm** — supports procedural, object-oriented, and functional styles.
6. **Interpreted portability** — "write once run anywhere" the bytecode/PVM is executed by
   whichever platform's CPython build you have.
7. **Extensive standard library** — "batteries included" (`collections`, `itertools`,
   `functools`, `asyncio`, etc.).
8. **Extensible/embeddable** — C extension modules (`numpy`, `pandas` are C/Fortran under the
   hood), can embed Python in C/C++ applications.
9. **Automatic memory management** with a notable caveat: the **Global Interpreter Lock (GIL)**
   in CPython serializes execution of Python bytecode across threads in one process.
10. **Indentation-based syntax** (no braces) enforcing readability.

### Why it matters

SDE-2 interviews often probe *trade-offs*: "Python is dynamically typed — what does that cost
you at scale?" (harder to catch bugs at compile time, mitigated with type hints + `mypy`/`pyright`).
"Python has a GIL — how do you get true parallelism?" (multiprocessing, C extensions releasing
the GIL, async for I/O-bound concurrency, or `multiprocessing`/`concurrent.futures.ProcessPoolExecutor`).

### Code Example

```python
# Dynamic typing
x = 5
x = "now a string"     # legal - rebinding, not "changing the type of the variable"

# Strong typing - no implicit coercion between incompatible types
try:
    "2" + 2
except TypeError as e:
    print(f"TypeError: {e}")   # can only concatenate str (not "int") to str

# Duck typing - "if it walks like a duck and quacks like a duck..."
class Duck:
    def speak(self):
        return "Quack"

class Dog:
    def speak(self):
        return "Woof (but I can 'speak' too)"

def make_it_speak(entity):
    return entity.speak()      # no type check - just needs a .speak() method

for e in (Duck(), Dog()):
    print(make_it_speak(e))
```

### Common Interview Questions

- Is Python interpreted or compiled? (Both, in a sense — compiled to bytecode, then interpreted
  by the PVM. Not natively AOT-compiled to machine code like C/Go, though JITs like PyPy exist.)
- Dynamically typed vs. statically typed vs. strongly typed vs. weakly typed — define all four
  and place Python correctly (dynamically + strongly typed).
- What is the GIL, and why does it exist? Does it affect multiprocessing? (No — GIL is per
  process; `multiprocessing` spawns separate processes/interpreters, sidestepping it.)
- How would you achieve true parallel CPU-bound computation in Python given the GIL?
  (`multiprocessing`, `concurrent.futures.ProcessPoolExecutor`, native extensions releasing GIL,
  or Python 3.13's experimental free-threaded/no-GIL build.)
- Why is Python considered "batteries included"?

### Pitfalls

- Saying Python is "not typed" — it IS strongly typed, just dynamically (checked at runtime).
- Confusing the GIL with a general "Python can't multithread" claim — threads still help for
  I/O-bound work (network calls, disk I/O) because the GIL is released during blocking I/O.
- Thinking `.pyc` bytecode is portable machine code — it's portable across the *same major
  Python version* only, and is CPython-specific.

---

## Python Execution Model

### Explanation

Understanding what happens between running `python script.py` and seeing output is a classic
SDE-2 systems-understanding question. The CPython pipeline:

1. **Lexing (Tokenizing)** — source code (`.py`) is broken into tokens (keywords, identifiers,
   literals, operators, punctuation) by the tokenizer.
2. **Parsing** — tokens are assembled into an **Abstract Syntax Tree (AST)** according to
   Python's grammar (CPython since 3.9 uses a PEG parser).
3. **Compilation to bytecode** — the AST is compiled into **bytecode**, a low-level, portable
   set of instructions (`LOAD_FAST`, `BINARY_ADD`, `CALL_FUNCTION`, etc.) stored in `.pyc` files
   inside a `__pycache__/` directory for importable modules (not for the top-level script you
   directly run, which is compiled in-memory each time).
4. **Execution by the PVM (Python Virtual Machine)** — the bytecode is interpreted frame-by-frame
   by CPython's evaluation loop (`ceval.c`), which is a stack-based virtual machine.
5. **Memory management** — CPython uses **reference counting** as the primary GC mechanism
   (every object has an `ob_refcnt`; when it drops to 0 the object is deallocated immediately)
   plus a **generational garbage collector** to detect and collect reference cycles
   (`gc` module, 3 generations).
6. **GIL** — only one thread executes Python bytecode at a time per process, protecting
   CPython's non-thread-safe reference counting from races.

```
 source.py --(tokenizer)--> tokens --(parser)--> AST --(compiler)--> bytecode (.pyc)
                                                                          |
                                                                     PVM (ceval loop)
                                                                          |
                                                                    machine execution
```

### Why it matters

This is the "explain what happens when you run a script" question — extremely common at
Google/Amazon/Microsoft onsite loops for language-fundamentals rounds. It also underlies
performance discussions (why Python is slower than C: interpretation overhead per bytecode
instruction, dynamic type checks, boxing of ints/floats as objects).

### Code Example

```python
import dis

def add(a, b):
    return a + b

# See the actual bytecode the compiler generated
dis.dis(add)
# Output (CPython 3.11+, illustrative):
#   2           0 RESUME                   0
#               2 LOAD_FAST                0 (a)
#               4 LOAD_FAST                1 (b)
#               6 BINARY_OP                0 (+)
#              10 RETURN_VALUE

# Inspect the AST
import ast
tree = ast.parse("x = 1 + 2")
print(ast.dump(tree, indent=2))

# .pyc caching in action - import a module twice
import importlib, py_compile
py_compile.compile(__file__ if __file__.endswith('.py') else 'dummy.py', doraise=False)

# Reference counting
import sys
a = []
print(sys.getrefcount(a))   # baseline refcount (includes the temp ref from getrefcount's arg)
b = a
print(sys.getrefcount(a))   # increases by 1 - 'b' now also refs the same list
del b
print(sys.getrefcount(a))   # decreases back down
```

### Common Interview Questions

- Walk me through what happens from `python app.py` to program output.
- What is a `.pyc` file, and when does Python decide to (re)compile it? (Cached in
  `__pycache__/module.cpython-3xx.pyc`; invalidated by comparing source mtime/hash + size, or
  in Python 3.7+ optionally by hash-based invalidation, PEP 552.)
- Is Python compiled or interpreted? (Hybrid — compiled to bytecode, then interpreted.)
- What is the PVM?
- Explain reference counting and how circular references are handled (generational GC in the
  `gc` module handles cycles that pure refcounting can't free, e.g., two objects referencing
  each other with no external references).
- Why does CPython use a stack-based VM?
- What triggers the reference count of an object to be 0, and what happens then (`__del__`
  called if defined, memory freed immediately — deterministic destruction, unlike Java's GC).

### Pitfalls

- Believing every run recompiles from scratch when importing modules — the `.pyc` cache avoids
  that (though the entry-point script itself is always recompiled to bytecode in memory, just
  not cached to disk in the same way).
- Assuming reference counting alone handles all garbage — cyclic references need the generational
  collector; `gc.disable()` in perf-sensitive code can leak memory if cycles exist.
- Confusing bytecode with machine code — bytecode is still interpreted, not directly executed
  by the CPU.
- Forgetting the GIL exists only in CPython — Jython/IronPython/PyPy have different concurrency
  models (though PyPy's default GC/GIL behavior mirrors CPython closely for compatibility).

---

## Tokens

### Explanation

A **token** is the smallest individual unit of a Python program that the lexer/tokenizer
produces from raw source text — analogous to "words" in a sentence. Python's tokenizer
(`tokenize` module) classifies source into these token categories:

- **Keywords** — reserved words (`if`, `for`, `class`, `def`, ...)
- **Identifiers** — names for variables, functions, classes (`total`, `my_func`)
- **Literals** — constant values (`42`, `3.14`, `"hi"`, `True`, `None`, `b"bytes"`)
- **Operators** — `+ - * / // % ** = == != < > <= >= and or not in is & | ^ ~ << >>` etc.
- **Delimiters/Punctuators** — `( ) [ ] { } , : . ; @ = -> += -= *= ...`
- **NEWLINE / INDENT / DEDENT** — Python's tokenizer emits *structural* tokens for line breaks
  and indentation changes since Python relies on whitespace, not braces, for blocks.
- **Comments** — technically stripped/ignored by the tokenizer for execution but still tokenized
  in `tokenize` output for tools like formatters/linters.

### Why it matters

Tokens are the direct input to the parser; understanding this layer helps explain syntax errors
("unexpected token"), how `black`/`autopep8` work, and shows you understand the language isn't
"magic" — it's a well-defined grammar built from a formal token stream.

### Code Example

```python
import tokenize
import io

source = 'total = 10 + 20  # sum\n'

tokens = tokenize.generate_tokens(io.StringIO(source).readline)
for tok in tokens:
    print(tok)
# Shows TokenInfo entries: NAME 'total', OP '=', NUMBER '10', OP '+', NUMBER '20',
# COMMENT '# sum', NEWLINE, ENDMARKER
```

### Common Interview Questions

- What's the difference between a token and a lexeme? (Lexeme = the actual substring, e.g.
  `"total"`; token = the classified category + value, e.g. `NAME("total")`.)
- Are `INDENT`/`DEDENT` real tokens? (Yes — Python's grammar treats indentation changes as
  explicit tokens, unlike most C-family languages.)
- How does Python distinguish `is` (keyword/operator token) from an identifier named `is_`?
  (Exact string match against the reserved keyword list; `is_` is a different identifier.)

### Pitfalls

- Thinking whitespace inside a line is always insignificant — indentation *is* significant
  (produces INDENT/DEDENT tokens) even though spaces between tokens on the same line generally
  aren't.
- Forgetting string literal prefixes (`f`, `r`, `b`, `rb`) change how a token is lexed and later
  evaluated (e.g., `r"\n"` keeps the literal backslash-n, doesn't turn it into a newline).

---

## Variables

### Explanation

In Python, a variable is a **name bound to an object** — it is not a fixed memory box holding a
value (as in C). The name-object binding lives in a **namespace** (a dict-like mapping, e.g. a
function's local namespace, module's global namespace). Assignment (`x = 5`) creates a binding
in the current namespace pointing to the object `5` in memory; it does not "copy a value into a
box named x."

Key implications:
- Multiple names can reference the **same object** (`a = b = []` — `a` and `b` are the same list).
- Variables don't have a fixed type; only objects have types (`type(5)` is `int`).
- Python has no variable *declaration* step separate from assignment — the first assignment
  both creates the binding and initializes it.
- Scope is determined lexically: **LEGB** rule — **L**ocal, **E**nclosing, **G**lobal, **B**uilt-in.

### Why it matters

This underlies the classic "mutable default argument" bug, the difference between `is` and `==`,
and why `a = b` for mutable objects means "both names point to the same list," a very common
production bug source.

### Code Example

```python
a = [1, 2, 3]
b = a            # b now refers to the SAME list object as a
b.append(4)
print(a)         # [1, 2, 3, 4] - mutated through b, visible via a too

c = a.copy()     # or list(a) / a[:] - a new object, same contents
c.append(5)
print(a)         # unaffected: [1, 2, 3, 4]

print(id(a), id(b), id(c))     # a and b share an id; c differs
print(a is b, a is c)          # True, False

# LEGB scope demo
x = "global"

def outer():
    x = "enclosing"
    def inner():
        nonlocal x          # binds to the *enclosing* x, not global
        x = "modified by inner"
    inner()
    print(x)                # "modified by inner"

outer()
print(x)                     # "global" - module-level x untouched

# The classic mutable-default-argument pitfall
def append_item(item, bucket=[]):     # default list created ONCE at def time
    bucket.append(item)
    return bucket

print(append_item(1))   # [1]
print(append_item(2))   # [1, 2]  <-- surprise! same list reused across calls

def append_item_fixed(item, bucket=None):
    if bucket is None:
        bucket = []
    bucket.append(item)
    return bucket
```

### Common Interview Questions

- What's the difference between `is` and `==`? (`is` compares identity/memory address; `==`
  compares value via `__eq__`.)
- Explain the mutable default argument gotcha and how to fix it.
- What is the LEGB rule?
- What does `global` vs `nonlocal` do, and when would you need each?
- Explain small integer / string interning (`-5` to `256` are cached singletons in CPython, so
  `a = 5; b = 5; a is b` is `True`, but this is an implementation detail, not a language
  guarantee — never rely on `is` for value equality).

### Pitfalls

- Using `is` to compare values (should use `==`) — works "by accident" for small ints/interned
  strings, breaks for larger numbers or different string constructions.
- Not understanding that `a = b` for mutable types shares the reference, causing "spooky action
  at a distance" bugs.
- Mutable default arguments persisting state across calls.
- Shadowing builtins by naming a variable `list`, `dict`, `str`, `id`, `type`, etc.

---

## Keywords

### Explanation

Keywords are **reserved words** with fixed meaning in Python's grammar — they cannot be used as
identifiers (variable/function/class names). As of Python 3.12, the standard keyword list
(from the `keyword` module) is:

```
False      await      else       import     pass
None       break      except     in         raise
True       class      finally    is         return
and        continue   for        lambda     try
as         def        from       nonlocal   while
async      del        global     not        with
elif       if         import*    or         yield
```

(35 keywords total in modern Python 3.)

Python also has **soft keywords** — words that are only special in specific contexts and can
otherwise be used as normal identifiers: `match`, `case`, `_`, and `type` (the `type` statement
for type aliases, PEP 695, added 3.12). These are available via `keyword.softkwlist`.

### Why it matters

Interviewers check whether you know that `match`/`case` are *not* reserved everywhere (you can
still write `match = 5`), unlike true keywords like `class` or `for`. This distinction reflects
real language-design trade-offs (introducing `match` as a full keyword would've broken existing
code using `match` as a variable name — a real backward-compatibility concern at scale).

### Code Example

```python
import keyword

print(keyword.kwlist)       # full list of hard keywords
print(keyword.softkwlist)   # ['_', 'case', 'match', 'type']

print(keyword.iskeyword("class"))     # True
print(keyword.iskeyword("match"))     # False - soft keyword, not a hard one
print(keyword.issoftkeyword("match")) # True

# Soft keywords can still be used as identifiers
match = 10           # legal!
print(match)

def describe(value):
    match value:                # here 'match' is a statement keyword
        case int():
            return "integer"
        case str():
            return "string"
        case _:
            return "other"

print(describe(5), describe("hi"), describe(3.2))
```

### Common Interview Questions

- Name all the Python keywords you can recall (expect ~15-20 off the top of your head is fine;
  full recall of 35 is not usually required, but knowing categories is).
- What is a soft keyword? Give an example.
- Can you use `type` as a variable name? (Yes, `type` is a builtin, not a keyword — shadowing
  it is legal but bad practice.)
- Difference between `is`/`in`/`not` as keywords vs operators (they're both — reserved words
  that also act as operators).
- What does `async`/`await` do, and since which version are they hard keywords? (Became true
  reserved keywords in Python 3.7; before that `async`/`await` were usable as identifiers.)

### Pitfalls

- Trying to use a keyword as a variable name (`class = "Math"` -> `SyntaxError`).
- Assuming `match` is fully reserved and refusing to use it as a variable name unnecessarily.
- Confusing keywords (grammar-level reserved words) with builtins (`print`, `len`, `type` —
  ordinary names in the builtins namespace that CAN be shadowed, though you shouldn't).

---

## Identifiers

### Explanation

An **identifier** is the name used for a variable, function, class, module, or other object.
Rules for valid identifiers in Python:

1. Must start with a letter (`A-Z`, `a-z`) or underscore `_` — **not** a digit.
2. Subsequent characters can be letters, digits (`0-9`), or underscores.
3. Cannot be a (hard) keyword.
4. Case-sensitive (`Value` != `value`).
5. Since Python 3, identifiers support full **Unicode** (not just ASCII) per PEP 3131 — e.g.,
   `变量 = 10` or `café = "coffee"` are legal, though ASCII is the practical convention for
   shared codebases.
6. No length limit.

Naming conventions (PEP 8, frequently asked):
- `snake_case` for variables/functions.
- `PascalCase`/`CapWords` for classes.
- `UPPER_SNAKE_CASE` for constants.
- Leading single underscore `_var` — convention for "internal use" (not enforced).
- Leading double underscore `__var` — triggers **name mangling** inside classes
  (`__var` becomes `_ClassName__var`), used to avoid subclass attribute clashes.
- Leading and trailing double underscore `__var__` — "dunder"/magic methods reserved by
  the language (`__init__`, `__str__`); avoid inventing your own dunder names.
- Single underscore `_` — conventionally a "throwaway" variable.

### Why it matters

Understanding name mangling is a real gotcha in OOP interview questions (private attribute
access, subclassing). PEP 8 conventions are checked in code review rounds at every major tech
company.

### Code Example

```python
# Valid identifiers
_private = 1
value2 = 2
CONSTANT_VALUE = 3
café = "coffee"          # unicode identifier, legal but unconventional

# Invalid identifiers (would raise SyntaxError if uncommented)
# 2value = 5            # cannot start with digit
# my-var = 5             # hyphen not allowed
# class = 5              # keyword

# Name mangling demo
class Base:
    def __init__(self):
        self.__secret = "base secret"     # becomes self._Base__secret

    def reveal(self):
        return self.__secret

class Child(Base):
    def __init__(self):
        super().__init__()
        self.__secret = "child secret"    # becomes self._Child__secret - NO collision

c = Child()
print(c.reveal())              # "base secret" - Base's method sees Base's mangled name
print(vars(c))
# {'_Base__secret': 'base secret', '_Child__secret': 'child secret'}
```

### Common Interview Questions

- What are the rules for valid Python identifiers?
- What is name mangling and why does it exist? (Avoids accidental override of "private"
  attributes by subclasses; it's obfuscation, not true privacy.)
- Difference between `_var`, `__var`, and `__var__`.
- Is Python case-sensitive? Give an example of a bug caused by assuming otherwise.
- Can identifiers contain unicode characters? Should you use that in production code?

### Pitfalls

- Assuming `__var` makes an attribute truly private/inaccessible — it's still reachable via
  `obj._ClassName__var`, just discouraged.
- Using leading underscores expecting enforced access control (Python has convention, not
  enforcement, for privacy).
- Naming a variable the same as a builtin (`str`, `list`, `id`) — shadows the builtin in that
  scope, causing confusing `TypeError`s later in the same scope.

---

## Comments

### Explanation

Comments are non-executable annotations for human readers, stripped out at the tokenizer level
(they don't produce bytecode). Python has:

- **Single-line comments**: start with `#` and run to end of line.
- **No native multi-line comment syntax** — the common workaround is a triple-quoted string
  literal (`"""..."""`) not assigned to anything, which is technically a *string expression
  statement*, not a true comment (it still gets evaluated as an expression, though CPython
  optimizes away unused constant expression statements in most cases; it does still consume a
  small amount of parse tree/bytecode versus real comments in edge cases).
- **Docstrings** — a triple-quoted string as the *first statement* in a module, class, function,
  or method. Unlike comments, docstrings are **retained at runtime** and accessible via
  `__doc__`, and consumed by tools like `help()`, Sphinx, and IDEs.
- **Shebang line**: `#!/usr/bin/env python3` — first line of a script, tells Unix shells which
  interpreter to use; from Python's perspective it's just a regular `#` comment.
- **Encoding declaration**: `# -*- coding: utf-8 -*-` — a special comment recognized by the
  parser to set source encoding (rarely needed now since UTF-8 is default since Python 3).

### Why it matters

Distinguishing comments (compile-time-discarded) from docstrings (runtime-accessible objects)
is a common trick question. It also opens discussion of tooling — linters flag missing
docstrings, `pydoc`/`help()` relies on them, type checkers can read docstring-embedded types
(older style) vs. PEP 484 annotations.

### Code Example

```python
# This is a single-line comment - ignored entirely by the compiler

def greet(name):
    """Return a friendly greeting for `name`.

    This is a docstring: unlike a comment, it becomes the function's
    __doc__ attribute and is available at runtime.
    """
    return f"Hello, {name}!"

print(greet.__doc__)
help(greet)

"""
This triple-quoted string is NOT assigned to a variable and NOT in a
docstring position (not the first statement of a module/function/class),
so it's commonly used as a 'block comment' - but it IS technically a
string literal expression statement evaluated (then discarded) at runtime.
"""

import dis
def f():
    "just a doc"       # docstring, becomes f.__doc__
    x = 1
    return x

dis.dis(f)   # notice there's no bytecode instruction for a plain '#' comment at all
```

### Common Interview Questions

- Does Python support multi-line comments natively? (No — only `#` per line; triple-quoted
  strings are a convention, not a real comment.)
- What's the difference between a comment and a docstring?
- How do you access a function's docstring programmatically? (`func.__doc__` or `help(func)`.)
- Do comments affect performance / bytecode size? (No, stripped at tokenization; a stray
  unused triple-quoted string literal statement, unlike a `#` comment, does technically produce
  a `LOAD_CONST`/`POP_TOP` in older Python versions, though modern CPython peephole-optimizes
  simple constant expression statements — the key interview point is that it's NOT a true
  comment even if visually similar.)
- What does the shebang line do and does Python care about it?

### Pitfalls

- Using triple-quoted strings as "multi-line comments" inside a function body and assuming zero
  runtime cost / that it becomes a docstring — only the *first* statement in a def/class/module
  is a docstring; any other triple-quoted string is just a discarded expression statement.
- Forgetting to keep docstrings updated — stale docs mislead `help()` users and API consumers.
- Writing comments that explain "what" instead of "why" (a common code-review nitpick, and
  sometimes explicitly asked about in interviews on code quality).

---

## Indentation

### Explanation

Python uses **indentation** (whitespace at the start of a line) to delimit code blocks, instead
of braces `{}` (C, Java) or `begin/end` keywords. This is enforced by the grammar itself — the
tokenizer emits `INDENT` and `DEDENT` tokens when indentation increases or decreases, and the
parser requires consistent indentation within a block.

Rules:
- All statements within the same block must be indented at the **same level**.
- The standard/PEP 8-recommended indentation is **4 spaces** per level.
- Mixing **tabs and spaces** is disallowed in Python 3 for ambiguous cases — CPython raises a
  `TabError` if the indentation can't be unambiguously reconciled.
- Indentation errors raise `IndentationError` (a subclass of `SyntaxError`), caught at compile
  time before any code runs.
- Blank lines and comment-only lines don't affect the indentation stack.

### Why it matters

Indentation-based syntax is Python's most visually distinguishing feature and a frequent
"gotcha" source for engineers coming from brace languages, especially around copy-pasted code
from mismatched sources (mixed tabs/spaces), and inconsistent editors. It also intersects with
version-control diffs (auto-formatters like `black` normalize indentation) and is why linters
flag mixed tabs/spaces early.

### Code Example

```python
def classify(n):
    if n > 0:
        result = "positive"      # 8 spaces - nested block under if
    elif n < 0:
        result = "negative"
    else:
        result = "zero"
    return result                # 4 spaces - back at function body level

print(classify(5), classify(-2), classify(0))

# IndentationError example (would raise if run):
# def broken():
#     x = 1
#       y = 2      # IndentationError: unexpected indent

# Inconsistent indentation across a block (would raise):
# if True:
#     a = 1
#      b = 2       # IndentationError: unindent does not match any outer indentation level
```

```python
# Demonstrating that indentation depth (as long as consistent within a block) is developer's
# choice, though PEP 8 mandates 4 spaces:
if True:
  x = 1        # 2 spaces - legal but not PEP 8 compliant
  if True:
      y = 2    # 6 spaces here - inconsistent style but still legal since it's a NEW block
  print(x, y)
```

### Common Interview Questions

- Why did Guido choose indentation over braces? (Enforces readability; "what you see is what
  you get" — removes the C/Java class of bugs where indentation visually suggests one block
  structure but braces define another.)
- What's the difference between `IndentationError` and `SyntaxError`? (`IndentationError` is a
  subclass of `SyntaxError` specifically for indentation issues.)
- Can you mix tabs and spaces in Python 3? (No — raises `TabError` when ambiguous; Python 2
  allowed it with heuristics, a notorious source of Python 2 bugs.)
- What happens if you use inconsistent indentation levels in the same block?

### Pitfalls

- Mixing tabs and spaces (especially when copy-pasting from Stack Overflow/Slack/docs) —
  causes `TabError`/`IndentationError` that can be invisible in some editors.
- Assuming indentation size must be exactly 4 spaces everywhere — Python only requires
  *consistency within a block*; 4 spaces is a PEP 8 convention, not a language rule.
- Editors auto-converting tabs to spaces inconsistently across a team, causing diff noise and
  intermittent errors.
- Single-line compound statements (`if True: x = 1`) — legal but discouraged by PEP 8 as it
  hides block structure.

---

## Input/Output

### Explanation

**Input** — the builtin `input([prompt])` function:
- Reads a line from `stdin`, strips the trailing newline, and **always returns a `str`**,
  regardless of what the user types. Any numeric conversion must be done explicitly
  (`int(input())`, `float(input())`), and can raise `ValueError` on bad input.
- Blocks execution until Enter is pressed (or EOF, which raises `EOFError`).

**Output** — the builtin `print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False)`:
- `sep` — string inserted between multiple positional arguments (default single space).
- `end` — string appended after the last argument (default newline; set to `''` to suppress).
- `file` — a writable stream (`sys.stdout` default; can redirect to `sys.stderr`, a file object,
  or `io.StringIO`).
- `flush` — forces the output buffer to be written immediately instead of waiting for the
  buffer to fill or the program to exit (important for real-time logs / progress bars, and for
  ensuring ordering when mixing `print` with other output mechanisms like subprocess output).

String formatting for output (frequently tested):
- **f-strings** (3.6+, preferred): `f"{value:.2f}"` — fastest, most readable, supports `=` debug
  specifier (3.8+: `f"{value=}"`).
- **`str.format()`**: `"{}".format(value)` — older, still common in codebases.
- **`%` formatting**: `"%s" % value` — legacy C-style, still seen in logging (`logging` module
  historically recommends `%s` for lazy evaluation reasons).

### Why it matters

Type coercion from `input()` is one of the most common beginner-to-intermediate bugs shown up
in interviews when candidates forget to cast input before arithmetic. `print`'s `sep`/`end`/
`flush` parameters come up in "format this output exactly" style questions and in
concurrency/logging discussions (`flush=True` for real-time visibility in Docker/CI logs).

### Code Example

```python
# input() always returns a string
name = input("Enter your name: ")        # e.g. user types "Alice"
print(type(name))                        # <class 'str'>

age_str = input("Enter your age: ")
age = int(age_str)                       # explicit conversion required
print(f"{name} is {age + 1} next year")  # f-string formatting

# print() formatting options
print("a", "b", "c")                       # a b c            (default sep=' ')
print("a", "b", "c", sep=", ")             # a, b, c
print("a", "b", "c", sep="")               # abc
print("no newline", end="")                # suppresses trailing \n
print(" -- appended on same line")

import sys
print("error!", file=sys.stderr)           # redirect to stderr

print("streaming...", end="", flush=True)  # force immediate write, bypass buffering

# f-string features
pi = 3.14159265
print(f"{pi:.2f}")            # 3.14 - fixed 2 decimal places
print(f"{pi = }")             # pi = 3.14159265 (Python 3.8+ debug specifier, keeps spaces as typed)
value = 255
print(f"{value:#x}")          # 0xff - hex formatting
print(f"{value:>10}")         # right-align in width 10

# Reading multiple values from one line
raw = input("Enter two numbers separated by space: ")   # e.g. "3 4"
a, b = map(int, raw.split())
print(a + b)
```

### Common Interview Questions

- Does `input()` ever return anything other than a `str`? (No — always `str`; you must cast.)
- What exception does `input()` raise on EOF (e.g., piped input runs out, Ctrl+D)?
  (`EOFError`.)
- Explain `print`'s `sep`, `end`, and `flush` parameters with examples.
- Why would you set `flush=True` explicitly? (Output buffering — when stdout is redirected to a
  file/pipe, Python typically fully buffers rather than line-buffers, so `print` output can lag
  behind real time unless flushed; matters for progress indicators, logs tailed in real time,
  and interleaving output with subprocess/thread output.)
- f-strings vs `.format()` vs `%` — which is preferred and why? (f-strings: fastest at runtime
  since evaluated at compile-time into efficient bytecode, most readable, supports inline
  expressions and the `=` debug specifier.)
- How do you print without a trailing newline?
- How do you read multiple space-separated integers from one line efficiently? (`map(int,
  input().split())`.)

### Pitfalls

- Forgetting to convert `input()` output before doing arithmetic (`input() + 1` raises
  `TypeError: can only concatenate str`).
- Not handling `ValueError` from `int(input())` when the user enters non-numeric text.
- Assuming `print` flushes immediately by default — in non-interactive contexts (piped/redirected
  output) Python may fully buffer stdout, delaying visibility, especially relevant in CI logs or
  Docker containers where output appears to "hang" then dump all at once.
- Using f-strings with an old Python version (`f"{x=}"` requires 3.8+; f-strings themselves
  require 3.6+) — a real compatibility issue in codebases supporting older interpreters.
- Using mutable/expensive expressions inside f-strings repeatedly in a hot loop without
  realizing they re-evaluate every time the f-string is constructed.

---

## Summary Checklist for SDE-2 Interviews

- Explain the full pipeline: source -> tokens -> AST -> bytecode -> PVM execution.
- Know CPython's memory model: reference counting + generational GC for cycles, and the GIL's
  role/impact on concurrency.
- Be precise about typing: Python is dynamically **and** strongly typed.
- Know the difference between hard keywords and soft keywords (`match`, `case`, `_`, `type`).
- Understand identifier rules and name mangling (`__attr` -> `_ClassName__attr`).
- Distinguish comments (compile-time discarded) from docstrings (runtime-accessible `__doc__`).
- Know indentation is enforced via `INDENT`/`DEDENT` tokens, and `IndentationError`/`TabError`
  are `SyntaxError` subclasses raised before any code executes.
- Know `input()` always returns `str`, and be fluent in `print()`'s `sep`/`end`/`file`/`flush`
  and f-string formatting mini-language.
