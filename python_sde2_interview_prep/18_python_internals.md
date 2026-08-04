# Python Internals

Understanding CPython (the reference implementation of Python) internals separates junior developers from senior SDE-2 engineers. Knowing how Python executes code under the hood helps write performant code, inspect stack traces, and debug execution anomalies.

## Table of Contents

- [CPython Architecture & Compilation Process](#cpython-architecture--compilation-process)
- [Bytecode & `.pyc` Files](#bytecode--pyc-files)
- [The Python Virtual Machine (PVM)](#the-python-virtual-machine-pvm)
- [Everything is an Object: `PyObject`](#everything-is-an-object-pyobject)
- [The Import System Internals](#the-import-system-internals)
- [Stack Frames & Symbol Tables](#stack-frames--symbol-tables)

---

## CPython Architecture & Compilation Process

### Explanation

CPython compiles Python source code into an intermediate format called **bytecode** before executing it on a stack-based virtual machine. The compilation process is:

1. **Tokenization**: The lexer converts source code (text) into a stream of tokens.
2. **Parsing**: The parser builds an Abstract Syntax Tree (AST) from the token stream.
3. **Compilation**: The compiler turns the AST into a Control Flow Graph (CFG) and then generates bytecode (code objects).
4. **Execution**: The Python Virtual Machine (PVM) interprets and runs the bytecode.

---

## Bytecode & `.pyc` Files

### Explanation

- **Bytecode**: A low-level, platform-independent instruction set. Each instruction is represented by a 1-byte opcode (hence "bytecode") and optional arguments.
- **`.pyc` Files**: Cached bytecode saved inside `__pycache__` directories. When importing a module, Python writes the compiled bytecode to a `.pyc` file. On subsequent runs, if the source file timestamp and size match, Python loads the `.pyc` file directly, speeding up import times.

### Code example

You can inspect the bytecode generated for a function using the standard library's `dis` module:

```python
import dis

def add(a, b):
    return a + b

dis.dis(add)
# Outputs:
#   2           0 LOAD_FAST                0 (a)
#               2 LOAD_FAST                1 (b)
#               4 BINARY_OP                0 (+)
#               8 RETURN_VALUE
```

---

## The Python Virtual Machine (PVM)

### Explanation

The PVM is the loop that executes bytecode. It is a **stack-based interpreter** (as opposed to register-based interpreters like Lua's VM or Dalvik).
- CPython maintains an **evaluation stack** (also called data stack).
- Most bytecodes pop items from this stack, perform an operation, and push the result back onto the stack.

---

## Everything is an Object: `PyObject`

### Explanation

In CPython, every Python object is represented by a C struct that extends `PyObject`.

### Why it matters / internals

At the core of every Python object is the `PyObject` struct, which contains:
1. `ob_refcnt`: The reference count (used for garbage collection).
2. `ob_type`: A pointer to a type object (which defines the object's class, available methods, etc.).

For variable-sized objects (like lists, strings, or tuples), CPython uses `PyVarObject`, which includes a third field:
3. `ob_size`: The number of items in the container.

This means even a simple integer in Python carries a memory overhead of at least 28 bytes (on 64-bit platforms) due to these metadata fields, whereas a raw C `int` requires only 4 bytes.

---

## The Import System Internals

### Explanation

When you execute `import foo`, Python performs the following steps:

1. **Search `sys.modules`**: Python checks `sys.modules` (a dictionary caching imported modules). If `foo` is present, it returns the cached module object immediately.
2. **Finders**: If not cached, Python iterates over `sys.meta_path`, invoking **Finders** to locate the module's source or bytecode. Finders search paths like directory paths listed in `sys.path`.
3. **Loaders**: Once located, a **Loader** compiles the source (if necessary), creates a new module object, executes the module's code in the new module's namespace, and stores it in `sys.modules`.

---

## Stack Frames & Symbol Tables

### Explanation

- **Stack Frame**: Represented by the `PyFrameObject` struct in CPython. Created whenever a function is called. It holds the variables and execution state:
  - `f_locals`: Local namespace dictionary.
  - `f_globals`: Global namespace dictionary.
  - `f_back`: Pointer to the calling frame (enabling traceback generation).
  - `f_code`: The code object (`PyCodeObject`) being executed.
- **Symbol Table**: A compiler data structure mapping variable names to their scopes (local, global, free, cell) at compile time. This dictates whether an instruction uses `LOAD_FAST` (fast index-based local lookup) or `LOAD_GLOBAL`.

---

## Namespaces & the LEGB Rule

### Explanation

A namespace is a mapping from names to objects (implemented as a `dict`). Python has four namespace levels searched in order: **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in. See [36_interview_favorites.md](36_interview_favorites.md#3-legb-rule) for the canonical gotcha example.

```python
import builtins
print(dir(builtins))  # the outermost (Built-in) namespace
```

### Why it matters

`LOAD_FAST` is used only for names the compiler proves are local (assigned somewhere in the function) — this is why assigning to a variable anywhere in a function makes it local for the *entire* function body, causing `UnboundLocalError` if read before that assignment.

```python
x = 10
def f():
    print(x)  # UnboundLocalError, not 10 -- x is local due to the assignment below
    x = 20
```

## Object Model Recap

"Everything is an object" means functions, classes, and modules are themselves instances of `PyObject`-derived types (`function`, `type`, `module`) and can be introspected, passed around, and have attributes just like any other value.

```python
def f(): pass
print(type(f))        # <class 'function'>
print(type(type(f)))  # <class 'type'>
print(type(int))      # <class 'type'> -- classes are objects of type 'type'
```

## Common Interview Questions

1. **"What invalidates a `.pyc` cache?"** A magic number tied to the bytecode format version, plus the source file's mtime and size (or a hash, depending on `PYTHONDONTWRITEBYTECODE`/hash-based `.pyc` mode) stored in the `.pyc` header.
2. **"Is CPython the only implementation?"** No — PyPy (JIT-compiled, faster for long-running CPU-bound code), Jython (JVM), IronPython (.NET), and MicroPython (embedded) are alternative implementations with different internals (e.g., PyPy has no GIL-bound bytecode interpreter in the same sense and uses a tracing JIT).
3. **Pitfall:** Assuming bytecode is portable across Python versions — `.pyc` files are tied to a specific interpreter version and are not forward/backward compatible.
