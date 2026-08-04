# Itertools Module

The `itertools` module contains a collection of fast, memory-efficient tools for working with iterators. All tools in this module return lazy iterables, meaning they process items one at a time and are written in highly optimized C. For SDE-2 interviews, you should know how to compose these tools to build data pipelines and perform combinatorial iterations.

## Table of Contents

- [Infinite Iterators (`cycle`, `count`, `repeat`)](#infinite-iterators-cycle-count-repeat)
- [Combinatoric Iterators (`product`, `permutations`, `combinations`)](#combinatoric-iterators-product-permutations-combinations)
- [Terminating Iterators (`chain`, `accumulate`, `groupby`)](#terminating-iterators-chain-accumulate-groupby)

---

## Infinite Iterators (`cycle`, `count`, `repeat`)

### Explanation

- **`count(start, step)`**: Returns an infinite sequence of spaced values.
- **`cycle(iterable)`**: Saves a copy of the elements of an iterable and cycles through them indefinitely.
- **`repeat(object, times)`**: Repeats an object indefinitely or a fixed number of times.

### Code example

```python
import itertools

# Infinite counting
for i in itertools.count(10, 2):
    if i > 14:
        break
    print(i)  # 10, 12, 14
```

---

## Combinatoric Iterators (`product`, `permutations`, `combinations`)

### Explanation

- **`product(*iterables, repeat=1)`**: Computes the Cartesian product of input iterables (equivalent to nested loops).
- **`permutations(iterable, r)`**: Returns successive $r$-length permutations of elements in the iterable.
- **`combinations(iterable, r)`**: Returns successive $r$-length combinations (subsets) of elements without replacement, maintaining input order.

### Code example

```python
import itertools

# Cartesian Product
print(list(itertools.product([1, 2], ["A", "B"])))
# [(1, 'A'), (1, 'B'), (2, 'A'), (2, 'B')]

# Combinations of length 2
print(list(itertools.combinations([1, 2, 3], 2)))
# [(1, 2), (1, 3), (2, 3)]
```

---

## Terminating Iterators (`chain`, `accumulate`, `groupby`)

### Explanation

- **`chain(*iterables)`**: Combines multiple iterables into a single sequence, yielding items from the first, then the second, and so on.
- **`accumulate(iterable, func=operator.add)`**: Returns accumulated sums (or running results of a binary function).
- **`groupby(iterable, key=None)`**: Groups consecutive keys and groups from the input.

### Why it matters / internals (Groupby Gotcha)

> [!IMPORTANT]
> **`groupby` requires input data to be sorted** by the grouping key first. It only groups *consecutive* identical keys. If the same key appears later in the stream separated by other keys, a new group is created.

### Code example

```python
import itertools

# Chain
combined = itertools.chain([1, 2], [3, 4])
print(list(combined))  # [1, 2, 3, 4]

# Groupby Gotcha
data = [("A", 1), ("B", 2), ("A", 3)]
# Incorrect: 'A' is not consecutive
groups = {k: list(g) for k, g in itertools.groupby(data, lambda x: x[0])}
print(groups)  # {'A': [('A', 3)], 'B': [('B', 2)]} (Lost first A group!)

# Correct: Sort first
sorted_data = sorted(data, key=lambda x: x[0])
groups_correct = {k: list(g) for k, g in itertools.groupby(sorted_data, lambda x: x[0])}
print(groups_correct)  # {'A': [('A', 1), ('A', 3)], 'B': [('B', 2)]}
```

---

## Other Frequently Used Tools

```python
import itertools

# islice: lazy slicing of any iterable, including infinite ones
list(itertools.islice(itertools.count(), 5, 10))  # [5, 6, 7, 8, 9]

# tee: split one iterator into n independent ones (consumes memory to buffer divergence)
a, b = itertools.tee(iter([1, 2, 3]), 2)

# starmap: like map, but unpacks argument tuples
list(itertools.starmap(pow, [(2, 5), (3, 2)]))  # [32, 9]

# zip_longest: like zip, but pads shorter iterables
list(itertools.zip_longest([1, 2], [1], fillvalue=0))  # [(1, 1), (2, 0)]
```

## Common Interview Questions

1. **"Why use `itertools.chain` instead of `list1 + list2`?"** `chain` doesn't materialize a new combined list — it lazily iterates each source in turn, which matters when combining large or infinite iterables.
2. **"How would you generate all subsets of a set?"** Use `itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1))` for the power set.
3. **Pitfall:** Consuming an iterator returned by `tee()` unevenly can cause unbounded memory growth internally, since `tee` must buffer elements the slower branch hasn't consumed yet.
4. **Pitfall:** `permutations`/`combinations` treat elements by *position*, not by value — duplicate values in the input produce duplicate-looking output tuples unless you dedupe with a `set()` afterward.
