# Functions

In Python, functions are first-class citizens. This means they are treated as objects: they can be passed as arguments to other functions, returned from other functions, bound to variable names, and stored in data structures. For SDE-2 interviews, understanding the mechanics of function calls, parameter passing, closures, scoping rules, and type hinting is essential.

## Table of Contents

- [Function Definition & Execution Mechanics](#function-definition--execution-mechanics)
- [Parameters and Arguments (Positional-only, Keyword-only, `*args`, `**kwargs`)](#parameters-and-arguments-positional-only-keyword-only-args-kwargs)
- [Mutable Default Arguments (The Classic Pitfall)](#mutable-default-arguments-the-classic-pitfall)
- [Scope and the LEGB Rule](#scope-and-the-legb-rule)
- [Closures and Late Binding](#closures-and-late-binding)
- [First-Class and Higher-Order Functions](#first-class-and-higher-order-functions)
- [Lambda Functions & Partial Functions](#lambda-functions--partial-functions)
- [Function Annotations & Type Hints](#function-annotations--type-hints)

---

## Function Definition & Execution Mechanics

### Explanation

When you define a function using `def`, CPython parses the code, compiles it into bytecode, and creates a function object at definition time. The body of the function is not executed until it is called.

A function call creates a new **activation record** or **stack frame** on the execution stack. This frame stores the local namespace, local variables, parameters, and reference to the calling frame.

### Why it matters / internals

- A function in Python is an instance of the `function` class. It has attributes like `__code__` (compiled bytecode), `__defaults__` (default positional arguments), `__kwdefaults__` (default keyword-only arguments), `__globals__` (reference to the global namespace dictionary), and `__closure__` (references to cell objects for closed-over variables).
- Because `def` is an executable statement, functions are dynamically created at runtime when the module containing them is imported or when the enclosing function runs.

### Code example

```python
def make_multiplier(factor):
    def multiply(x):
        return x * factor
    return multiply

double = make_multiplier(2)
print(double.__code__.co_varnames)    # ('x',)
print(double.__closure__[0].cell_contents)  # 2
```

### Common interview questions / gotchas

- "What is the difference between function definition time and function execution time?" -> Definition compiles bytecode and creates the function object. Execution creates a new stack frame and evaluates the bytecode.
- "How are nested functions garbage collected?" -> They are garbage collected when their references are no longer held, even if they have closed-over variables from outer functions, thanks to CPython's reference counting and cyclic GC.

---

## Parameters and Arguments (Positional-only, Keyword-only, `*args`, `**kwargs`)

### Explanation

Python offers fine-grained control over how arguments are accepted:
- **Positional-only parameters**: Separated by `/`. Arguments before `/` cannot be passed by keyword.
- **Keyword-only parameters**: Separated by `*`. Arguments after `*` must be passed by keyword.
- `*args`: Collects arbitrary positional arguments into a `tuple`.
- `**kwargs`: Collects arbitrary keyword arguments into a `dict`.

### Why it matters / internals

- Positional-only parameters (`/`, introduced in PEP 570) allow changing parameter names in the future without breaking user code. They also match C API behaviors.
- Keyword-only parameters (`*`, introduced in PEP 3102) prevent bugs when users pass arguments in the wrong order or force API callers to be explicit.
- Unpacking: When calling a function, `*iterable` unpacks elements as positional arguments, and `**dict` unpacks keys/values as keyword arguments.

### Code example

```python
def configure_service(host, port, /, timeout=30, *, retries=3, **kwargs):
    # host, port -> Positional-only
    # timeout -> Positional OR Keyword
    # retries -> Keyword-only
    print(f"{host}:{port}, timeout={timeout}, retries={retries}, extra={kwargs}")

# Correct:
configure_service("localhost", 8080, 10, retries=5, verbose=True)

# TypeError: configure_service() got some positional-only arguments passed as keyword arguments: 'host, port'
# configure_service(host="localhost", port=8080)
```

---

## Mutable Default Arguments (The Classic Pitfall)

### Explanation

Default arguments in Python are evaluated **once**, when the function is defined, not each time the function is called. If you use a mutable object (like a list, dictionary, or set) as a default argument, all function calls share that same object.

### Why it matters / internals

The default values are stored in the function's `__defaults__` tuple. When the function is called without that parameter, Python binds the parameter variable to the object in `__defaults__`. If you mutate that object, the modification persists in `__defaults__`.

### Code example

```python
# Bad practice:
def append_to(element, target=[]):
    target.append(element)
    return target

print(append_to(1))  # [1]
print(append_to(2))  # [1, 2] (Shared reference!)

# Good practice:
def append_to_safe(element, target=None):
    if target is None:
        target = []
    target.append(element)
    return target

print(append_to_safe(1))  # [1]
print(append_to_safe(2))  # [2]
```

### Pitfalls

- Using empty lists, dicts, or sets directly as defaults: `def process(data={}):`.
- Using mutable class attributes or mutable custom objects as defaults.

---

## Scope and the LEGB Rule

### Explanation

Python resolves names using the **LEGB rule** (Local -> Enclosing -> Global -> Built-in):
1. **Local (L)**: Names assigned inside a function and not declared `global` or `nonlocal`.
2. **Enclosing (E)**: Names in the local scope of any enclosing/nested functions, from inner to outer.
3. **Global (G)**: Names assigned at the top-level of a module, or declared `global`.
4. **Built-in (B)**: Names pre-loaded in the builtins module (e.g., `len`, `int`, `ValueError`).

### Why it matters / internals

- Reading a variable searches LEGB. Writing to a variable by default creates or modifies the name in the **L**ocal scope.
- To write to an enclosing scope variable, use the `nonlocal` keyword.
- To write to a global scope variable, use the `global` keyword.

### Code example

```python
x = "global"

def outer():
    x = "enclosing"
    
    def inner():
        nonlocal x
        x = "modified enclosing"
    
    inner()
    print(x)  # "modified enclosing"

outer()
print(x)      # "global"
```

### Pitfalls

- **UnboundLocalError**: Writing to a variable inside a function without `global` or `nonlocal` makes Python treat the variable as local to the entire function scope. If you read it before writing to it in the same function, Python raises an error.

```python
y = 10
def read_and_write():
    # print(y)  # UnboundLocalError: local variable 'y' referenced before assignment
    y = 20
```

---

## Closures and Late Binding

### Explanation

A **closure** is a nested function that remembers and has access to variables from its enclosing scope, even after the enclosing function has finished executing.

### Why it matters / internals

- Cell objects: When a nested function references a variable in an enclosing scope, CPython creates a "cell" object to store the variable's value. Both the enclosing scope and the closure point to this same cell, extending its lifetime beyond the execution frame of the enclosing function.

### Late Binding Closure (Classic Pitfall)

Python's closures bind variables by reference, not by value. The nested functions look up the value when they are **executed**, not when they are defined.

```python
# Pitfall:
def make_multipliers():
    return [lambda x: i * x for i in range(3)]

multipliers = make_multipliers()
print([m(2) for m in multipliers])  # Expected: [0, 2, 4], Actual: [4, 4, 4]
# Why? The variable 'i' is looked up when m(2) is called. At that time, i is 2.

# Solution: Bind at definition time using default arguments
def make_multipliers_safe():
    return [lambda x, i=i: i * x for i in range(3)]

multipliers_safe = make_multipliers_safe()
print([m(2) for m in multipliers_safe])  # [0, 2, 4]
```

---

## First-Class and Higher-Order Functions

### Explanation

A **higher-order function** is a function that does at least one of the following:
- Takes one or more functions as arguments.
- Returns a function as its result.

Examples in Python include `map()`, `filter()`, `sorted()`, and custom decorators.

---

## Lambda Functions & Partial Functions

### Explanation

- **Lambda Functions**: Anonymous, single-expression functions. They cannot contain statements or assignments (pre-Python 3.8).
- **Partial Functions**: Created using `functools.partial`, which freezes a portion of a function's arguments and/or keywords, returning a new callable.

### Code example

```python
from functools import partial

# Lambda
square = lambda x: x * x

# Partial
def multiply(x, y):
    return x * y

double = partial(multiply, 2)
print(double(5))  # 10
```

---

## Function Annotations & Type Hints

### Explanation

Function annotations (PEP 3107) and type hints (PEP 484) let you attach metadata to function parameters and return values.

### Why it matters / internals

- Annotations are stored in the function's `__annotations__` dictionary.
- They are **not** enforced at runtime by Python itself; they are used by static type checkers (like `mypy`) or runtime libraries (like `pydantic`).

### Code example

```python
def process_items(items: list[int]) -> int:
    return sum(items)

print(process_items.__annotations__)  # {'items': list[int], 'return': <class 'int'>}
```
