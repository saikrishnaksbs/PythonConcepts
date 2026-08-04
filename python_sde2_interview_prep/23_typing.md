# Typing

Python is dynamically typed at runtime, but since PEP 484 (Python 3.5) it has an
optional **static type system** expressed through type hints. Type hints do not
change runtime behavior by themselves — they are metadata consumed by tools like
`mypy`, `pyright`, IDEs, and frameworks (FastAPI, Pydantic, dataclasses). For an
SDE-2 candidate, fluency in the `typing` module signals that you can write
production-grade, self-documenting, statically-checkable code that scales across
large codebases and teams — exactly what companies like Google, Amazon,
Microsoft, Atlassian, Uber, Flipkart, Walmart, and Adobe expect from mid-level+
engineers working in shared services and internal libraries.

---

## Type Hints Basics (PEP 484, Function/Variable Annotations)

### Explanation

PEP 484 introduced a syntax for annotating variables, function parameters, and
return values with type information. Annotations are stored in
`__annotations__` and are **not enforced at runtime** by the Python
interpreter — they are purely advisory unless you use a validation layer
(Pydantic) or a decorator that inspects them.

Two annotation forms:

- **Function annotations**: `def f(x: int, y: str = "a") -> bool:`
- **Variable annotations** (PEP 526): `count: int = 0` or `count: int` (no
  value, just a declaration).

### When/why to use it

- Documents intent for every parameter and return value without needing a
  docstring.
- Enables IDE autocomplete, refactoring safety, and static analysis.
- Catches an entire class of bugs (`TypeError`, `AttributeError` from wrong
  types) before code ships, via CI-gated `mypy`/`pyright` runs.
- Required in most modern Python style guides (Google Python Style Guide
  mandates type hints on public APIs).

### How mypy uses it

`mypy` performs static analysis by walking the AST, inferring types where
possible, and comparing declared/inferred types against usage. It never
executes your code. It reports mismatches such as passing a `str` where `int`
is expected, or calling a method that doesn't exist on the inferred type.

### Code example

```python
from __future__ import annotations  # postpones evaluation of annotations (PEP 563)


def greet(name: str, times: int = 1) -> str:
    """Return a greeting repeated `times` times."""
    return (f"Hello, {name}! " * times).strip()


# Variable annotations
user_count: int = 0
user_count += 1

pending_ids: list[int] = []  # PEP 585 generics without importing List

# Runtime does NOT enforce this -- this "works" even though it's wrong:
def add(a: int, b: int) -> int:
    return a + b

result = add("3", "4")  # mypy flags this; Python happily returns "34" at runtime
print(result)  # "34"
print(add.__annotations__)  # {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}
```

### Common interview questions / gotchas

- "Does Python enforce type hints at runtime?" No — they're purely advisory
  unless you add explicit runtime checks or use a library like Pydantic.
- "What is PEP 484 vs PEP 526?" 484 = function annotations; 526 = variable
  annotations syntax.
- "What does `from __future__ import annotations` do?" Makes all annotations
  strings (lazy evaluation), avoiding forward-reference errors and slightly
  improving import performance; became default behavior proposal (PEP 563,
  though its default-on rollout was later deferred/reconsidered for 3.10+).
- "How do you type-check a project in CI?" `mypy --strict` (or `pyright`) run
  as a pre-commit hook / CI gate.

### Pitfalls / common mistakes

- Assuming annotations validate input — they don't; you still need
  `isinstance` checks or a validation library for untrusted input (e.g., API
  request bodies).
- Circular import issues from importing classes purely for annotation
  purposes — solved with `from __future__ import annotations` or
  `TYPE_CHECKING` guard.
- Mixing old (`typing.List`) and new (`list[int]`) generic syntax
  inconsistently across a codebase (only matters pre-3.9 compatibility).
- Forgetting `-> None` on functions with no return value, which some strict
  configs require explicitly.

---

## Optional

### Explanation

`Optional[X]` is shorthand for `Union[X, None]` — a value that is either type
`X` or `None`. It is one of the most common annotations in real code because
`None` defaults and "not found" sentinels are everywhere.

### When/why to use it

- Function parameters with a default of `None`.
- Return types of lookup functions (`dict.get`, DB queries) that may not find
  a result.
- Forces callers to explicitly handle the `None` case, which mypy will flag
  if you use the value without a None-check (narrowing).

### How mypy uses it

mypy treats `Optional[X]` as a 2-member union. Any usage of the variable that
assumes it's non-`None` (e.g., calling a method on it) without a prior
`if x is not None:` check, `assert x is not None`, or similar narrowing
pattern raises `error: Item "None" of "Optional[X]" has no attribute "..."`.

### Code example

```python
from typing import Optional


def find_user(user_id: int, db: dict[int, str]) -> Optional[str]:
    return db.get(user_id)  # returns None if missing


def greet_user(user_id: int, db: dict[int, str]) -> str:
    name = find_user(user_id, db)
    if name is None:
        return "Unknown user"
    return f"Hello, {name}"  # mypy narrows `name` to `str` here


users = {1: "Alice", 2: "Bob"}
print(greet_user(1, users))  # Hello, Alice
print(greet_user(99, users))  # Unknown user
```

### Common interview questions / gotchas

- "What's the difference between `Optional[X]` and `X = None` as a default?"
  `Optional[X]` is a type; `= None` is a default value. You typically need
  both together: `def f(x: Optional[int] = None) -> None: ...`.
- "Is `Optional[int]` the same as `int | None`?" Yes, semantically identical;
  the latter is the PEP 604 syntax (3.10+).
- mypy will NOT auto-infer `Optional` just because a default is `None` unless
  `--no-implicit-optional`/newer mypy defaults enforce explicit
  `Optional[...]` (implicit Optional was deprecated and removed by default in
  recent mypy versions).

### Pitfalls / common mistakes

- Forgetting to narrow (`if x is None: return`) before using the value —
  mypy will catch this, but at runtime it's a live `AttributeError`/`TypeError`
  waiting to happen.
- Overusing `Optional` everywhere "just in case" instead of designing APIs
  that avoid `None` (e.g., raising an exception or returning a sentinel/empty
  collection when appropriate).
- Confusing `Optional[X]` with "optional parameter" (a parameter with a
  default value) — a parameter can have a default without being `Optional`,
  and can be `Optional` without having a default.

---

## Union (and the newer `|` syntax)

### Explanation

`Union[X, Y]` means "a value that is either type `X` or type `Y`." Since
Python 3.10 (PEP 604), you can write this more concisely as `X | Y`, which
works both in annotations and in `isinstance`-adjacent contexts.

### When/why to use it

- Functions that legitimately accept/return more than one type, e.g., a
  parser that returns `int | float`, or a function accepting `str | Path`.
- Modeling APIs where a field can be one of several JSON types.
- Encourages explicit handling of each branch (mypy forces you to narrow).

### How mypy uses it

mypy treats a `Union` as the set of member types; any operation must be valid
for *all* members unless you narrow with `isinstance`, `match`, or similar.
This is called "exhaustiveness checking" when combined with `Literal` unions.

### Code example

```python
from typing import Union


def stringify(value: Union[int, float, str]) -> str:
    if isinstance(value, str):
        return value
    return str(value)


# Python 3.10+ syntax
def parse_number(raw: str) -> int | float:
    try:
        return int(raw)
    except ValueError:
        return float(raw)


print(stringify(42))       # "42"
print(stringify(3.14))     # "3.14"
print(parse_number("10"))  # 10 (int)
print(parse_number("3.5")) # 3.5 (float)
```

### Common interview questions / gotchas

- "What's the difference between `Union[X, Y]` and `X | Y`?" Purely
  syntactic; `|` requires Python 3.10+ at runtime for actual `types.UnionType`
  objects, though `from __future__ import annotations` lets you use `|` in
  annotations on older versions too (since it's just a string then).
- "How do you narrow a Union?" `isinstance()` checks, `match` statements
  (structural pattern matching), or `Literal`-discriminated unions
  ("tagged unions").
- "What is a discriminated/tagged union?" A `Union` of `TypedDict`s or
  dataclasses that share a common `Literal` field (e.g., `type: Literal["a"]`)
  used to discriminate which branch applies.

### Pitfalls / common mistakes

- Overly broad unions (`Union[int, str, float, bytes, None]`) that push
  complexity onto every caller — often a sign the function should be split.
- Forgetting that `Union[X, X]` collapses to `X`, and `Union` order doesn't
  matter for type equivalence.
- Using `|` syntax in a function signature on Python < 3.10 at runtime
  (not just in a string annotation) causes a `TypeError` — only safe if
  annotations are lazily evaluated or you're on 3.10+.

---

## Any

### Explanation

`Any` is the universal escape hatch: a value typed `Any` is compatible with
every other type, and every other type is compatible with `Any`. It
effectively disables static checking for that value.

### When/why to use it

- Interfacing with untyped third-party libraries or dynamic data (raw JSON
  before validation).
- Gradual typing migrations — mark unfinished parts `Any` and progressively
  tighten.
- Genuinely dynamic containers (e.g., a generic cache storing arbitrary
  values) where a `TypeVar` isn't appropriate.

### How mypy uses it

mypy treats `Any` as bidirectionally compatible with everything — assigning
`Any` to `int` is fine, and vice versa, with zero warnings. This means `Any`
silently swallows type errors that flow through it, which is the tradeoff for
its convenience.

### Code example

```python
from typing import Any
import json


def load_config(path: str) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)  # JSON can be any shape


def process(data: Any) -> None:
    # No mypy error here even though this could be wrong at runtime:
    print(data.upper())  # if data is an int, this blows up at runtime


config: dict[str, Any] = {"debug": True, "retries": 3, "name": "svc"}
print(config["retries"] + 1)  # 4
```

### Common interview questions / gotchas

- "What's the difference between `Any` and `object`?" `object` is the actual
  top type — you can assign anything TO an `object`-typed variable, but you
  can't call arbitrary methods on it without narrowing (mypy enforces this).
  `Any` disables checking entirely in both directions.
- "When is `Any` an anti-pattern?" When used to silence errors instead of
  fixing them, or spread pervasively through a codebase, defeating the
  purpose of static typing.
- "How do you find where `Any` leaks in a codebase?" `mypy --disallow-any-
  expr` or `--strict` plus reviewing `reveal_type()` output.

### Pitfalls / common mistakes

- Treating `Any` as "I don't know the type" when `object` (with explicit
  narrowing) is more correct and safer.
- `Any` contamination: once a value is `Any`, everything derived from it
  becomes `Any` too, silently disabling checks downstream.
- Using `Any` to work around a genuine design problem instead of using
  `Union`, `TypeVar`, or `Protocol`.

---

## Generic

### Explanation

`Generic[T]` (from `typing`) lets you write classes and functions that are
parameterized over a type, similar to Java/C++ generics or templates. You
declare a `TypeVar` and use it as a placeholder that gets bound to a concrete
type at each usage site.

### When/why to use it

- Reusable containers/data structures: `Stack[T]`, `Cache[K, V]`, `Result[T,
  E]`.
- Preserving type information through wrapper/utility functions (e.g., a
  `first(items: list[T]) -> T` that returns the same type it was given).
- Avoids duplicating class definitions per type or falling back to `Any`.

### How mypy uses it

mypy substitutes the `TypeVar` with the concrete type used at each call site
or instantiation, and checks consistency: if `Stack[int]` is created, pushing
a `str` onto it is an error.

### Code example

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def is_empty(self) -> bool:
        return not self._items


int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
print(int_stack.pop())  # 2

# mypy would flag: int_stack.push("oops")  # Argument has incompatible type "str"


def first(items: list[T]) -> T:
    return items[0]


print(first([1, 2, 3]))        # 1, inferred as int
print(first(["a", "b", "c"]))  # "a", inferred as str
```

### Common interview questions / gotchas

- "What's a `TypeVar`, and how is it different from just using `Any`?" A
  `TypeVar` preserves the *relationship* between input and output types
  across a single call; `Any` discards type information entirely.
- "How do you bound a `TypeVar`?" `TypeVar("T", bound=SomeBaseClass)`
  restricts it to subtypes of `SomeBaseClass`; `TypeVar("T", int, str)`
  restricts it to exactly those types (constrained TypeVar).
- "What's covariance/contravariance?" `TypeVar("T_co", covariant=True)` for
  read-only producers (e.g., `Sequence[T_co]`), `contravariant=True` for
  consumers (e.g., callback parameters) — advanced but common at senior
  levels.
- Python 3.12 introduced native generic syntax: `class Stack[T]: ...` (PEP
  695), removing the need for explicit `TypeVar`/`Generic` imports.

### Pitfalls / common mistakes

- Forgetting to inherit from `Generic[T]` when using a bare `TypeVar` in a
  class (pre-3.12) — mypy will complain the class isn't generic.
- Reusing the same module-level `TypeVar` across unrelated generic classes,
  which is fine technically but confusing; convention is one `TypeVar` per
  logical purpose.
- Using a `TypeVar` when a `Protocol` or plain `Union` would be simpler — not
  every parameterized function needs full generics.

---

## Protocol

### Explanation

`Protocol` (PEP 544) enables **structural typing** ("duck typing" made
static): a class satisfies a `Protocol` if it has the right methods/attributes
regardless of inheritance. This contrasts with nominal typing (ABCs), which
require explicit subclassing.

### When/why to use it

- Defining an interface for "anything with a `.read()` method" without
  forcing implementers to inherit from a base class.
- Decoupling library code from concrete implementations — accept anything
  structurally compatible (common in dependency injection, testing/mocking).
- Matches how Python code is naturally written (duck typing) while still
  getting static checks.

### How mypy uses it

mypy checks whether a passed object's set of methods/attributes matches the
`Protocol`'s signature — no explicit `implements` or inheritance required.
This is "structural subtyping" as opposed to the "nominal subtyping" used by
regular classes/ABCs.

### Code example

```python
from typing import Protocol


class SupportsClose(Protocol):
    def close(self) -> None: ...


class FileHandle:
    def close(self) -> None:
        print("closing file")


class NetworkConnection:
    def close(self) -> None:
        print("closing connection")


def shutdown(resource: SupportsClose) -> None:
    resource.close()


shutdown(FileHandle())         # closing file
shutdown(NetworkConnection())  # closing connection
# Neither class inherits from SupportsClose -- structural typing "just works"


# runtime_checkable lets you use isinstance() with a Protocol
from typing import runtime_checkable


@runtime_checkable
class Sized(Protocol):
    def __len__(self) -> int: ...


print(isinstance([1, 2, 3], Sized))  # True
print(isinstance(42, Sized))         # False
```

### Common interview questions / gotchas

- "Protocol vs ABC — when do you use which?" `Protocol` for structural,
  retroactive interfaces (esp. across libraries you don't control); `ABC` for
  nominal typing where you want explicit registration, shared implementation
  via mixins, or `abstractmethod` enforcement at instantiation time.
- "Can you use `isinstance()` with a `Protocol`?" Only if decorated with
  `@runtime_checkable`, and even then it only checks method/attribute
  *presence*, not signatures.
- "Is `Protocol` a runtime concept?" It's primarily a static typing
  construct; runtime checks via `@runtime_checkable` are shallow (existence,
  not type-correctness of the members).

### Pitfalls / common mistakes

- Assuming `@runtime_checkable` validates argument types/signatures — it only
  checks that the named attributes/methods exist.
- Defining a `Protocol` with `...` bodies and forgetting they're not meant to
  be instantiated directly (they're interfaces).
- Confusing structural (`Protocol`) with nominal (`ABC`) typing in an
  interview — a common trap question is "does this class need to inherit
  from the Protocol?" (No.)

---

## TypedDict

### Explanation

`TypedDict` (PEP 589) lets you describe the expected shape of a `dict` (fixed
keys with specific value types), used heavily for JSON-like data (API
payloads, config dicts) where a full class/dataclass would be overkill, but a
bare `dict[str, Any]` is too loose.

### When/why to use it

- Typing JSON API request/response bodies without converting to classes.
- Config dictionaries with known keys.
- Migrating legacy dict-based code to be type-safe incrementally.

### How mypy uses it

mypy checks that dict literals or dict-typed values assigned to a
`TypedDict`-annotated variable have exactly the right keys with the right
value types (missing required keys, extra keys, or wrong types are flagged).

### Code example

```python
from typing import TypedDict, Optional


class UserDict(TypedDict):
    id: int
    name: str
    email: str


class UserDictWithOptionalBio(TypedDict, total=False):
    bio: str  # optional key, since total=False


def make_user(id: int, name: str, email: str) -> UserDict:
    return {"id": id, "name": name, "email": email}


user: UserDict = make_user(1, "Alice", "alice@example.com")
print(user["name"])  # Alice

# mypy would flag:
# bad_user: UserDict = {"id": 1, "name": "Bob"}  # missing "email"
# bad_user2: UserDict = {"id": 1, "name": "Bob", "email": "b@x.com", "extra": 1}  # extra key


# Mixed required/optional via inheritance
class PartialUser(TypedDict):
    id: int
    name: str


class FullUser(PartialUser, total=False):
    email: str  # optional


full: FullUser = {"id": 2, "name": "Carol"}  # email omitted, still valid
```

### Common interview questions / gotchas

- "TypedDict vs dataclass vs NamedTuple?" `TypedDict` is *only* a static
  typing construct over a plain `dict` — zero runtime validation, zero extra
  methods; `dataclass` and `NamedTuple` create real objects with attribute
  access, `__init__`, `__repr__`, etc.
- "Does TypedDict validate at runtime?" No — a `TypedDict` is literally just
  `dict` at runtime; you can put anything in it and Python won't complain.
  For runtime validation you need Pydantic or manual checks.
- "How do you make some keys optional?" `total=False` on the whole class, or
  split into a required base + optional subclass (as shown above), or (3.11+)
  `Required[...]`/`NotRequired[...]` per-field markers.

### Pitfalls / common mistakes

- Assuming `TypedDict` enforces anything at runtime — it's purely a mypy/IDE
  hint; `isinstance(x, UserDict)` doesn't even work as expected (it's not a
  real class you can instantiate-check against in the normal sense).
- Forgetting `total=False` and then wondering why a dict missing an optional
  key fails type checking.
- Using `TypedDict` for data that needs real behavior (methods, validation,
  immutability) — reach for `dataclass` or Pydantic `BaseModel` instead.

---

## Literal

### Explanation

`Literal[...]` restricts a value to one or more *exact* values (not just a
type), e.g., `Literal["GET", "POST", "PUT"]` or `Literal[1, 2, 3]`. It's how
you encode enums-as-strings, mode flags, and discriminant fields precisely.

### When/why to use it

- Function parameters that only accept a fixed set of string/int constants
  (HTTP methods, log levels, modes like `"r"`/`"w"`/`"a"`).
- Discriminated unions: a `Literal` field used to distinguish between
  `TypedDict`/dataclass variants in a `Union`.
- Replacing "magic strings" with statically checked, autocompletable values
  without the runtime overhead of a full `Enum` (though `Enum` is often
  preferred when you also need runtime safety).

### How mypy uses it

mypy narrows the allowed value set exactly. Passing a string not in the
`Literal` set is a static error, and mypy can perform exhaustiveness checking
on `Literal`-discriminated unions when combined with `match` statements.

### Code example

```python
from typing import Literal, Union, TypedDict

Mode = Literal["r", "w", "a", "rb", "wb"]


def open_file(path: str, mode: Mode = "r") -> None:
    print(f"opening {path} in mode {mode}")


open_file("data.txt", "r")   # fine
open_file("data.txt", "rb")  # fine
# open_file("data.txt", "x")  # mypy error: Literal["x"] not compatible with Mode


# Discriminated union pattern
class CircleShape(TypedDict):
    kind: Literal["circle"]
    radius: float


class RectShape(TypedDict):
    kind: Literal["rect"]
    width: float
    height: float


Shape = Union[CircleShape, RectShape]


def area(shape: Shape) -> float:
    if shape["kind"] == "circle":
        return 3.14159 * shape["radius"] ** 2
    return shape["width"] * shape["height"]


print(area({"kind": "circle", "radius": 2.0}))       # 12.56636
print(area({"kind": "rect", "width": 3, "height": 4}))  # 12
```

### Common interview questions / gotchas

- "Literal vs Enum — when to use which?" `Literal` for lightweight static
  constraints on primitives (esp. across API boundaries with JSON strings);
  `Enum` when you want a real runtime type with named members, iteration, and
  namespacing.
- "How does exhaustiveness checking work with Literal unions?" Using
  `match`/`if-elif` over all `Literal` branches, mypy can detect a missing
  branch if you assign the "impossible" remaining type to a variable typed
  `NoReturn` (the `assert_never` pattern from `typing_extensions`).
- "Can Literal values be non-primitive?" No — only `int`, `str`, `bytes`,
  `bool`, `Enum` members, and `None` are allowed as `Literal` arguments.

### Pitfalls / common mistakes

- Forgetting `Literal` gives zero runtime protection — passing an invalid
  string at runtime (e.g., from user input) will not raise unless you add an
  explicit check.
- Overusing `Literal` for values that will grow/change often — a bare `str`
  or `Enum` might be more maintainable than an ever-expanding `Literal` list.
- Mixing up `Literal["true"]` (the string) with `Literal[True]` (the
  boolean) — these are different types entirely.

---

## Final

### Explanation

`Final` (PEP 591) marks a variable, attribute, or method as **not to be
reassigned/overridden**. `Final[int]` on a variable means "this name should
never be rebound after first assignment." On a method, `@final` means "this
method should not be overridden in a subclass." On a class, `@final` means
"this class should not be subclassed."

### When/why to use it

- Declaring true constants (`MAX_RETRIES: Final = 3`) to prevent accidental
  reassignment.
- Locking down critical base-class methods that subclasses must not override
  (e.g., a template-method pattern's orchestration method).
- Communicating API stability guarantees in shared libraries — very relevant
  in large orgs (Amazon/Google-scale) where many teams depend on the same
  internal packages.

### How mypy uses it

mypy raises an error on any reassignment of a `Final`-annotated name, any
subclass overriding a `@final` method, or any subclassing of a `@final`
class. This is 100% static — Python itself will still let you do it at
runtime.

### Code example

```python
from typing import Final, final


MAX_RETRIES: Final[int] = 3
API_VERSION: Final = "v2"  # type inferred as str, still Final

# MAX_RETRIES = 5  # mypy error: Cannot assign to final name "MAX_RETRIES"
# (Python itself would happily allow this reassignment at runtime!)


class Base:
    @final
    def critical_setup(self) -> None:
        print("must not be overridden")


class Child(Base):
    pass
    # def critical_setup(self) -> None:  # mypy error: Cannot override final attribute
    #     print("oops")


@final
class Sealed:
    pass


# class Sub(Sealed):  # mypy error: Cannot inherit from final class "Sealed"
#     pass


print(MAX_RETRIES, API_VERSION)  # 3 v2
```

### Common interview questions / gotchas

- "Does `Final` make a variable immutable?" No — it only prevents
  *rebinding* the name. `Final[list[int]]` still lets you `.append()` to the
  list; it just prevents `x = [...]` again.
- "What's the runtime effect of `Final`?" None whatsoever — it's a
  mypy-only/static-analysis-only construct; Python will let you reassign a
  `Final` variable without any error or warning.
- "`Final` vs `const` in other languages?" Similar intent, but Python's
  `Final` is purely a linting-time contract, not enforced by the runtime or
  the bytecode compiler.

### Pitfalls / common mistakes

- Believing `Final` gives you C++ `const`-like runtime immutability — it does
  not; combine with immutable types (`tuple`, frozen `dataclass`) for actual
  immutability.
- Forgetting `@final` needs the `typing.final` decorator (method/class) while
  plain `Final` is a type annotation (for variables) — they look similar but
  serve different syntactic positions.
- Applying `Final` to a mutable default argument and assuming it protects
  against mutation bugs — it doesn't; that's a separate (in-place mutation)
  concern.

---

## Callable

### Explanation

`Callable[[ArgTypes], ReturnType]` types a function, lambda, method, or any
callable object, specifying the types of its parameters and return value.
`Callable[..., ReturnType]` (with literal ellipsis) means "any arguments."

### When/why to use it

- Typing higher-order functions: decorators, callback parameters, functions
  that accept a strategy/comparator function.
- Typing `functools.partial`, event handlers, and dependency-injected
  factories.
- Making APIs that accept "a function of this shape" self-documenting and
  statically checkable, which is common in event-driven systems, plugin
  architectures, and middleware chains (all common in backend interview
  system-design follow-ups).

### How mypy uses it

mypy checks that any function/lambda passed where a `Callable[[...], R]` is
expected has a compatible signature (parameter types are contravariant,
return type is covariant), and checks the return value's usage matches `R`.

### Code example

```python
from typing import Callable


def apply_twice(func: Callable[[int], int], value: int) -> int:
    return func(func(value))


def increment(x: int) -> int:
    return x + 1


print(apply_twice(increment, 5))          # 7
print(apply_twice(lambda x: x * 2, 3))    # 12


# Callable as a decorator return type
def logged(func: Callable[..., int]) -> Callable[..., int]:
    def wrapper(*args: object, **kwargs: object) -> int:
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


@logged
def add(a: int, b: int) -> int:
    return a + b


print(add(2, 3))  # prints "calling add" then 5


# Typing a comparator/strategy callback
def sort_by(items: list[str], key_func: Callable[[str], int]) -> list[str]:
    return sorted(items, key=key_func)


print(sort_by(["ccc", "a", "bb"], len))  # ['a', 'bb', 'ccc']
```

### Common interview questions / gotchas

- "How do you type `*args`/`**kwargs` in a Callable-consuming function?"
  Individually annotate them in the wrapper (`*args: object, **kwargs:
  object` or more specific types); `Callable[..., R]` itself can't express
  arbitrary `*args`/`**kwargs` shapes precisely — for that, use
  `ParamSpec` (PEP 612, `typing.ParamSpec`) to forward exact signatures
  through decorators.
- "Callable vs Protocol with `__call__`?" `Callable[[X], Y]` is a shorthand
  for a `Protocol` defining `__call__(self, x: X) -> Y`; use a full
  `Protocol` when the callable also needs other attributes, or when you want
  a named, reusable interface.
- "What's `ParamSpec` for?" Precisely preserving a wrapped function's full
  parameter signature through a decorator, something plain `Callable[...,
  R]` can't do.

### Pitfalls / common mistakes

- Using `Callable[..., R]` everywhere out of laziness, losing all parameter
  type checking — prefer being explicit when the signature is known.
- Forgetting that `Callable` argument types are checked contravariantly,
  which occasionally confuses people expecting simple covariant behavior in
  subtype relationships between callables.
- Not using `ParamSpec`/`Concatenate` when writing generic decorators,
  leading to the wrapped function's signature being "erased" to `Callable[...,
  Any]` for callers and IDEs.

---

## NewType

### Explanation

`NewType` creates a distinct "logical" type that is a subtype of an existing
type at the type-checker level, but is literally the same object at runtime
(zero overhead — it's just a callable identity function). It's used to
prevent mixing up semantically different values that share the same
underlying primitive type, e.g., `UserId` and `ProductId` both being `int`.

### When/why to use it

- Preventing accidental mixing of IDs/values that share a primitive type but
  represent different domain concepts (`UserId` vs `OrderId`, both `int`).
- Adding a lightweight semantic layer without the runtime cost of wrapping in
  a real class.
- Common in large-scale systems (Amazon/Uber-style microservices) where
  passing the wrong ID type into a function is a real, costly bug class.

### How mypy uses it

mypy treats `UserId` (from `NewType("UserId", int)`) as a distinct type that
is *not* interchangeable with plain `int` in the reverse direction — you can
pass a `UserId` where `int` is expected (since it "is-a" int), but not a bare
`int` where `UserId` is expected without explicit construction.

### Code example

```python
from typing import NewType

UserId = NewType("UserId", int)
ProductId = NewType("ProductId", int)


def get_user_name(user_id: UserId) -> str:
    return f"user-{user_id}"


def get_product_name(product_id: ProductId) -> str:
    return f"product-{product_id}"


raw_id = 42
user_id = UserId(raw_id)         # explicit construction, still just an int at runtime
product_id = ProductId(raw_id)

print(get_user_name(user_id))        # user-42
# get_user_name(product_id)          # mypy error: ProductId is not compatible with UserId
# get_user_name(42)                  # mypy error: int is not compatible with UserId (must wrap explicitly)

print(type(user_id))  # <class 'int'>  -- NewType has ZERO runtime cost/wrapper
print(user_id == 42)  # True, it's literally just an int
```

### Common interview questions / gotchas

- "NewType vs subclassing vs type alias — differences?" A type alias
  (`UserId = int`) is fully interchangeable with `int` (no extra safety); a
  real subclass (`class UserId(int): ...`) creates a genuinely new runtime
  type with possible behavior differences and construction overhead;
  `NewType` sits in between — static-only distinction, zero runtime cost.
- "Does NewType have any runtime behavior?" The `NewType` callable
  (`UserId(...)`) is effectively an identity function at runtime (in
  optimized builds) — it just returns its argument unchanged; the "type" only
  exists for mypy.
- "Can you subclass a NewType?" No — `NewType` cannot be used as a base for
  another `NewType` in older typing versions (this restriction has loosened
  slightly in newer Python, but it's a known gotcha to bring up).

### Pitfalls / common mistakes

- Assuming `NewType` gives runtime validation/enforcement — it does not; you
  can still pass a raw `int` in un-type-checked code paths (e.g., from
  external input) and nothing will stop you at runtime.
- Using `NewType` when what you actually want is a full value object with
  validation/behavior — a `dataclass` or Pydantic model is more appropriate
  when there's real business logic attached to the identifier.
- Forgetting to explicitly wrap raw values (`UserId(raw_id)`) at the
  boundary where the primitive first "becomes" the domain type (e.g., when
  parsing an incoming request) — inconsistent wrapping defeats the purpose.

---

## Summary Table

| Construct | Purpose | Runtime Enforced? |
|---|---|---|
| Type hints (PEP 484) | Annotate params/vars/returns | No |
| `Optional[X]` | `X` or `None` | No |
| `Union[X, Y]` / `X \| Y` | One of several types | No |
| `Any` | Disable checking for a value | N/A (no-op) |
| `Generic[T]` | Parameterize classes/functions over a type | No |
| `Protocol` | Structural interface | No (unless `@runtime_checkable`, and even then only shallow) |
| `TypedDict` | Shape of a dict | No |
| `Literal` | Exact allowed values | No |
| `Final` | Prevent reassignment/override/subclass | No |
| `Callable` | Type a function/callable | No |
| `NewType` | Distinct logical type, zero runtime cost | No (identity function at runtime) |

**The single most important takeaway for interviews**: the entire `typing`
module is a contract for static analysis tools (mypy, pyright) and IDEs.
Python's interpreter ignores annotations at runtime (aside from storing them
in `__annotations__`). If you need actual runtime validation — for untrusted
input like API request bodies — you need an additional layer such as
Pydantic, `attrs` with validators, manual `isinstance` checks, or `assert`
statements. Being able to articulate this static-vs-runtime distinction
clearly is itself a strong signal in SDE-2 interviews.
