# Advanced OOP

This module covers the object-oriented Python features that separate SDE-2
candidates from beginners: abstract base classes, metaclasses, descriptors,
properties, `__slots__`, dataclasses, protocols, and generics. Interviewers
at Google, Amazon, Microsoft, Atlassian, Uber, Flipkart, Walmart, and Adobe
use these topics to probe whether you understand Python's object model
deeply enough to design libraries, frameworks, and APIs, not just call them.

---

## 1. Abstract Base Classes (ABCs)

### Explanation

An Abstract Base Class defines an interface that subclasses must implement.
Python provides the `abc` module with `ABC` (a convenience base class) and
`ABCMeta` (the metaclass that actually enforces abstractness). Methods
decorated with `@abstractmethod` must be overridden in any concrete
subclass; Python refuses to instantiate a class that still has unimplemented
abstract methods.

Internally, `ABCMeta.__new__` collects all methods marked with
`__isabstractmethod__ = True` (set by the `@abstractmethod` decorator) into
a frozenset stored as `cls.__abstractmethods__`. When you call `MyClass()`,
`object.__new__` (via cooperation with `ABCMeta`) checks whether
`__abstractmethods__` is non-empty, and raises `TypeError` if so. This is
enforced at instantiation time, not at class-definition time.

`abc` also supports virtual subclassing via `register()`, and abstract
properties/classmethods/staticmethods via stacking decorators
(`@property` + `@abstractmethod`).

### Why it matters for SDE-2 interviews

- Demonstrates you can design contracts/interfaces for pluggable systems
  (e.g., payment gateways, storage backends, notification channels) — a
  very common system-design-adjacent coding question.
- Companies building SDKs (AWS/Azure-style client libraries) and internal
  platforms (Uber's dispatch strategies, Flipkart's pricing engines) rely on
  ABCs to define swappable strategy implementations (Strategy pattern).
  Interviewers want to see you reach for ABC instead of "just document it
  and hope."
- Shows you understand duck typing's limits and when to formalize a contract.

### Code example

```python
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """Interface every concrete payment gateway must implement."""

    @abstractmethod
    def charge(self, amount: float) -> str:
        """Charge the given amount, return a transaction id."""
        raise NotImplementedError

    @abstractmethod
    def refund(self, transaction_id: str) -> bool:
        raise NotImplementedError

    def summary(self) -> str:
        # Concrete (non-abstract) method — shared by all subclasses.
        return f"{self.__class__.__name__} gateway"


class StripeGateway(PaymentGateway):
    def charge(self, amount: float) -> str:
        return f"stripe-txn-{amount}"

    def refund(self, transaction_id: str) -> bool:
        print(f"Refunding {transaction_id} via Stripe")
        return True


if __name__ == "__main__":
    # PaymentGateway()  # TypeError: Can't instantiate abstract class
    gw = StripeGateway()
    print(gw.charge(42.5))
    print(gw.summary())

    # Abstract property example
    class Shape(ABC):
        @property
        @abstractmethod
        def area(self) -> float:
            ...

    class Square(Shape):
        def __init__(self, side):
            self.side = side

        @property
        def area(self) -> float:
            return self.side ** 2

    print(Square(4).area)
```

### Common interview questions / gotchas

- "What happens if you try to instantiate a class with unimplemented
  abstract methods?" — `TypeError` at instantiation, not import time.
- "Can an ABC have concrete methods?" — Yes; only methods marked
  `@abstractmethod` must be overridden.
- "How do you make an abstract *property* or abstract *classmethod*?" —
  Stack `@property`/`@classmethod` above `@abstractmethod`.
- "What's `register()` and virtual subclassing?" — Lets you declare a class
  as a subclass of an ABC without inheriting from it, so
  `isinstance(x, ABC)` returns True (used by `collections.abc`).
- "ABC vs Protocol — when do you use which?" — ABC = nominal typing
  (explicit inheritance); Protocol = structural typing (duck typing).

### Pitfalls / common mistakes

- Forgetting `ABC` in the base classes tuple (or not using `ABCMeta`
  directly) — then `@abstractmethod` is decorative only and does nothing.
- Overriding `__init__` in a subclass and forgetting `super().__init__()`,
  silently skipping base-class setup.
- Believing abstract methods can't have a body — they can, and subclasses
  can call it via `super().charge(...)` for shared logic.
- Assuming ABC enforcement happens at class definition time — it only
  happens when you attempt to instantiate.

---

## 2. Metaclasses

### Explanation

A metaclass is "the class of a class." Just as an object is an instance of
a class, a class is an instance of its metaclass — by default `type`.
Defining `class Foo(metaclass=Meta): ...` tells Python to build `Foo` by
calling `Meta(name, bases, namespace)` instead of the default `type(...)`.

The class-creation pipeline is:

1. Python collects the class body into a namespace dict (optionally via
   `Meta.__prepare__` if defined, which lets you control the namespace type,
   e.g., an `OrderedDict` for field ordering).
2. `Meta.__new__(mcls, name, bases, namespace)` creates the class object
   itself. This is where you can inspect/rewrite attributes, inject
   methods, validate the class body, register the class in a registry, etc.
3. `Meta.__init__(cls, name, bases, namespace)` runs after the class object
   exists, for further initialization.
4. Metaclasses participate in MRO like any other type; Python computes
   `type(Foo)` following the C3 linearization the same way instance-level
   `__class__` lookups do.

`__new__` vs `__init__` on a metaclass: `__new__` returns (and can replace)
the class object being created — use it when you need to mutate the
namespace *before* the class exists (e.g., renaming attributes, adding
`__slots__`). `__init__` receives the already-created class — use it for
side effects that need the finished class (e.g., registering it in a
dict).

Common real-world use cases:
- ORMs (Django/SQLAlchemy-style): a `ModelMeta` metaclass scans class-level
  field declarations (`name = CharField()`) and converts them into a schema
  descriptor, builds `_meta`, wires up a table name, etc.
- Singleton enforcement: override `__call__` on the metaclass to return the
  same instance every time.
- API registries/plugin systems: automatically register every subclass in
  a global dict as it's defined.
- Enforcing coding standards: e.g., requiring every method be documented,
  or preventing multiple inheritance.

### Why it matters for SDE-2 interviews

- Framework-heavy shops (Adobe's internal Python tooling, Uber's service
  scaffolding, Flipkart/Walmart's internal ORildlike layers) use metaclasses
  under the hood; being able to explain "how does Django's `Model` class
  turn `name = CharField()` into a DB column" is a strong signal of depth.
  You don't need to write metaclasses daily, but you must understand them
  to debug frameworks that use them.
- Tests whether you understand Python's object model beyond
  "classes are just templates" — a favorite differentiator question at
  Google/Microsoft-style interviews ("what is `type(type)`?").

### Code example

```python
# --- 1. type() as a metaclass, used directly ---
Dog = type("Dog", (), {"bark": lambda self: "Woof!"})
print(Dog().bark())


# --- 2. Custom metaclass: auto-registering plugin classes ---
class PluginMeta(type):
    registry = {}

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if bases:  # don't register the base class itself
            PluginMeta.registry[name] = cls
        return cls


class BasePlugin(metaclass=PluginMeta):
    pass


class CsvExporter(BasePlugin):
    def export(self):
        return "csv"


class JsonExporter(BasePlugin):
    def export(self):
        return "json"


print(PluginMeta.registry)  # {'CsvExporter': ..., 'JsonExporter': ...}


# --- 3. Singleton via metaclass __call__ ---
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigManager(metaclass=SingletonMeta):
    def __init__(self):
        self.settings = {}


a = ConfigManager()
b = ConfigManager()
print(a is b)  # True


# --- 4. Minimal ORM-style field-collecting metaclass ---
class Field:
    def __init__(self, field_type):
        self.field_type = field_type


class ModelMeta(type):
    def __new__(mcls, name, bases, namespace):
        fields = {
            key: val for key, val in namespace.items() if isinstance(val, Field)
        }
        namespace["_fields"] = fields
        return super().__new__(mcls, name, bases, namespace)


class Model(metaclass=ModelMeta):
    pass


class User(Model):
    name = Field(str)
    age = Field(int)


print(User._fields.keys())  # dict_keys(['name', 'age'])
```

### Common interview questions / gotchas

- "What is `type(type)`?" — `type` (it's its own metaclass, the fixed point
  of the class hierarchy).
- "What's the difference between `__new__` and `__init__` on a metaclass?"
  — `__new__` builds/returns the class object (can mutate namespace before
  creation); `__init__` configures the already-created class.
- "How would you implement a Singleton in Python — name two ways?" —
  Metaclass `__call__` override, or a module-level instance, or
  `functools.lru_cache` on a factory function, or `__new__` override on the
  class itself.
- "Why might Django use a metaclass instead of `__init_subclass__`?" —
  Historical reasons (Django predates `__init_subclass__`, added in 3.6);
  today `__init_subclass__` covers many simpler "run code when a subclass
  is defined" use cases without the complexity of a full metaclass.
- "Metaclass vs class decorator — when would you pick one over the other?"
  — Class decorators are simpler and composable but can't affect
  inheritance (a decorator only runs once on the class it wraps, not on its
  subclasses); metaclasses propagate through the whole hierarchy.

### Pitfalls / common mistakes

- Reaching for a metaclass when `__init_subclass__` or a simple class
  decorator would do — metaclasses are hard to compose (two unrelated
  metaclasses on your bases cause `TypeError: metaclass conflict`).
- Forgetting `super().__new__` / `super().__init__` calls, breaking
  cooperative multiple inheritance.
- Confusing instance-level `__call__` (calling an instance of a class) with
  metaclass-level `__call__` (calling the class itself, i.e.,
  instantiation) — this confusion is exactly what makes the Singleton
  pattern above work, and exactly what trips people up when reading it.
- Mutating `namespace` in `__new__` in a way that breaks
  `super().__new__()`'s expectations (e.g., removing dunder keys it needs).

---

## 3. Descriptors

### Explanation

A descriptor is any object whose class defines one or more of `__get__`,
`__set__`, or `__delete__`. When such an object is stored as a *class*
attribute, attribute access on instances is routed through these methods
instead of the normal instance `__dict__` lookup.

- **Data descriptor**: defines `__set__` and/or `__delete__` (with or
  without `__get__`). Data descriptors take priority over the instance
  `__dict__` — `instance.attr` invokes the descriptor even if
  `instance.__dict__['attr']` exists.
- **Non-data descriptor**: defines only `__get__`. Instance `__dict__`
  takes priority over non-data descriptors. This is how plain functions
  become bound methods: functions implement `__get__` (making them
  non-data descriptors), so `instance.method` returns a bound method, but
  if you put a value directly in `instance.__dict__['method']` it wins.

**Descriptor protocol lookup order** for `instance.attr`
(`type.__getattribute__`, simplified):
1. Look up `attr` in `type(instance).__mro__`. If found and it is a *data*
   descriptor, call `descriptor.__get__(instance, type(instance))` and
   return that — instance `__dict__` is not even consulted.
2. Otherwise look in `instance.__dict__`. If found, return it.
3. Otherwise, if the class-level `attr` was found in step 1 and is a
   *non-data* descriptor, call its `__get__`.
4. Otherwise, if the class-level `attr` was found and is a plain (non-
   descriptor) value, return it directly.
5. Otherwise raise `AttributeError` (possibly resolved via `__getattr__`).

`property` is itself implemented as a data descriptor: `property.__get__`
calls your getter function, `property.__set__` calls your setter (raising
`AttributeError` if none was provided), and `property.__delete__` calls
your deleter.

### Why it matters for SDE-2 interviews

- Descriptors are the mechanism behind `property`, methods, `staticmethod`,
  `classmethod`, and ORM fields (Django's `CharField`, SQLAlchemy columns).
  Explaining "how does `@property` actually work under the hood" is a
  classic Google/Amazon deep-dive follow-up after a candidate casually uses
  `@property`.
- Validated/typed attributes (e.g., a `PositiveInt` descriptor reused
  across many model classes) are a real pattern in production code at
  companies with large data-model codebases (Walmart, Flipkart catalog
  systems) to avoid repeating validation logic in every `__init__`.

### Code example

```python
class PositiveNumber:
    """A reusable data descriptor enforcing value > 0."""

    def __set_name__(self, owner, name):
        # Called automatically when the descriptor is assigned in a class body.
        self.name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self  # accessed on the class itself, e.g. Product.price
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"{self.name[1:]} must be positive, got {value}")
        setattr(instance, self.name, value)

    def __delete__(self, instance):
        delattr(instance, self.name)


class Product:
    price = PositiveNumber()
    quantity = PositiveNumber()

    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity


p = Product(10.0, 5)
print(p.price, p.quantity)
try:
    p.price = -5
except ValueError as e:
    print("Rejected:", e)


# --- Non-data descriptor: how bound methods work ---
class Greeter:
    def hello(self):
        return "hi"


g = Greeter()
print(type(Greeter.__dict__["hello"]))       # <class 'function'>
print(type(g.hello))                          # <class 'method'> (bound via __get__)
g.__dict__["hello"] = lambda: "overridden"    # instance dict wins (non-data descriptor)
print(g.hello())                              # 'overridden'


# --- property is a data descriptor ---
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def area(self):
        return 3.14159 * self._radius ** 2


c = Circle(2)
print(c.area)
print(isinstance(type(c).area, property))  # True
print(hasattr(type(c).area, "__set__"))    # True -> data descriptor
```

### Common interview questions / gotchas

- "What's the difference between a data descriptor and a non-data
  descriptor, and why does it matter?" — Priority order relative to
  instance `__dict__`.
- "How does `instance.method()` become a bound call?" — Functions define
  `__get__`, making them non-data descriptors; accessing via an instance
  binds `self`.
- "Implement a validated attribute descriptor reusable across classes." —
  Exactly the `PositiveNumber` example above.
- "What does `__set_name__` do and when was it added?" — Lets a descriptor
  learn the attribute name it was assigned to, without repeating the name
  as a string; added in Python 3.6 (PEP 487).
- "Why does `instance.__dict__['x'] = 5` not override a `property` named
  `x`?" — Because `property` is a data descriptor, so it wins over
  instance `__dict__`.

### Pitfalls / common mistakes

- Storing per-instance state directly on the descriptor instance (`self.value
  = value` inside `__set__`) instead of on the *instance* — this leaks
  state across all instances sharing that one descriptor object, since the
  descriptor itself is a single class-level object.
- Forgetting the `if instance is None: return self` guard in `__get__`,
  which breaks class-level access (`Product.price`) used for introspection.
- Not handling `__set_name__` and hardcoding attribute names, making the
  descriptor non-reusable.
- Assuming any object with `__get__` blocks instance `__dict__` — only true
  for descriptors that also define `__set__`/`__delete__`.

---

## 4. Properties

### Explanation

`@property` turns a method into a computed attribute accessed without
parentheses. It's syntactic sugar over the descriptor protocol: `property`
is a built-in class whose `__init__` takes `fget`, `fset`, `fdel`, and
`__doc__`, and whose `__get__`/`__set__`/`__delete__` dispatch to them.

```
@property
def x(self): ...       # defines fget, wraps into a property object
@x.setter
def x(self, value): ... # returns a NEW property object with fset added
@x.deleter
def x(self): ...
```

Each of `.setter`/`.deleter` doesn't mutate the property in place — it
returns a new `property` object copying the existing getter/deleter and
adding the new function, then rebinds the class attribute `x` to it.

Use properties for:
- Computed/derived attributes (e.g., `area` from `radius`).
- Validation on assignment without changing the public API.
- Lazy computation with caching (combine with manual caching or
  `functools.cached_property`).
- Maintaining backward compatibility: converting a plain attribute into a
  property later without breaking callers who do `obj.x` or `obj.x = 5`.

### Why it matters for SDE-2 interviews

- Nearly universal — expected baseline knowledge, but interviewers use it
  to segue into "how is this implemented" (descriptors) to gauge depth.
- API-design signal: knowing when to expose a property vs. a plain
  attribute vs. a method shows judgment valued in code review at any of
  these companies.

### Code example

```python
class Temperature:
    def __init__(self, celsius=0.0):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("Below absolute zero!")
        self._celsius = value

    @celsius.deleter
    def celsius(self):
        print("Resetting to 0")
        self._celsius = 0.0

    @property
    def fahrenheit(self):
        # Computed / read-only attribute, no setter defined.
        return self._celsius * 9 / 5 + 32


t = Temperature(25)
print(t.celsius, t.fahrenheit)
t.celsius = 100
print(t.fahrenheit)

try:
    t.fahrenheit = 50  # AttributeError: can't set attribute
except AttributeError as e:
    print("Error:", e)

del t.celsius
print(t.celsius)


# functools.cached_property: computed once, then cached on the instance
from functools import cached_property
import time


class Report:
    def __init__(self, rows):
        self.rows = rows

    @cached_property
    def total(self):
        print("Computing total...")
        time.sleep(0.1)
        return sum(self.rows)


r = Report([1, 2, 3])
print(r.total)  # Computing total...
print(r.total)  # cached, no recompute
```

### Common interview questions / gotchas

- "How do you make a read-only computed attribute?" — Define only
  `@property` with no setter; assignment raises `AttributeError`.
- "How is `@property` implemented?" — Via the descriptor protocol (see
  Descriptors section).
- "`cached_property` vs `property` — difference and gotcha?" —
  `cached_property` stores the result in the instance `__dict__` after
  first access (so it requires the class NOT use `__slots__` unless
  `__slots__` includes `__dict__`), and does not re-run when the underlying
  data changes, unlike a plain `property` which recomputes every access.
- "Why prefer a property over exposing a public method
  `get_x()`/`set_x()` (Java-style)?" — Pythonic API design: start with
  plain attributes; upgrade to properties only when you need validation or
  computed logic, without changing calling code.

### Pitfalls / common mistakes

- Forgetting `@x.setter` must use the *same* property name (`x`), not a
  differently named method — otherwise you silently create a second,
  separate property/attribute.
- Doing expensive work inside a `@property` getter — callers expect
  attribute access to be cheap; use `cached_property` or an explicit method
  if it's costly.
- Using `cached_property` on a class with `__slots__` and no `__dict__`
  slot — raises `TypeError` because `cached_property` needs somewhere to
  stash the cached value.
- Mutating `self._x` directly elsewhere in the class, bypassing the
  setter's validation logic.

---

## 5. `__slots__`

### Explanation

By default, every instance of a Python class gets a `__dict__` for storing
arbitrary instance attributes, which is flexible but memory-heavy (a dict
has significant per-instance overhead — hash table, resizing headroom,
etc.). Declaring `__slots__ = ('a', 'b', ...)` tells Python to allocate
fixed-size, C-level attribute slots for exactly those names instead of a
per-instance `__dict__`, and it disables arbitrary attribute creation.

Mechanically, `__slots__` works via descriptors too: for each name in
`__slots__`, Python creates a slot descriptor (a `member_descriptor`, data
descriptor) on the class, similar in spirit to the `PositiveNumber`
descriptor above but implemented in C, storing the value directly in a
fixed-offset slot in the instance's memory layout rather than in a dict.

Memory savings can be substantial — commonly 40-50% per instance for
simple objects — significant when instantiating millions of objects (e.g.,
graph nodes, event records, trading tick objects).

### Limitations

- No `instance.__dict__` unless you explicitly include `'__dict__'` in
  `__slots__` (which defeats much of the memory benefit).
- No dynamically adding new attributes not listed in `__slots__` —
  `AttributeError`.
- Every class in a multiple-inheritance chain that defines non-empty
  `__slots__` must be compatible (you can't easily combine multiple
  non-empty `__slots__` bases with different slot layouts — raises
  `TypeError: multiple bases have instance lay-out conflict`).
- Subclasses that don't declare `__slots__` still get a `__dict__` (the
  parent's savings only partially apply).
- No support for weak references unless `'__weakref__'` is included.
- Class attributes with default *mutable or complex* values can't be mixed
  naively with slots the way `__dict__`-based classes allow.

### Why it matters for SDE-2 interviews

- Classic performance/memory optimization question: "You have 10 million
  small objects; how do you reduce memory?" — `__slots__` is the direct
  Python answer, often paired with `sys.getsizeof` measurement.
  Companies dealing with large in-memory datasets (Uber's location pings,
  Adobe's asset metadata, Walmart's inventory records) value this
  awareness.
- Signals understanding of CPython internals beyond surface syntax.

### Code example

```python
import sys


class PointDict:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class PointSlots:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


pd = PointDict(1, 2)
ps = PointSlots(1, 2)

print("dict-based instance has __dict__:", hasattr(pd, "__dict__"))
print("slots-based instance has __dict__:", hasattr(ps, "__dict__"))

# Rough memory comparison (instance dict overhead not fully captured by
# getsizeof alone, but directionally correct):
print(sys.getsizeof(pd.__dict__))  # dict overhead that PointSlots avoids

try:
    ps.z = 10  # not declared in __slots__
except AttributeError as e:
    print("Error:", e)


# Inheritance with slots
class Point3DSlots(PointSlots):
    __slots__ = ("z",)  # only add the NEW slot; don't repeat x, y

    def __init__(self, x, y, z):
        super().__init__(x, y)
        self.z = z


p3 = Point3DSlots(1, 2, 3)
print(p3.x, p3.y, p3.z)
```

### Common interview questions / gotchas

- "What does `__slots__` actually save, mechanically?" — Removes the
  per-instance `__dict__`, storing attributes in fixed C-level slots
  instead.
- "Can you add new attributes to a `__slots__`-based instance at runtime?"
  — No, unless `__dict__` is included in slots.
- "What happens with multiple inheritance and `__slots__`?" — Layout
  conflicts can raise `TypeError`; generally avoid combining multiple
  non-empty `__slots__` bases.
- "If a subclass doesn't declare `__slots__`, does it still save memory?"
  — No — Python silently gives it a `__dict__`, so the memory benefit is
  lost for that subclass's instances (though the parent's fixed slots are
  still used underneath).
- "Do slots work with `@property` or class-level defaults?" — Slot names
  and class attribute names (like properties) must not collide; a slot
  descriptor and a class attribute of the same name conflict.

### Pitfalls / common mistakes

- Repeating parent slot names in a child class's `__slots__` — wastes
  memory (duplicate slot) and can cause subtle bugs.
- Adding `__dict__` to `__slots__` "just in case," which cancels out most
  of the memory savings while adding complexity.
- Forgetting that `__slots__` breaks pickling in old Python versions
  without a `__getstate__`/`__setstate__` (modern Python generally handles
  this fine, but it can still trip up naive equality/copy assumptions with
  frameworks expecting `__dict__`).
- Assuming `__slots__` gives thread safety or immutability — it does
  neither; it's purely a memory/attribute-restriction optimization.

---

## 6. Dataclasses

### Explanation

`@dataclass` (from the `dataclasses` module, Python 3.7+) auto-generates
boilerplate — `__init__`, `__repr__`, `__eq__` (and optionally
`__lt__`/`__le__`/etc. via `order=True`, and `__hash__` behavior via
`frozen`/`eq`) — based on class-level type-annotated fields.

Key building blocks:
- `field(default=..., default_factory=..., init=, repr=, compare=,
  metadata=)` — customize a specific field, especially needed for mutable
  defaults (lists/dicts/sets can't be plain `= []` defaults — Python raises
  `ValueError` for dataclasses specifically to prevent the classic mutable
  default bug; use `default_factory=list`).
- `frozen=True` — makes instances immutable after `__init__` (attribute
  assignment raises `FrozenInstanceError`) and auto-generates `__hash__`
  based on field values (useful for dict keys / set membership).
- `__post_init__` — a hook automatically called at the end of the
  generated `__init__`, used for derived-field computation or validation
  that can't be expressed as a simple default.
- `order=True` — generates comparison methods based on field order (like a
  tuple comparison).

### Comparison to `namedtuple`

| Feature | `dataclass` | `namedtuple` |
|---|---|---|
| Mutability | mutable by default (immutable via `frozen=True`) | always immutable |
| Type hints | first-class, used for `__init__` | optional (`typing.NamedTuple`) |
| Inheritance | full class inheritance supported | limited/awkward |
| Methods | add any method normally | same, but feels bolted-on |
| Iteration/unpacking as tuple | no (unless you add `__iter__`) | yes, behaves like a tuple |
| Memory | normal instance (`__dict__` unless `__slots__` added) | very compact (tuple-based) |
| Default values, validation | `field()`, `__post_init__` | more limited |

Use `namedtuple`/`typing.NamedTuple` for small, truly immutable,
tuple-like records you want to unpack/iterate. Use `dataclass` for richer
domain objects with methods, defaults, validation, and optional mutability.

### Why it matters for SDE-2 interviews

- Extremely common in modern take-home assignments and live-coding
  ("model a `Task`/`Order`/`Employee`") — using `@dataclass` correctly
  signals you write idiomatic modern Python instead of hand-rolling
  `__init__`/`__eq__`/`__repr__`.
- Companies with data-heavy domain models (Flipkart catalog objects, Uber
  trip records, Walmart order objects) use dataclasses pervasively for DTOs
  passed between services.

### Code example

```python
from dataclasses import dataclass, field, FrozenInstanceError
from typing import List


@dataclass
class Employee:
    name: str
    salary: float
    department: str = "Engineering"
    skills: List[str] = field(default_factory=list)
    _id_counter: int = field(default=0, repr=False, compare=False)

    def __post_init__(self):
        # Derived/validated field, computed after __init__ assigns the rest.
        if self.salary < 0:
            raise ValueError("Salary cannot be negative")
        self.annual_bonus = round(self.salary * 0.1, 2)


e1 = Employee("Asha", 90000, skills=["Python", "SQL"])
e2 = Employee("Asha", 90000, skills=["Python", "SQL"])
print(e1)
print(e1 == e2)          # True: field-wise equality auto-generated
print(e1.annual_bonus)


@dataclass(frozen=True, order=True)
class Point:
    x: int
    y: int


p1 = Point(1, 2)
p2 = Point(1, 3)
print(p1 < p2)            # True: tuple-style comparison via order=True
try:
    p1.x = 99
except FrozenInstanceError as e:
    print("Error:", e)

points = {p1, p2}          # frozen dataclasses are hashable -> usable in sets
print(len(points))


# namedtuple comparison
from collections import namedtuple
from typing import NamedTuple

PointNT = namedtuple("PointNT", ["x", "y"])
pt = PointNT(1, 2)
x, y = pt  # unpacks like a tuple
print(x, y, pt[0])


class PointTyped(NamedTuple):
    x: int
    y: int


pt2 = PointTyped(1, 2)
print(pt2._replace(x=5))  # immutable "copy with change" helper
```

### Common interview questions / gotchas

- "Why can't you use `field: list = []` as a default in a dataclass?" —
  Mutable default shared across instances; dataclasses explicitly detect
  and forbid this for `list`/`dict`/`set`, forcing `default_factory`.
- "How do you make a dataclass hashable/usable as a dict key?" —
  `frozen=True` (and `eq=True`, the default) auto-generates `__hash__`
  based on fields; a mutable dataclass has `__hash__` set to `None` by
  default (matching how `__eq__` implies unhashable unless you override).
- "What does `__post_init__` do and when do you need it?" — Runs after
  the generated `__init__` finishes assigning fields; used for validation
  or computing derived fields not directly expressible as defaults.
- "`dataclass` vs `NamedTuple` vs plain class — when would you pick each?"
  — see comparison table above.
- "Can a dataclass field depend on another field's value at construction
  time?" — Yes, via `__post_init__` (fields aren't lazily resolved to each
  other automatically).

### Pitfalls / common mistakes

- Declaring fields without type annotations — `dataclass` only picks up
  class-level attributes that have type annotations; a bare `x = 5` is
  treated as a normal class attribute, not a dataclass field.
- Forgetting `frozen=True` dataclasses still allow mutating *nested*
  mutable objects (e.g., a `frozen` dataclass holding a `list` field — the
  list itself can still be mutated in place; only reassignment of the
  attribute is blocked).
- Field ordering issues: fields with defaults must come after fields
  without defaults (same rule as function parameters), or you get a
  `TypeError` at class-definition time.
- Comparing/hashing dataclasses that contain unhashable fields (e.g., a
  `list`) when `frozen=True` — hashing will fail at runtime since the
  generated `__hash__` tries to hash all compared fields.

---

## 7. Protocols (structural typing)

### Explanation

`typing.Protocol` (PEP 544, Python 3.8+) formalizes duck typing: instead of
requiring a class to explicitly inherit from an interface (nominal typing,
like ABCs), a `Protocol` describes a *shape* — a set of methods/attributes
— and any object satisfying that shape is considered compatible, with no
inheritance relationship required. This is checked statically by type
checkers (mypy, pyright) and can optionally be checked at runtime with
`@runtime_checkable` + `isinstance()`.

```python
class SupportsClose(Protocol):
    def close(self) -> None: ...
```

Any object with a `close()` method — a file, a socket, a custom resource
— satisfies `SupportsClose`, without ever mentioning it in its class
definition. This is exactly how Python's own `typing` module models
built-in duck-typed interfaces (`Iterable`, `Sized`, `Hashable`,
`SupportsInt`, etc.).

`@runtime_checkable` allows `isinstance(obj, MyProtocol)` at runtime, but
it only checks for the *presence* of the named methods/attributes, not
their signatures (no argument/type checking at runtime — that's the
static checker's job).

### Why it matters for SDE-2 interviews

- Reflects current, idiomatic typed Python — companies with strict typing
  standards (Google's internal style guide leans heavily on structural
  typing patterns; Microsoft/Amazon large Python services increasingly
  require mypy/pyright in CI) expect familiarity with `Protocol` for
  writing flexible, decoupled interfaces without forcing inheritance
  hierarchies onto third-party or legacy types.
- Useful in dependency-injection/testing contexts: you can pass in any
  object satisfying a `Protocol` (including simple test doubles) without
  those doubles needing to inherit from a real base class.

### Code example

```python
from typing import Protocol, runtime_checkable, List


class SupportsArea(Protocol):
    def area(self) -> float: ...


class Circle:
    def __init__(self, r: float):
        self.r = r

    def area(self) -> float:
        return 3.14159 * self.r ** 2


class Rectangle:
    def __init__(self, w: float, h: float):
        self.w, self.h = w, h

    def area(self) -> float:
        return self.w * self.h


def total_area(shapes: List[SupportsArea]) -> float:
    # Neither Circle nor Rectangle inherits from SupportsArea; this is
    # purely structural — a static type checker verifies this is valid.
    return sum(s.area() for s in shapes)


print(total_area([Circle(2), Rectangle(3, 4)]))


@runtime_checkable
class SupportsClose(Protocol):
    def close(self) -> None: ...


class DbConnection:
    def close(self) -> None:
        print("closing connection")


conn = DbConnection()
print(isinstance(conn, SupportsClose))  # True, runtime structural check
print(isinstance(42, SupportsClose))    # False


# Protocol with attributes, not just methods
class HasName(Protocol):
    name: str


def greet(entity: HasName) -> str:
    return f"Hello, {entity.name}"


class Robot:
    name = "R2D2"


print(greet(Robot()))
```

### Common interview questions / gotchas

- "Protocol vs ABC — core difference?" — Structural (duck typing, no
  inheritance needed) vs nominal (explicit `class X(ABC)` inheritance
  required).
- "How do you get runtime `isinstance` checks with a Protocol?" —
  `@runtime_checkable`, but note it only checks method/attribute
  *presence*, not signatures.
- "Why might you prefer a Protocol over an ABC for a utility function that
  accepts 'anything with a `.read()` method'?" — You don't control every
  caller's class hierarchy (e.g., third-party file-like objects); a
  Protocol lets them satisfy the interface without modification.
- "Can a Protocol have default method implementations?" — Yes, protocols
  can provide concrete method bodies as defaults, similar to a mixin, and
  classes can optionally also explicitly inherit from the Protocol if
  desired (a Protocol can double as an ABC-like base if you choose).

### Pitfalls / common mistakes

- Assuming `@runtime_checkable` performs full signature/type validation —
  it doesn't; it only checks that the named attributes exist.
- Forgetting `@runtime_checkable` and then trying `isinstance(obj, MyProto)`
  — raises `TypeError: Instance and class checks can only be used with
  @runtime_checkable protocols`.
- Using a Protocol when you actually want to force a real inheritance
  contract with shared implementation state — that's what ABC (or a
  regular base class) is for.
- Overusing Protocols for tightly coupled internal code where a simple ABC
  or concrete base class would be clearer and enforce more at
  class-definition time rather than only via static analysis.

---

## 8. Generic Types

### Explanation

`typing.Generic` and `TypeVar` let you parameterize classes and functions
over types, so a type checker can track "this container holds `T`s" and
flag type mismatches — Python's version of Java/C++ generics, entirely a
static-typing construct (erased at runtime; no runtime enforcement).

```python
T = TypeVar("T")

class Stack(Generic[T]):
    def push(self, item: T) -> None: ...
    def pop(self) -> T: ...
```

`Stack[int]` and `Stack[str]` are then distinct types to a checker, even
though at runtime it's the same `Stack` class doing the same thing
regardless of `T`.

`TypeVar` can be constrained (`TypeVar("T", int, float)` — only these
exact types) or bounded (`TypeVar("T", bound=Shape)` — `T` must be `Shape`
or a subclass), and can be marked covariant/contravariant
(`covariant=True`/`contravariant=True`) for variance rules in generic
containers.

Since Python 3.12, PEP 695 introduces cleaner built-in syntax:
`class Stack[T]: ...` and `def first[T](items: list[T]) -> T: ...`,
without needing to import `TypeVar`/`Generic` explicitly — but
understanding the classic `TypeVar`/`Generic` mechanics is still essential
since most production codebases (and interview environments) target 3.8-3.11.

### Why it matters for SDE-2 interviews

- Directly tests whether you can design reusable, type-safe data
  structures (generic `Cache[K, V]`, `Repository[T]`, `Result[T, E]`)
  — a very natural "design a generic X" interview prompt at any of these
  companies, especially ones with typed Python services (Google, Microsoft,
  Adobe).
- Shows awareness that Python's type system is optional/erased —
  interviewers often probe "does this raise an error at runtime if you
  violate `T`?" to check you understand static vs. dynamic typing
  boundaries.

### Code example

```python
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> Optional[T]:
        return self._items[-1] if self._items else None

    def __len__(self) -> int:
        return len(self._items)


int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
print(int_stack.pop())

str_stack: Stack[str] = Stack()
str_stack.push("hello")
# int_stack.push("oops")  # a type checker (mypy/pyright) flags this;
                           # at runtime Python happily allows it (erased).


class Cache(Generic[K, V]):
    def __init__(self) -> None:
        self._store: dict[K, V] = {}

    def get(self, key: K) -> Optional[V]:
        return self._store.get(key)

    def set(self, key: K, value: V) -> None:
        self._store[key] = value


cache: Cache[str, int] = Cache()
cache.set("age", 30)
print(cache.get("age"))


# Bounded TypeVar: T must be a Comparable-like type
from typing import TypeVar

class Comparable(Generic[T]):
    def __lt__(self, other: T) -> bool: ...

CT = TypeVar("CT", bound=Comparable)


def smallest(items: List[CT]) -> CT:
    result = items[0]
    for item in items[1:]:
        if item < result:
            result = item
    return result


print(smallest([5, 3, 8, 1]))


# Generic function (works without a Generic class)
def first_item(items: List[T]) -> T:
    return items[0]


print(first_item([10, 20, 30]))
print(first_item(["a", "b"]))
```

### Common interview questions / gotchas

- "Does `Stack[int]` prevent you from pushing a string at runtime?" — No.
  Generics are purely a static-typing hint; Python performs no runtime
  enforcement unless you add your own `isinstance` checks.
- "What's the difference between a constrained and a bound `TypeVar`?" —
  Constrained (`TypeVar('T', int, float)`) restricts `T` to exactly one of
  the listed types; bound (`TypeVar('T', bound=Base)`) allows `Base` or
  any subclass.
- "What does covariance/contravariance mean for generics, with an
  example?" — Covariant: `List[Cat]` can be used where `List[Animal]` is
  expected if the container is read-only; contravariant is the reverse,
  relevant for callable/parameter positions (e.g., a
  `Callable[[Animal], None]` handler can be substituted where
  `Callable[[Cat], None]` is expected).
- "How does PEP 695 (3.12) change generic syntax?" — Adds native
  `class Foo[T]:` / `def foo[T](...)` syntax, removing the need for
  explicit `TypeVar`/`Generic` imports, while remaining compatible in
  intent with the classic approach.

### Pitfalls / common mistakes

- Believing generics provide runtime type safety — they don't; only static
  type checkers enforce them, and only if actually run in CI.
- Reusing the same bare `TypeVar` name (`T`) across unrelated generic
  classes/functions in the same module without realizing each `TypeVar`
  instance is independent — this is usually fine, but confuses newcomers
  reading code that appears to "share" `T` across contexts.
- Forgetting `Generic[T]` in the class's base classes while still trying to
  use `T` inside method signatures — type checkers won't treat the class as
  generic without explicitly inheriting from `Generic[T]` (pre-3.12
  syntax).
- Over-engineering with generics for code that will only ever operate on
  one concrete type — adds indirection and cognitive overhead without
  real benefit; use generics when genuine type-parameterized reuse is
  needed (containers, repositories, result wrappers), not everywhere.

---

## Summary Table

| Feature | Core Mechanism | Primary Use Case |
|---|---|---|
| ABC | `ABCMeta` + `@abstractmethod` | Enforce interface contracts |
| Metaclass | `type` subclass controlling class creation | Frameworks, ORMs, registries, singletons |
| Descriptor | `__get__`/`__set__`/`__delete__` | Reusable attribute behavior (validation, computed values) |
| Property | Built-in data descriptor | Computed/validated attributes with clean syntax |
| `__slots__` | Fixed C-level attribute storage | Memory optimization at scale |
| Dataclass | Code generation from annotated fields | Boilerplate-free domain/data objects |
| Protocol | Structural typing (PEP 544) | Duck typing with static-checker support |
| Generic | `TypeVar`/`Generic` (or PEP 695 syntax) | Reusable, type-parameterized containers/functions |
