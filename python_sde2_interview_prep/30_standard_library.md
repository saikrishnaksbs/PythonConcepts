# Standard Library

This file is a working reference to the parts of the Python standard library that
come up most often in SDE-2 interviews and in day-to-day backend/systems work at
companies like Google, Amazon, Microsoft, Atlassian, Uber, Flipkart, Walmart, and
Adobe. Each section covers what the module is for, why it matters in real systems,
a runnable example, and interview questions/gotchas you should be ready to answer.

## math

### What it's for

`math` gives you fast, C-implemented numeric functions that operate on Python
`float`/`int` scalars: trig, logarithms, powers, factorials, gcd/lcm, and
constants like `math.pi` and `math.inf`. It is the go-to for scalar math when you
don't need arrays (that's numpy's job).

### Why/when it's used

- Computing distances (Euclidean, haversine) in geo/location services (Uber,
  Flipkart logistics).
- Combinatorics in algorithm problems (`math.comb`, `math.perm`, `math.factorial`).
- Numerically stable checks (`math.isclose` instead of `==` for floats).
- `math.gcd`/`math.lcm` for scheduling problems (e.g., "every gcd(a, b) seconds").

```python
import math

# Basic functions
print(math.sqrt(16))          # 4.0
print(math.pow(2, 10))        # 1024.0 (always returns float, unlike 2 ** 10)
print(math.floor(3.7), math.ceil(3.2))  # 3 4
print(math.log(8, 2))         # 3.0 (log base 2)
print(math.log2(8), math.log10(1000))   # 3.0 3.0

# Floating point gotcha
print(0.1 + 0.2 == 0.3)              # False! classic float trap
print(math.isclose(0.1 + 0.2, 0.3))  # True -- correct way to compare floats
print(math.isclose(0.1 + 0.2, 0.3, rel_tol=1e-9, abs_tol=0.0))

# gcd / lcm (Python 3.9+ supports lcm; gcd takes *args since 3.9)
print(math.gcd(12, 18))         # 6
print(math.lcm(4, 6))           # 12
print(math.gcd(12, 18, 24))     # 6, multiple args supported

# combinatorics
print(math.comb(5, 2))   # 10 -- 5 choose 2
print(math.perm(5, 2))   # 20 -- permutations
print(math.factorial(5)) # 120

# infinity and nan
print(math.inf, -math.inf, math.nan)
print(math.isnan(math.nan), math.isinf(math.inf))
```

### Interview questions / gotchas

- Why is `0.1 + 0.2 != 0.3`? (IEEE-754 double precision cannot represent 0.1 or
  0.2 exactly in binary; use `math.isclose` or `Decimal` for exact comparisons.)
- Difference between `math.pow(x, y)` and `x ** y`? (`math.pow` always returns a
  float and doesn't support complex results; `**` can return int for int
  operands and handles negative bases raised to fractional powers differently.)
- `math.floor(-3.5)` vs `int(-3.5)` — floor rounds toward negative infinity
  (-4), `int()` truncates toward zero (-3).
- How would you compute gcd/lcm before Python 3.9? (`math.gcd` existed since
  3.5; `lcm` had to be derived as `a * b // math.gcd(a, b)`.)

## statistics

### What it's for

The `statistics` module provides basic descriptive statistics — mean, median,
mode, variance, standard deviation — implemented in pure Python with exact
arithmetic where possible (it uses `Fraction`/`Decimal` internally for
accuracy on `int`/`Decimal` inputs).

### Why/when it's used

- Quick aggregations on small-to-medium in-memory datasets (latency samples,
  A/B test summaries) without pulling in numpy/pandas as a dependency.
- When precision matters more than speed (numpy uses float64 and can
  accumulate rounding error on large datasets; `statistics` is more exact for
  exact-typed inputs).

```python
import statistics as st

data = [2, 4, 4, 4, 5, 5, 7, 9]

print(st.mean(data))              # 5.0
print(st.median(data))            # 4.5
print(st.mode(data))              # 4 (most common)
print(st.stdev(data))             # sample standard deviation
print(st.pstdev(data))            # population standard deviation
print(st.variance(data))          # sample variance

# statistics keeps precision for exact types
from fractions import Fraction
print(st.mean([Fraction(1, 3), Fraction(1, 6)]))  # 1/4 exact, no float error
```

### statistics vs numpy

| Aspect            | statistics module          | numpy                          |
|-------------------|-----------------------------|---------------------------------|
| Dependency        | stdlib, no install needed  | external package                |
| Performance       | pure Python, slow on large data | vectorized C, fast on large arrays |
| Precision         | exact for int/Fraction/Decimal | float64, faster but lossier |
| Use case          | small datasets, scripts, quick reports | large numeric arrays, ML pipelines |

### Interview questions / gotchas

- When would `statistics.mean` be preferable to `numpy.mean`? (Small data,
  no numpy dependency wanted, or exact arithmetic needed for `Decimal`/
  `Fraction` inputs.)
- `stdev` vs `pstdev` — sample (n-1 denominator, Bessel's correction) vs
  population (n denominator). Using the wrong one is a common mistake when
  computing standard deviation of a full population vs a sample.
- `statistics.mean([])` raises `StatisticsError` — must handle empty input.
- `mode` raises `StatisticsError` on ties in older Python (3.7), but from
  3.8+ `mode` returns the first most-common value and `multimode` returns all.

## random

### What it's for

`random` generates pseudo-random numbers using the Mersenne Twister PRNG. It's
deterministic given a seed, which makes it great for simulations, testing,
sampling, and shuffling — but it is **not cryptographically secure**.

### Why/when it's used

- Load testing / simulation (randomized traffic generation).
- Shuffling recommendation lists, sampling for A/B tests.
- Reproducible ML experiments (seeding for deterministic results).
- Never for tokens, passwords, or session IDs — use `secrets` for that.

```python
import random

random.seed(42)  # reproducibility: same seed -> same sequence

print(random.random())          # float in [0.0, 1.0)
print(random.randint(1, 10))    # int in [1, 10], inclusive both ends
print(random.randrange(0, 10, 2))  # even numbers 0,2,4,6,8

items = ["a", "b", "c", "d", "e"]
print(random.choice(items))         # single random element
print(random.sample(items, k=3))    # 3 unique elements, no replacement
print(random.choices(items, k=3))   # 3 elements, WITH replacement (repeats OK)

random.shuffle(items)   # shuffles in place
print(items)

# weighted choice
print(random.choices(items, weights=[10, 1, 1, 1, 1], k=1))
```

### random vs secrets

```python
import secrets

# WRONG for security-sensitive code:
insecure_token = "".join(random.choices("abcdef0123456789", k=32))

# RIGHT: secrets uses os.urandom (CSPRNG) under the hood
secure_token = secrets.token_hex(16)      # 32 hex chars, 16 bytes of entropy
secure_url_token = secrets.token_urlsafe(16)
api_key = secrets.token_bytes(32)
print(secrets.choice(["a", "b", "c"]))     # cryptographically secure choice
```

### Interview questions / gotchas

- Why is `random` unsuitable for generating password reset tokens or session
  IDs? (Mersenne Twister is deterministic and its internal state can be
  recovered from enough outputs, letting an attacker predict future values;
  `secrets`/`os.urandom` pulls from the OS CSPRNG.)
- `random.sample` vs `random.choices`: sample is without replacement (errors
  if k > population size unless using `counts`), choices is with replacement.
- How do you get reproducible results across runs? (`random.seed(n)` at the
  start; note this only guarantees reproducibility within the same Python/
  library version — algorithm changes between versions can change output.)
- Is `random.random()` thread-safe? Yes, the module-level functions use a
  global `Random` instance guarded appropriately, but for parallel
  reproducible streams you should create separate `random.Random(seed)`
  instances per thread/process.

## datetime

### What it's for

`datetime` models dates, times, and the arithmetic between them. The most
important concept is **naive vs aware** datetimes — naive objects carry no
timezone info, aware ones do.

### Why/when it's used

- Any system that logs timestamps, schedules jobs, or shows times to users
  across timezones (literally every backend service).
- Computing durations/expirations (JWT expiry, cache TTLs, SLA windows).

```python
from datetime import datetime, date, time, timedelta, timezone

# naive datetime -- no timezone info, ambiguous in distributed systems
naive = datetime.now()
print(naive, naive.tzinfo)  # tzinfo is None

# aware datetime -- always store/compare these in backend systems
aware_utc = datetime.now(timezone.utc)
print(aware_utc, aware_utc.tzinfo)

# constructing aware datetimes explicitly
dt = datetime(2026, 8, 1, 12, 30, tzinfo=timezone.utc)

# timedelta arithmetic
one_day = timedelta(days=1)
tomorrow = aware_utc + one_day
print(tomorrow - aware_utc == one_day)  # True

# converting between timezones (3.9+ recommended: zoneinfo)
from zoneinfo import ZoneInfo
ist = aware_utc.astimezone(ZoneInfo("Asia/Kolkata"))
print(ist)

# formatting and parsing
formatted = aware_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
print(formatted)
parsed = datetime.strptime("2026-08-01 12:30:00", "%Y-%m-%d %H:%M:%S")
print(parsed)

# comparing naive and aware raises TypeError
try:
    naive < aware_utc
except TypeError as e:
    print("error:", e)

# epoch conversions -- common in APIs
epoch_seconds = aware_utc.timestamp()
back = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
```

### Common pitfalls

- Mixing naive and aware datetimes causes `TypeError: can't compare
  offset-naive and offset-aware datetimes`.
- `datetime.now()` uses local system time (naive); `datetime.utcnow()` is
  **deprecated** (returns naive UTC, easy to misuse) — prefer
  `datetime.now(timezone.utc)`.
- `strptime`/`strftime` format codes are locale- and platform-sensitive for
  things like `%p` (AM/PM) or `%a` (weekday abbreviation).
- Daylight saving time transitions can create ambiguous or nonexistent local
  times; use `zoneinfo` (3.9+) or `pytz` for correct DST-aware arithmetic
  rather than fixed UTC offsets.

### Interview questions / gotchas

- What's the difference between naive and aware datetimes, and why do
  distributed systems need aware ones? (Naive datetimes are ambiguous across
  timezones/servers; always store timestamps in UTC, convert to local only
  for display.)
- How do you safely add "1 month" to a date? (`timedelta` only supports
  fixed durations like days/seconds; month arithmetic needs
  `dateutil.relativedelta` or manual calendar logic because months have
  variable lengths.)
- Why prefer storing UTC epoch or ISO-8601 with offset in a database over
  naive local time? (Avoids DST ambiguity and makes cross-service comparison
  correct.)

## decimal

### What it's for

`Decimal` provides base-10 arbitrary-precision floating point arithmetic,
avoiding the binary floating-point representation errors of `float`.

### Why/when it's used

- Any monetary calculation — banking, billing, invoicing, e-commerce order
  totals (Amazon, Walmart, Flipkart checkout flows) — where cents must add up
  exactly and rounding must be explicit and controllable.
- Anywhere regulatory/financial precision matters more than raw speed.

```python
from decimal import Decimal, getcontext, ROUND_HALF_UP

# float imprecision
print(0.1 + 0.2)              # 0.30000000000000004

# Decimal -- always construct from strings (or ints), not floats!
a = Decimal("0.1")
b = Decimal("0.2")
print(a + b)                  # Decimal('0.3') -- exact

bad = Decimal(0.1)            # constructing from float inherits its imprecision
print(bad)                    # Decimal('0.1000000000000000055511151231257827021181583404541015625')

# precision / context
getcontext().prec = 6
print(Decimal(1) / Decimal(3))   # 0.333333 (6 significant digits)

# money rounding
price = Decimal("19.995")
print(price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))  # 20.00

# arithmetic between Decimal and float raises TypeError
try:
    Decimal("1.1") + 2.2
except TypeError as e:
    print("error:", e)
print(Decimal("1.1") + Decimal(str(2.2)))  # convert float via str first
```

### Interview questions / gotchas

- Why can't `float` represent 0.1 exactly? (Binary floating point can only
  exactly represent sums of powers of 2; 0.1 in base 2 is a repeating
  fraction, so it's stored as the closest approximation.)
- Why must you construct `Decimal` from a string, not a float, for exact
  values? (`Decimal(0.1)` captures the float's existing binary imprecision;
  `Decimal("0.1")` is exact.)
- How do you control rounding behavior for currency? (`quantize()` with an
  explicit `rounding` mode like `ROUND_HALF_UP`; the default context rounding
  is `ROUND_HALF_EVEN`, i.e., banker's rounding, which surprises people.)
- Is `Decimal` slower than `float`? Yes — it's implemented for correctness,
  not speed, so it's reserved for financial/precision-critical paths, not
  hot numeric loops.

## fractions

### What it's for

`Fraction` represents rational numbers exactly as numerator/denominator pairs,
avoiding both binary float error and decimal rounding.

### Why/when it's used

- Exact ratio computations (e.g., aspect ratios, probability calculations,
  recipe scaling) where you need `1/3` to stay exactly `1/3`, not `0.333...`.
- Simplifying fractions automatically (`Fraction` reduces to lowest terms).

```python
from fractions import Fraction

f = Fraction(1, 3)
print(f)                       # 1/3
print(f + Fraction(1, 6))      # 1/2, exact, auto-reduced

# from float (careful -- inherits float imprecision)
print(Fraction(0.5))           # 1/2 -- exact because 0.5 is exactly representable
print(Fraction(0.1))           # a huge exact fraction representing float 0.1's real value

# from string is exact and intuitive
print(Fraction("1/3") + Fraction("1/6"))  # 1/2
print(Fraction("0.75"))                    # 3/4

# converting to float/decimal when needed for output
print(float(Fraction(1, 3)))   # 0.3333333333333333
```

### Interview questions / gotchas

- Why prefer `Fraction` over `float` for probability or ratio math in a
  simulation? (No accumulated rounding error across many operations.)
- `Fraction(0.1)` vs `Fraction("0.1")` — the first captures the *actual*
  binary float value of 0.1 (a large, ugly fraction), the second gives you
  the exact mathematical `1/10`. This is the same float-precision gotcha as
  `Decimal`.
- `Fraction` automatically reduces to lowest terms via gcd — useful in
  problems needing canonical fraction representation (e.g., LeetCode
  "Fraction to Recurring Decimal" style questions).

## pathlib

### What it's for

`pathlib.Path` is the modern, object-oriented way to work with filesystem
paths, replacing most `os.path` string manipulation with methods on a `Path`
object.

### Why/when it's used

- Any file I/O code — config loading, log rotation, build tooling, deployment
  scripts. Cleaner and less error-prone than string-concatenating paths.
- Cross-platform path handling (Windows backslashes vs POSIX slashes) is
  handled automatically.

```python
from pathlib import Path

p = Path("/tmp/data") / "reports" / "2026" / "summary.csv"
print(p)                     # /tmp/data/reports/2026/summary.csv (POSIX separators)
print(p.name)                # summary.csv
print(p.stem)                # summary
print(p.suffix)              # .csv
print(p.parent)              # /tmp/data/reports/2026
print(p.parts)                # ('/', 'tmp', 'data', 'reports', '2026', 'summary.csv')

# existence / type checks
print(p.exists(), p.is_file(), p.is_dir())

# creating directories and files
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text("col1,col2\n1,2\n")
print(p.read_text())

# globbing
for f in Path("/tmp/data").rglob("*.csv"):
    print(f)

# resolving absolute paths and symlinks
print(Path("./relative/path").resolve())

# joining with strings vs os.path
import os.path
old_style = os.path.join("/tmp/data", "reports", "summary.csv")
new_style = Path("/tmp/data") / "reports" / "summary.csv"
print(str(new_style) == old_style)
```

### pathlib vs os.path

| Aspect        | os.path                     | pathlib                          |
|---------------|------------------------------|-----------------------------------|
| API style     | functions on strings         | methods on Path objects           |
| Readability   | `os.path.join(a, b, c)`      | `Path(a) / b / c`                 |
| Chaining      | awkward                      | fluent (`.parent.parent / "x"`)   |
| Introspection | separate functions           | `.exists()`, `.is_file()`, etc.   |

### Interview questions / gotchas

- Why prefer `pathlib` over `os.path` in new code? (More readable, less
  error-prone concatenation via `/` operator, object methods for common
  checks, built-in globbing.)
- Does `Path.exists()` follow symlinks? Yes by default; use
  `is_symlink()` to detect a symlink itself.
- `Path.rglob("*.py")` vs `Path.glob("**/*.py")` — equivalent, `rglob` is
  shorthand for recursive glob.
- Gotcha: `Path` objects aren't interchangeable with `str` everywhere in
  older APIs — need `str(path)` for some third-party libraries that don't
  accept `os.PathLike`.

## os

### What it's for

`os` is the low-level interface to the operating system: environment
variables, process info, directory traversal, and (legacy) path manipulation.

### Why/when it's used

- Reading configuration/secrets from environment variables (12-factor apps).
- Walking a directory tree to process files (log ingestion, build pipelines).
- Getting process/user info for logging or diagnostics.

```python
import os

# environment variables
print(os.environ.get("HOME"))
os.environ["MY_FLAG"] = "1"          # only affects this process and its children
db_url = os.environ.get("DATABASE_URL", "sqlite:///default.db")  # default fallback

# os.path (legacy but still common)
print(os.path.join("a", "b", "c"))
print(os.path.exists("/tmp"))
print(os.path.splitext("archive.tar.gz"))  # ('archive.tar', '.gz')
print(os.path.abspath("."))

# walking a directory tree
for dirpath, dirnames, filenames in os.walk("/tmp"):
    for fname in filenames:
        full = os.path.join(dirpath, fname)
    break  # just show top-level for demo

# process info
print(os.getpid())          # current process ID
print(os.getcwd())          # current working directory
print(os.cpu_count())       # number of logical CPUs, useful for sizing worker pools

# running a command (prefer subprocess for anything nontrivial)
print(os.listdir("/tmp")[:5])
```

### Interview questions / gotchas

- `os.environ["KEY"]` vs `os.environ.get("KEY")` — the first raises
  `KeyError` if missing, the second returns `None` (or a default) — prefer
  `.get()` with sane defaults for optional config.
- `os.walk` is top-down by default; can be made bottom-up with
  `topdown=False`, useful when deleting directories after emptying them.
- How does `os.cpu_count()` inform designing a thread/process pool size?
  (CPU-bound work: pool size ~= cpu_count; I/O-bound: can go higher since
  threads spend time waiting.)
- `os.fork()` availability (POSIX only, not on Windows) — relevant for how
  `multiprocessing` behaves differently across platforms (see multiprocessing
  section: `fork` vs `spawn` start methods).

## sys

### What it's for

`sys` exposes interpreter-level state: command-line arguments, the module
search path, exit codes, and object introspection like memory size.

### Why/when it's used

- Parsing raw CLI args (though `argparse` is preferred for anything nontrivial).
- Debugging import issues via `sys.path`.
- Controlling process exit codes for scripts used in CI/CD pipelines.
- Estimating memory footprint of objects for performance tuning.

```python
import sys

# command line arguments
print(sys.argv)            # ['script.py', 'arg1', 'arg2', ...]

# module search path -- where "import x" looks
print(sys.path[:2])

# exiting with a status code (0 = success, nonzero = failure, used by CI)
def main():
    if len(sys.argv) < 2:
        print("usage: script.py <arg>", file=sys.stderr)
        sys.exit(1)
    return 0

# sys.exit raises SystemExit -- catchable, unlike os._exit
try:
    sys.exit(2)
except SystemExit as e:
    print("caught exit code:", e.code)

# memory size of objects
print(sys.getsizeof(42))          # size in bytes of an int object
print(sys.getsizeof("hello"))     # size of a str object
print(sys.getsizeof([1, 2, 3]))   # size of the list container (not its elements!)

# python version info
print(sys.version_info)
print(sys.platform)   # 'darwin', 'linux', 'win32', etc.
```

### Interview questions / gotchas

- `sys.exit()` vs `os._exit()` — `sys.exit` raises `SystemExit` (runs cleanup
  handlers, `finally` blocks, atexit); `os._exit` terminates immediately
  without cleanup, used in child processes after `fork()` to avoid running
  parent cleanup twice.
- `sys.getsizeof([1, 2, 3])` returns the size of the list object itself
  (pointers), not the recursive size of contained objects — a common trick
  question.
- Why would `import` fail even though the file exists? Check `sys.path` —
  the directory containing the module may not be on the path.
- `sys.argv[0]` is always the script name; real args start at index 1.

## shutil

### What it's for

`shutil` provides high-level file operations: copying, moving, and archiving
files/directories (things `os` doesn't do in one call).

### Why/when it's used

- Backup/deployment scripts (copying build artifacts, config files).
- Log rotation/archival (zipping old logs before deletion).
- Cleaning up temp workspaces.

```python
import shutil
from pathlib import Path

Path("/tmp/shutil_demo/src").mkdir(parents=True, exist_ok=True)
Path("/tmp/shutil_demo/src/file.txt").write_text("hello")

# copy a single file (copy2 preserves metadata like timestamps)
shutil.copy2("/tmp/shutil_demo/src/file.txt", "/tmp/shutil_demo/file_copy.txt")

# copy an entire directory tree
shutil.copytree("/tmp/shutil_demo/src", "/tmp/shutil_demo/src_backup", dirs_exist_ok=True)

# move / rename
shutil.move("/tmp/shutil_demo/file_copy.txt", "/tmp/shutil_demo/src_backup/file_copy.txt")

# disk usage
total, used, free = shutil.disk_usage("/tmp")
print(f"free space: {free // (1024**3)} GB")

# archiving (zip/tar)
shutil.make_archive("/tmp/shutil_demo_backup", "zip", "/tmp/shutil_demo")
shutil.unpack_archive("/tmp/shutil_demo_backup.zip", "/tmp/shutil_demo_unpacked")

# cleanup
shutil.rmtree("/tmp/shutil_demo")
shutil.rmtree("/tmp/shutil_demo_unpacked")
```

### Interview questions / gotchas

- `shutil.copy` vs `shutil.copy2` vs `shutil.copyfile` — `copy` preserves
  permission bits, `copy2` also preserves metadata (mtime, atime), `copyfile`
  copies only content, no metadata, and doesn't accept a directory as dst.
- `shutil.move` across filesystems falls back to copy+delete since a plain
  rename (`os.rename`) can't cross filesystem/device boundaries.
- `shutil.rmtree` is irreversible and dangerous — always validate the path
  isn't something like `/` or a user's home directory before calling it in
  automation scripts.

## tempfile

### What it's for

`tempfile` creates temporary files/directories safely — with unique names,
correct permissions, and automatic cleanup — avoiding race conditions from
hand-rolling "random filename in /tmp" logic.

### Why/when it's used

- Scratch space for processing uploads before moving to permanent storage.
- Test fixtures needing isolated filesystem state.
- Any place you'd be tempted to do `open("/tmp/myfile" + str(random.random()))`
  — that pattern is a security/race-condition bug.

```python
import tempfile
import os

# NamedTemporaryFile -- has a visible name on the filesystem, auto-deleted on close (by default)
with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=True) as f:
    f.write("a,b,c\n1,2,3\n")
    f.seek(0)
    print(f.read())
    print("exists during use:", os.path.exists(f.name))
print("exists after context exit:", os.path.exists(f.name))  # False, deleted

# TemporaryDirectory -- self-cleaning directory, great for test isolation
with tempfile.TemporaryDirectory() as tmpdir:
    path = os.path.join(tmpdir, "scratch.txt")
    with open(path, "w") as f:
        f.write("scratch data")
    print(os.listdir(tmpdir))
print("dir removed:", not os.path.exists(tmpdir))

# a plain unique temp file name (use with care)
fd, path = tempfile.mkstemp(suffix=".log")
os.close(fd)
os.remove(path)
```

### Security notes

- Always use `tempfile` module functions rather than constructing your own
  temp filenames — `tempfile` avoids predictable-name race conditions
  (TOCTOU: time-of-check to time-of-use attacks) by creating the file
  atomically with `O_EXCL`.
- On multi-user systems, `tempfile` sets restrictive permissions (owner-only)
  by default, unlike a naive `open("/tmp/x", "w")`.
- On Windows, `NamedTemporaryFile(delete=True)` can't be reopened by name
  while still held open by the same process — a common cross-platform gotcha;
  use `delete=False` and manually clean up if you need to reopen it.

### Interview questions / gotchas

- Why not just do `open(f"/tmp/tmp_{random.random()}")`? (Predictable name +
  race window between check and creation = security vulnerability; also
  doesn't guarantee automatic cleanup.)
- `NamedTemporaryFile` vs `TemporaryDirectory` — file for single scratch
  file needs, directory for multi-file scratch workspace (e.g., unzipping an
  archive to inspect contents).
- What happens to a `NamedTemporaryFile` if the process crashes before the
  `with` block exits? (OS-level temp cleanup on reboot handles orphaned
  files eventually, but the file may briefly leak until then — not a
  guaranteed instant cleanup.)

## logging

### What it's for

`logging` is the standard structured logging framework — loggers, handlers,
formatters, and levels (DEBUG/INFO/WARNING/ERROR/CRITICAL). Full coverage,
including handlers, formatters, structured/JSON logging, and best practices
for production services, is in `32_logging.md`. This is just a quick pointer
and minimal example so this file's context is self-contained.

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

logger.debug("this won't show, level is INFO")
logger.info("service started")
logger.warning("cache miss rate high: %.2f%%", 42.5)
try:
    1 / 0
except ZeroDivisionError:
    logger.exception("division failed")  # logs traceback automatically
```

See `32_logging.md` for handlers, log rotation, structured/JSON logging, and
per-module logger configuration.

## argparse

### What it's for

`argparse` builds command-line interfaces: positional/optional args, type
coercion, subcommands, help text, and validation — far more robust than
manually parsing `sys.argv`.

### Why/when it's used

- Internal tooling/scripts (deployment scripts, data migration tools, ETL
  jobs run from cron or CI) that need a real CLI with `--help`.
- Building multi-command tools (like `git <subcommand>`) via subparsers.

```python
import argparse

parser = argparse.ArgumentParser(description="User management CLI")
parser.add_argument("--verbose", action="store_true", help="enable verbose output")
parser.add_argument("--retries", type=int, default=3, help="number of retries")
parser.add_argument("username", help="target username")  # positional, required

subparsers = parser.add_subparsers(dest="command", required=True)

create_p = subparsers.add_parser("create", help="create a user")
create_p.add_argument("--email", type=str, required=True)

delete_p = subparsers.add_parser("delete", help="delete a user")
delete_p.add_argument("--force", action="store_true")

# simulate: myscript.py --verbose alice create --email alice@example.com
args = parser.parse_args(["--verbose", "alice", "create", "--email", "alice@example.com"])
print(args.username, args.command, args.email, args.verbose, args.retries)

if args.command == "create":
    print(f"creating user {args.username} with email {args.email}")
```

### Common patterns

```python
# choices restrict valid values
parser.add_argument("--env", choices=["dev", "staging", "prod"], default="dev")

# nargs for variable-length args
parser.add_argument("--tags", nargs="+")   # one or more values -> list

# mutually exclusive group
group = parser.add_mutually_exclusive_group()
group.add_argument("--quiet", action="store_true")
group.add_argument("--verbose", action="store_true")
```

### Interview questions / gotchas

- Why use `argparse` instead of manually indexing `sys.argv`? (Auto-generated
  `--help`, type validation/coercion, error messages, default values,
  subcommands — manual parsing reinvents all of this poorly.)
- How do you structure a CLI with multiple subcommands like `tool sync` and
  `tool status`? (`add_subparsers()`, dispatch on `args.command`.)
- `action="store_true"` vs `type=bool` — `type=bool` is a classic gotcha
  because `bool("False")` is `True` (any nonempty string is truthy); flags
  should use `action="store_true"/"store_false"` instead.

## threading

### What it's for

`threading` provides OS-level threads within a single process, sharing
memory. Due to the Global Interpreter Lock (GIL), only one thread executes
Python bytecode at a time, so threads help with I/O-bound concurrency, not
CPU-bound parallelism.

### Why/when it's used

- Concurrent I/O: multiple simultaneous network requests, file reads, or DB
  queries where threads spend most of their time waiting (GIL is released
  during I/O waits).
- Background tasks in a server process (e.g., a heartbeat thread) without the
  overhead of separate processes.

```python
import threading
import time

counter = 0
lock = threading.Lock()

def increment(n):
    global counter
    for _ in range(n):
        with lock:          # without this lock, this is a classic race condition
            counter += 1

threads = [threading.Thread(target=increment, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(counter)  # 400000, correct because of the lock

# Event for signaling between threads
stop_event = threading.Event()

def worker():
    while not stop_event.is_set():
        time.sleep(0.1)
    print("worker stopping")

t = threading.Thread(target=worker)
t.start()
time.sleep(0.3)
stop_event.set()
t.join()

# RLock -- reentrant lock, same thread can acquire it multiple times
rlock = threading.RLock()
def recursive(n):
    with rlock:
        if n > 0:
            recursive(n - 1)
recursive(5)  # would deadlock with a plain Lock if re-acquired by same thread
```

### GIL interaction

The GIL means CPU-bound Python code doesn't get real parallelism from
threads — one thread runs bytecode while others wait, even on multi-core
CPUs. Threads *do* help for I/O-bound work because the GIL is released
during blocking I/O calls (file/network/DB), letting other threads run.

### Interview questions / gotchas

- Why doesn't `threading` speed up CPU-bound work in CPython? (The GIL
  serializes bytecode execution; use `multiprocessing` or a C-extension/
  numpy that releases the GIL for true CPU parallelism.)
- `Lock` vs `RLock` — RLock allows the same thread to acquire it multiple
  times (tracks owner + count); plain `Lock` deadlocks if reacquired by the
  owning thread.
- What's a race condition, and how does `with lock:` prevent it? (Concurrent
  unsynchronized read-modify-write on shared state; the lock ensures mutual
  exclusion around the critical section.)
- How would you gracefully stop a long-running thread? (Cooperative
  cancellation via `threading.Event`, since Python has no safe forced-thread-
  kill API.)

## multiprocessing

### What it's for

`multiprocessing` spawns separate OS processes, each with its own Python
interpreter and memory space — sidestepping the GIL entirely, giving true
parallelism for CPU-bound work at the cost of higher memory use and
inter-process communication (IPC) overhead.

### Why/when it's used

- CPU-bound work: image/video processing, numeric computation, data
  transformation pipelines that need multiple cores.
- Isolating crashes/faults per worker (one process crashing doesn't take down
  others).

```python
import multiprocessing as mp
import time

def cpu_bound_task(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

if __name__ == "__main__":
    # Process -- explicit, low-level
    p = mp.Process(target=cpu_bound_task, args=(10_000_000,))
    p.start()
    p.join()

    # Pool -- higher-level, manages a fixed worker pool, distributes work
    with mp.Pool(processes=4) as pool:
        results = pool.map(cpu_bound_task, [5_000_000] * 4)
        print(results)

    # shared memory for cross-process state (avoids pickling overhead for simple types)
    shared_counter = mp.Value("i", 0)   # 'i' = C int
    shared_array = mp.Array("d", [0.0] * 5)  # 'd' = C double

    def bump(counter):
        with counter.get_lock():
            counter.value += 1

    procs = [mp.Process(target=bump, args=(shared_counter,)) for _ in range(10)]
    for pr in procs: pr.start()
    for pr in procs: pr.join()
    print(shared_counter.value)  # 10
```

### threading vs multiprocessing (quick contrast)

- Threads share memory (fast communication, but GIL-limited for CPU work,
  need locks for shared state).
- Processes have isolated memory (no GIL contention, real parallel CPU
  execution, but IPC is slower — requires pickling data to pass between
  processes — and startup overhead is higher).

### Interview questions / gotchas

- Why use `multiprocessing` instead of `threading` for CPU-bound work?
  (Bypasses the GIL — each process has its own interpreter/GIL, so cores are
  actually used in parallel.)
- What is the `fork` vs `spawn` start method distinction? (`fork` — POSIX
  only, copies the parent process memory, fast but can cause subtle bugs with
  inherited state like open file descriptors or threads; `spawn` — starts a
  fresh interpreter, safer/more portable, default on Windows and macOS
  (3.8+), but slower to start and requires objects to be picklable.)
- Why must `Pool`/`Process` code be guarded by
  `if __name__ == "__main__":` on Windows/spawn? (Without it, the spawned
  child re-imports the module and re-executes top-level code, causing
  infinite recursive process spawning.)
- How do processes share data since memory isn't shared? (`Value`/`Array`
  for simple shared C-typed data, `Queue`/`Pipe` for message passing,
  `Manager` for shared Python objects like dicts/lists via a proxy server
  process — all involve serialization/IPC overhead compared to threads.)

## asyncio

### What it's for

`asyncio` provides single-threaded cooperative concurrency via an event loop,
coroutines (`async def`), and `await`. It excels at massively concurrent
I/O-bound workloads (thousands of open connections) without the memory
overhead of one-thread/one-connection.

### Why/when it's used

- High-concurrency network servers/clients (web servers, API gateways, chat
  systems, web scrapers) where you're mostly waiting on network I/O.
- When you need to manage thousands of concurrent connections cheaply — real
  OS threads would be too memory-heavy per connection.

```python
import asyncio
import time

async def fetch(name, delay):
    print(f"{name} starting")
    await asyncio.sleep(delay)   # non-blocking sleep -- yields control to event loop
    print(f"{name} done")
    return f"{name} result"

async def main():
    start = time.perf_counter()

    # sequential -- takes sum of delays
    # await fetch("A", 1); await fetch("B", 1)

    # concurrent -- takes max of delays, since both run "at once" cooperatively
    results = await asyncio.gather(
        fetch("A", 1),
        fetch("B", 1),
        fetch("C", 1),
    )
    print(results)
    print(f"elapsed: {time.perf_counter() - start:.2f}s")  # ~1s, not 3s

    # timeouts
    try:
        await asyncio.wait_for(fetch("slow", 5), timeout=1)
    except asyncio.TimeoutError:
        print("timed out waiting for slow task")

    # creating tasks that run in the background
    task = asyncio.create_task(fetch("background", 2))
    await asyncio.sleep(0.5)
    print("doing other work while background task runs")
    await task

asyncio.run(main())
```

### asyncio vs threads/processes

- `asyncio` is single-threaded — concurrency comes from cooperative yielding
  at `await` points, so there's no need for locks around shared state
  between coroutines (no preemption mid-statement), simplifying reasoning
  about races, but a single CPU-bound `await`-free coroutine blocks
  everything else on the event loop.
- Choose `asyncio` over threads when you need very high connection counts
  (thousands) with mostly I/O waiting and your I/O libraries are async-native
  (aiohttp, asyncpg, etc.). Choose threads when working with blocking/legacy
  libraries you can't rewrite as async.
- Choose `multiprocessing` (or `asyncio` + `run_in_executor` for a mix) when
  the work is CPU-bound.

### Interview questions / gotchas

- Why doesn't `asyncio` need locks the way `threading` does for shared
  in-memory state? (Only one coroutine runs at a time on the event loop; a
  context switch only happens at explicit `await` points, not mid-statement,
  so there's no risk of two coroutines interleaving in the middle of a
  non-await-containing critical section.)
- What happens if you call a blocking function (e.g., `time.sleep` or a
  synchronous `requests.get`) inside a coroutine? (It blocks the entire
  event loop — nothing else runs until it returns; use
  `await asyncio.sleep()` / async HTTP clients, or offload blocking calls to
  a thread pool via `loop.run_in_executor`.)
- `asyncio.gather` vs `asyncio.create_task` — `gather` runs and awaits
  multiple awaitables concurrently and collects results; `create_task`
  schedules a coroutine to run in the background immediately, letting you do
  other work before awaiting it.
- When is asyncio the wrong tool? (CPU-bound work — it doesn't give
  parallelism, just concurrency on a single thread.)

## concurrent.futures

### What it's for

`concurrent.futures` gives a unified high-level API — `Executor`, `Future` —
over both thread pools (`ThreadPoolExecutor`) and process pools
(`ProcessPoolExecutor`), so you can swap concurrency strategy with minimal
code changes.

### Why/when it's used

- Simpler alternative to raw `threading`/`multiprocessing` when you just need
  "run these N things concurrently and collect results," especially with
  `map()` or `as_completed()`.
- Good default choice for bounded parallel work (parallel API calls, parallel
  file processing) without manually managing thread/process lifecycles.

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import time

def io_task(n):
    time.sleep(0.5)
    return n * 2

def cpu_task(n):
    return sum(i * i for i in range(n))

# ThreadPoolExecutor -- good for I/O-bound work
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(io_task, i) for i in range(4)]
    for future in as_completed(futures):
        print("thread result:", future.result())

    # map() -- simpler, preserves input order in output
    results = list(executor.map(io_task, range(4)))
    print(results)

# ProcessPoolExecutor -- good for CPU-bound work
if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(cpu_task, n): n for n in [10**6, 10**6, 10**6]}
        for future in as_completed(futures):
            n = futures[future]
            print(f"cpu_task({n}) = {future.result()}")

# handling exceptions raised inside the worker
with ThreadPoolExecutor() as executor:
    future = executor.submit(lambda: 1 / 0)
    try:
        future.result()
    except ZeroDivisionError:
        print("caught exception from worker thread")
```

### Interview questions / gotchas

- `ThreadPoolExecutor` vs `ProcessPoolExecutor` — same API, but threads share
  memory (subject to GIL, cheap to start) while processes don't (bypass GIL,
  expensive to start, args/results must be picklable).
- `executor.map()` vs `as_completed(futures)` — `map` returns results in
  submission order (blocks in order even if a later one finishes first);
  `as_completed` yields futures as they finish, useful for reacting to the
  fastest results first.
- How do you get exceptions raised inside a worker? (`future.result()`
  re-raises them in the calling thread — don't forget to call `.result()` or
  exceptions can silently vanish if you never retrieve it.)
- Why prefer `concurrent.futures` over raw `threading`/`multiprocessing` for
  typical "fan out N tasks, collect results" code? (Less boilerplate, unified
  API, automatic pool lifecycle management via context manager.)

## subprocess

### What it's for

`subprocess` runs external commands/processes from Python, capturing their
stdout/stderr/return codes — the modern replacement for `os.system`/`os.popen`.

### Why/when it's used

- Invoking external tools/binaries (git, ffmpeg, compilers, shell scripts)
  from a Python orchestration/deployment/CI script.
- Wrapping legacy CLI tools as part of a larger pipeline.

```python
import subprocess

# run() -- high-level, blocks until command completes, since Python 3.5
result = subprocess.run(
    ["echo", "hello world"],
    capture_output=True,
    text=True,          # decode stdout/stderr as str instead of bytes
    check=True,          # raise CalledProcessError on nonzero exit code
)
print(result.stdout.strip())     # "hello world"
print(result.returncode)         # 0

# capturing both streams and handling failures
try:
    subprocess.run(["ls", "/nonexistent_path"], check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    print("failed:", e.returncode, e.stderr.strip())

# passing input to stdin
result = subprocess.run(["cat"], input="piped input\n", capture_output=True, text=True)
print(result.stdout)

# Popen -- low-level, for streaming output or long-running processes
with subprocess.Popen(["ping", "-c", "3", "127.0.0.1"], stdout=subprocess.PIPE, text=True) as proc:
    for line in proc.stdout:
        print("streamed:", line.strip())

# timeouts
try:
    subprocess.run(["sleep", "5"], timeout=1)
except subprocess.TimeoutExpired:
    print("command timed out")
```

### shell=True security risk

```python
# DANGEROUS: never build shell=True commands from untrusted/user input
user_input = "somefile.txt; rm -rf /"  # attacker-controlled string
# subprocess.run(f"cat {user_input}", shell=True)  # command injection!

# SAFE: pass args as a list, no shell interpretation, no injection risk
subprocess.run(["cat", user_input])  # treats the whole string as one filename argument
```

### Interview questions / gotchas

- Why is `shell=True` with string-formatted user input dangerous? (The
  string is passed to a shell, so metacharacters like `;`, `|`, `&&`,
  backticks allow arbitrary command injection; always use `shell=False`
  (default) with a list of args, or rigorously sanitize/quote if `shell=True`
  is unavoidable.)
- `subprocess.run` vs `Popen` — `run` is a blocking convenience wrapper
  built on top of `Popen`; use `Popen` directly when you need to stream
  output line-by-line while the process runs, or manage multiple concurrent
  subprocesses manually.
- What does `check=True` do, and why is it important? (Raises
  `CalledProcessError` on nonzero exit code — without it, failures silently
  return a nonzero `returncode` that's easy to ignore.)
- How do you avoid deadlocks when a subprocess produces large output on both
  stdout and stderr? (Use `subprocess.run(..., capture_output=True)`, which
  internally handles reading both streams concurrently; manually wiring
  `Popen` with `PIPE` for both and only reading one can deadlock once the OS
  pipe buffer fills.)

## Comparison table: threading vs multiprocessing vs asyncio vs concurrent.futures

| Dimension | threading | multiprocessing | asyncio | concurrent.futures |
|---|---|---|---|---|
| Concurrency model | OS threads, shared memory | OS processes, isolated memory | single-threaded event loop, cooperative coroutines | wraps threads OR processes behind one API |
| GIL impact | Serialized bytecode execution; GIL released during I/O | Bypassed entirely (separate interpreters) | N/A — single thread, no parallel bytecode execution anyway | Same as underlying executor (Thread or Process) |
| Best for | I/O-bound work with blocking/legacy libraries | CPU-bound work needing real parallel cores | Very high-concurrency I/O-bound work with async-native libraries | Simple "fan out and collect" tasks, either I/O or CPU-bound |
| Parallelism for CPU-bound work | No (GIL-limited) | Yes (true parallel cores) | No (single thread) | Yes, if using ProcessPoolExecutor |
| Memory overhead | Low (shared memory, ~cheap threads) | High (separate memory per process, IPC serialization cost) | Very low (coroutines are cheap, no OS thread per task) | Same as underlying executor |
| Shared state complexity | Needs locks (Lock/RLock) around shared mutable state | No shared state by default; needs Value/Array/Queue/Manager + IPC | No locks needed for in-process state (cooperative, single-threaded) | Depends on executor type (thread needs locks, process doesn't share) |
| Startup cost | Low | Higher (process spawn/fork cost) | Very low (just a coroutine object) | Depends on executor type |
| Typical use case examples | Concurrent blocking DB/API calls, background heartbeat thread | Image/video processing, numeric simulations, ML preprocessing | High-concurrency web server/client, chat backend, scraping thousands of URLs | Parallel file processing, batch API calls, parallel test execution |
| Error handling | Exceptions in thread don't propagate automatically; must check manually or via Future | Exceptions must be picklable to cross process boundary; propagate via Future | Exceptions propagate naturally via await/try-except | future.result() re-raises worker exceptions in caller |
| Scales to how many concurrent units | Hundreds (threads are relatively cheap but not free) | Bounded by CPU cores (diminishing returns beyond core count) | Thousands to tens of thousands of coroutines | Depends on chosen executor's limits |

### Rule of thumb

- I/O-bound, need to reuse blocking/synchronous libraries -> `threading` or
  `ThreadPoolExecutor`.
- I/O-bound, need very high concurrency and have async-native libraries
  available -> `asyncio`.
- CPU-bound, need real parallel execution across cores -> `multiprocessing`
  or `ProcessPoolExecutor`.
- Want a simple, uniform "submit tasks, collect results" API and don't want
  to hand-roll thread/process lifecycle management -> `concurrent.futures`,
  choosing `ThreadPoolExecutor` or `ProcessPoolExecutor` based on whether the
  workload is I/O-bound or CPU-bound.
