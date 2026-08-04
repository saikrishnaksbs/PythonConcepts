# Comprehensions

Comprehensions in Python provide a concise way to create collections (lists, sets, dictionaries) and generators. While they improve readability, they also run slightly faster than equivalent `for` loops because the loop iteration is performed at C-level inside the interpreter. For SDE-2 roles, you should understand how scoping works inside comprehensions, the difference between eager and lazy evaluations, and how to write clean nested comprehensions.

## Table of Contents

- [List Comprehensions](#list-comprehensions)
- [Set and Dictionary Comprehensions](#set-and-dictionary-comprehensions)
- [Generator Expressions (Lazy Evaluation)](#generator-expressions-lazy-evaluation)
- [Nested Comprehensions & Loop Execution Order](#nested-comprehensions--loop-execution-order)
- [Scoping in Comprehensions](#scoping-in-comprehensions)

---

## List Comprehensions

### Explanation

A list comprehension constructs a new list by applying an expression to each item in an iterable, optionally filtering elements with an `if` condition.

### Code example

```python
# Traditional loop:
squares = []
for x in range(10):
    if x % 2 == 0:
        squares.append(x * x)

# List comprehension:
squares_comp = [x * x for x in range(10) if x % 2 == 0]
```

---

## Set and Dictionary Comprehensions

### Explanation

- **Set Comprehension**: Similar to list comprehensions but uses curly braces `{}` and produces a set (which deduplicates elements).
- **Dictionary Comprehension**: Uses curly braces `{}` and specifies `key: value` pairs.

### Code example

```python
# Set comprehension
unique_lengths = {len(word) for word in ["apple", "banana", "pear", "apple"]}
# Output: {4, 5, 6}

# Dict comprehension
square_map = {x: x * x for x in range(5)}
# Output: {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

---

## Generator Expressions (Lazy Evaluation)

### Explanation

A generator expression uses parentheses `()` instead of brackets and yields elements lazily (one at a time) rather than building the entire list in memory.

### Why it matters / internals

Use generator expressions when piping outputs to reduction functions (like `sum()`, `any()`, `all()`, `min()`, `max()`) to avoid allocating temporary lists in memory.

```python
# Allocates temporary list of 1M elements
total_eager = sum([x * x for x in range(1000000)])

# Zero-allocation (constant memory)
total_lazy = sum(x * x for x in range(1000000))
```

---

## Nested Comprehensions & Loop Execution Order

### Explanation

When nesting loops inside a comprehension, the order of the `for` clauses matches the order you would write them in a nested standard `for` loop.

### Code example

```python
matrix = [[1, 2], [3, 4]]

# Flatten the matrix:
# Equivalent to:
# flattened = []
# for row in matrix:
#     for col in row:
#         flattened.append(col)
flattened = [col for row in matrix for col in row]
print(flattened)  # [1, 2, 3, 4]
```

### Pitfalls

Writing nested comprehensions beyond two levels degrades readability. Code readability is a key SDE-2 standard; if a comprehension is complex, refactor it into a standard generator function or loop.

---

## Scoping in Comprehensions

### Explanation

In Python 2, the loop variable in a list comprehension would leak into the surrounding scope. In Python 3, comprehensions are executed in a separate, temporary nested scope (implemented as an implicit function under the hood). Loop variables do **not** leak or overwrite variables in the enclosing scope.

### Code example

```python
x = 99
# List comprehension variable 'x' is isolated
squares = [x * x for x in range(5)]
print(x)  # 99 (Unchanged!)
```

**Gotcha:** The iterable of the *first* `for` clause is evaluated eagerly in the enclosing scope (so it can raise `NameError` immediately if undefined), but subsequent clauses and the expression execute inside the comprehension's own scope.

```python
def make():
    return [y for y in undefined_name]  # NameError raised at call time, not definition time
```

---

## Common Interview Questions

1. **"Are comprehensions faster than loops?"** Usually yes for simple transformations — the loop runs as a single specialized bytecode (`LIST_APPEND`) inside the interpreter's C loop instead of repeated Python-level `.append()` calls.
2. **"When should you NOT use a comprehension?"** When the expression has side effects, needs multiple statements, or nesting exceeds 2 levels — prefer an explicit loop or generator function for readability.
3. **Pitfall:** Comprehensions with multiple `if` conditions chain as logical AND — `[x for x in range(10) if x > 2 if x < 8]` is equivalent to `if x > 2 and x < 8`.
4. **Pitfall:** A dict comprehension with duplicate keys silently keeps only the last value — `{k: v for k, v in pairs}` drops earlier duplicates without warning.
