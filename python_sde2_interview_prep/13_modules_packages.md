# Modules & Packages

## Introduction

Python organizes code into modules (single `.py` files) and packages (directories of modules). Understanding the import system deeply — how Python finds, loads, and caches modules — is a common SDE-2 topic because it touches build systems, deployment, circular-import bugs, and packaging in production services at companies like Google, Amazon, Microsoft, Atlassian, Uber, Flipkart, Walmart, and Adobe.

---

## The Import System

### `sys.path` and Module Resolution

**Explanation:** When you write `import foo`, Python searches a list of directories stored in `sys.path` to locate `foo`. `sys.path` is built at interpreter startup from: (1) the directory containing the script being run (or `''` for the interactive interpreter), (2) the `PYTHONPATH` environment variable, (3) installation-dependent default paths (standard library, `site-packages`). The search order matters — the first matching module wins, which is a classic source of shadowing bugs (e.g., a local file named `json.py` shadowing the stdlib `json` module).

**Why it matters / internals:** Import resolution uses "finders" and "loaders" (PEP 302/451). `sys.meta_path` holds finder objects that are consulted in order: built-in module finder, frozen importer, and `PathFinder` (which walks `sys.path`). Each entry in `sys.path` may have an associated "path importer cache" (`sys.path_importer_cache`) to avoid re-scanning directories. Understanding this helps debug `ModuleNotFoundError` in Docker containers, Lambda functions, or CI pipelines where `sys.path` differs from local dev.

```python
import sys
import os

# Inspect the current search path
for p in sys.path:
    print(p)

# Dynamically add a directory (common in scripts/tests)
sys.path.insert(0, os.path.abspath("../lib"))

# PYTHONPATH env var also contributes to sys.path
print(os.environ.get("PYTHONPATH"))

import json
print(json.__file__)  # confirms which json module got picked up
```

**Common interview questions / gotchas:**
- "Why does `import foo` work locally but fail in production?" — usually a `sys.path` / working-directory mismatch, or missing `PYTHONPATH` in the deployment environment.
- "What happens if two packages on `sys.path` have the same top-level name?" — the first one found (by `sys.path` order) wins silently; no error.
- Modifying `sys.path` at runtime is a common (if hacky) fix for monorepos/test discovery — interviewers probe whether you know the cleaner alternative (proper packaging, `pip install -e .`, `PYTHONPATH`).

**Pitfalls:**
- Naming your own file the same as a stdlib module (`random.py`, `email.py`, `types.py`) silently breaks imports for that file and anything importing the real module.
- Relying on `sys.path.insert(0, ...)` hacks in production code instead of proper packaging.
- Forgetting that the script's own directory is prepended to `sys.path[0]`, which can cause different behavior when running `python script.py` vs `python -m package.script`.

---

### Module Caching in `sys.modules`

**Explanation:** Once a module is imported, Python stores it in the `sys.modules` dict keyed by its fully qualified name. Subsequent `import` statements for the same module do **not** re-execute the module's code — they just bind the name to the cached module object. This is why global state initialized at module import time (e.g., a database connection pool) is created exactly once per process.

**Why it matters / internals:** This caching is what makes modules singletons within a process. It also explains circular imports: if module A imports module B while B is still being initialized (partially in `sys.modules` but not fully executed), you can get `AttributeError` because B's namespace is incomplete at that point.

```python
import sys

import collections
print("collections" in sys.modules)  # True after first import

# Force re-execution of a module (rarely needed, mostly for tests/hot-reload)
import importlib
import collections
importlib.reload(collections)

# Manually inspect a cached module
mod = sys.modules["collections"]
print(mod.OrderedDict)

# Deleting from cache forces a fresh import next time
del sys.modules["collections"]
import collections  # re-executes module top-level code
```

**Common interview questions / gotchas:**
- "Is a module executed once or every time it's imported?" — once per process; cached in `sys.modules`.
- "How would you hot-reload a module in a long-running service?" — `importlib.reload()`, but warn about stale references held by other modules (old bound functions/classes still point to the old code object unless re-imported everywhere).
- Explain a circular import failure using `sys.modules` partial-population reasoning.

**Pitfalls:**
- `importlib.reload()` only updates the module object in place; any `from module import name` bindings elsewhere are **not** updated — they still reference the old object.
- Assuming module-level code runs fresh on every `import` — it does not, unless explicitly reloaded or removed from `sys.modules`.
- Multiprocessing: each child process gets its own `sys.modules` (own interpreter), so global module state is not shared across processes, only within a process/thread.

---

## Absolute Imports

**Explanation:** An absolute import specifies the full path from the project's top-level package, e.g., `from mypackage.subpackage.module import func`. Since Python 3 (PEP 328), all imports are absolute by default unless explicitly written as relative (with leading dots).

**Why it matters:** Absolute imports are unambiguous, easy to grep, and behave the same regardless of which module does the importing. They're the recommended style (PEP 8) for readability and refactor-safety, especially in large codebases with deep package trees, which is standard at big-tech scale (monorepos at Google/Uber, service repos at Amazon).

```python
# Project layout:
# myapp/
#   __init__.py
#   utils/
#     __init__.py
#     strings.py
#   services/
#     __init__.py
#     order_service.py

# services/order_service.py
from myapp.utils.strings import slugify   # absolute import
import myapp.utils.strings as strutils    # also absolute

def make_slug(title):
    return slugify(title)
```

**Common interview questions / gotchas:**
- "Absolute vs relative imports — when would you choose each?" Absolute for clarity/refactor-safety; relative for tight intra-package coupling that might get renamed/moved as a unit.
- Absolute imports require the top-level package to be importable (on `sys.path` or installed) — a common CI failure is running `pytest` from the wrong directory so `myapp` isn't found.

**Pitfalls:**
- Long absolute import chains can become unwieldy in deeply nested packages; some teams alias with `import ... as ...`.
- If the project isn't installed (`pip install -e .`) or the root isn't on `sys.path`, absolute imports fail with `ModuleNotFoundError` even though the code "looks right."

---

### Relative Imports

**Explanation:** Relative imports use leading dots to reference modules relative to the current module's package: single dot (`.`) means the same package, double dot (`..`) means the parent package, etc. They only work inside a package (a module that is part of a package hierarchy, not run directly as `__main__`).

**Why it matters / internals:** Relative imports are resolved using the importing module's `__package__` (or `__name__` for packages) attribute, not the filesystem path directly. This is why running a module directly as a script (`python mypackage/module.py`) breaks relative imports — as `__main__`, the module has no package context.

```python
# myapp/services/order_service.py
from . import order_repository        # same package (myapp.services)
from .. import config                  # parent package (myapp)
from ..utils.strings import slugify    # sibling package

# myapp/services/__init__.py
from .order_service import OrderService
```

**Common interview questions / gotchas:**
- "Why does `python myapp/services/order_service.py` raise `ImportError: attempted relative import with no known parent package`?" — because running a file directly sets `__name__ == "__main__"` with no package context; must run via `python -m myapp.services.order_service` instead.
- "How many dots can you use?" — as many as needed to walk up the package hierarchy, but PEP 8 discourages going beyond one or two levels for readability.

**Pitfalls:**
- Mixing relative imports with running the file as a script — always run package code via `-m` or through an installed entry point.
- Circular relative imports between sibling modules in the same package are just as possible as with absolute imports and equally hard to debug.
- Relative imports cannot cross outside the top-level package (e.g., can't `..` past the root package).

---

## `__name__` and `__main__`

**Explanation:** Every module has a `__name__` attribute. When a file is run directly as the entry point, Python sets `__name__ = "__main__"`. When the same file is imported as a module, `__name__` is set to its fully qualified module name. The `if __name__ == "__main__":` idiom lets a file be both an importable library and a runnable script.

**Why it matters:** This pattern is essential for testable code — you can `import` a module in unit tests without triggering its "script" behavior (like starting a server or parsing CLI args).

```python
# calc.py
def add(a, b):
    return a + b

def main():
    import sys
    a, b = int(sys.argv[1]), int(sys.argv[2])
    print(add(a, b))

if __name__ == "__main__":
    main()
```

```python
# test_calc.py — importing calc.py does NOT run main()
import calc
assert calc.add(2, 3) == 5
```

**Common interview questions / gotchas:**
- "What's the purpose of `if __name__ == '__main__':`?" — allows dual-purpose script/library files, and prevents side effects on import.
- "What is `__name__` set to for a package's `__init__.py`?" — the package's dotted name, e.g., `myapp.utils`.
- Running with `python -m package.module` sets `__name__` to `"__main__"` too, but still respects package context for relative imports — a nuance worth knowing.

**Pitfalls:**
- Forgetting the guard and having import-time side effects (network calls, argument parsing) fire when the module is merely imported (e.g., by test collection), causing flaky or slow test suites.
- Assuming `__name__` is always the file name — it's the *module* name, which includes package prefixes when imported normally.

---

## `__all__`

**Explanation:** `__all__` is a list (or tuple) of strings defined at module level that controls what `from module import *` exposes. It does not affect explicit imports like `from module import specific_name` or `import module`.

**Why it matters:** It documents and enforces the public API surface of a module, preventing internal helper names from leaking via wildcard imports. It's also read by some IDEs/linters and documentation tools to determine public symbols.

```python
# stringutils.py
__all__ = ["slugify", "truncate"]

def slugify(text):
    return text.lower().replace(" ", "-")

def truncate(text, length=10):
    return text[:length]

def _internal_helper():  # not exported via *
    pass
```

```python
from stringutils import *
print(slugify("Hello World"))   # works
print(_internal_helper)         # NameError: not imported by *
```

**Common interview questions / gotchas:**
- "Does `__all__` prevent `from module import _internal_helper`?" — no, explicit imports always work; `__all__` only restricts `import *`.
- "Is `import *` recommended?" — generally discouraged in production code (namespace pollution, unclear provenance of names); `__all__` is a mitigation, not an endorsement.
- Interviewers sometimes ask you to spot that a module lacks `__all__` and `import *` pulled in unexpected names.

**Pitfalls:**
- Forgetting to update `__all__` when adding/removing public functions, causing it to drift from reality.
- Believing `__all__` provides access control/privacy — it's purely a wildcard-import filter, not enforced encapsulation (Python has no true private members).

---

## Package Structure

### Regular Packages and `__init__.py`

**Explanation:** A regular package is a directory containing an `__init__.py` file. The presence of `__init__.py` (even empty) historically marked a directory as an importable package. `__init__.py` runs when the package is first imported and can be used to define package-level API, run initialization code, or set `__all__` for `from package import *`.

**Why it matters / internals:** `__init__.py` is where teams commonly re-export submodule symbols to create a clean public API, e.g. `from .order_service import OrderService` inside `myapp/services/__init__.py` so callers can do `from myapp.services import OrderService` instead of reaching into submodules directly.

```python
# myapp/services/__init__.py
from .order_service import OrderService
from .payment_service import PaymentService

__all__ = ["OrderService", "PaymentService"]

# consumer code
from myapp.services import OrderService  # clean public API
```

**Common interview questions / gotchas:**
- "What runs when you import a package?" — the package's `__init__.py`, top to bottom, before any submodule you explicitly imported.
- "Is `__init__.py` required in Python 3?" — no, thanks to namespace packages (see below), but it's still the recommended way to define regular packages with explicit APIs.
- Explain why heavy imports inside `__init__.py` (e.g., importing every submodule eagerly) can slow down startup for large packages — relevant to service cold-start times.

**Pitfalls:**
- Putting expensive computation or I/O in `__init__.py`, causing slow imports for any consumer, even those who only need one submodule.
- Circular imports caused by `__init__.py` importing from a submodule that itself imports the parent package.
- Forgetting `__init__.py` in older tooling/Python 2 compatibility contexts, breaking package discovery.

---

### Namespace Packages (PEP 420)

**Explanation:** Since Python 3.3, a directory *without* `__init__.py` can still act as a package — a "namespace package." Namespace packages allow a single logical package's contents to be split across multiple directories/distributions (found by `sys.path`) and merged at import time.

**Why it matters / internals:** Namespace packages are used by large plugin ecosystems and monorepos where multiple independently-installed distributions contribute to the same top-level namespace (e.g., `google.cloud.storage` and `google.cloud.pubsub` shipped as separate wheels but both under `google.cloud`). Python's import system detects the absence of `__init__.py`, then uses `PathFinder`'s namespace-package machinery to create a `_NamespacePath` that aggregates matching directories from all of `sys.path`.

```python
# Two separately installed distributions:
# dist_a/google/cloud/storage/__init__.py
# dist_b/google/cloud/pubsub/__init__.py
# Neither dist_a/google/cloud/ nor dist_b/google/cloud/ has __init__.py

import google.cloud.storage
import google.cloud.pubsub
# Both resolve under the shared namespace package "google.cloud"

print(google.cloud.__path__)  # a _NamespacePath, aggregating both locations
```

**Common interview questions / gotchas:**
- "How does Python know a directory is a namespace package vs just a random folder?" — if no `__init__.py` is found but the directory name matches during `PathFinder` search across `sys.path` entries, it's treated as a namespace package portion.
- "Can you mix a regular package and a namespace package with the same name?" — the regular package (with `__init__.py`) takes precedence once found; behavior can be surprising/fragile if both exist on `sys.path`.
- Good follow-up: "Why might a namespace package import silently succeed but be missing expected submodules?" — because it only aggregates directories currently on `sys.path`; a missing wheel install means a silently incomplete namespace.

**Pitfalls:**
- Accidentally creating a namespace package by forgetting `__init__.py`, then being confused when `dir(package)` looks empty and IDE autocomplete fails.
- Namespace packages have no `__init__.py`, so no package-level initialization code or `__all__` can be centrally defined for the whole namespace.
- Debugging is harder: `import` errors can be silent/partial since multiple directories are merged rather than a single clear source of truth.

---

## Virtual Environments

### `venv` and `pip`

**Explanation:** A virtual environment is an isolated Python installation (its own `site-packages`, sometimes its own interpreter symlink) that lets a project have its own dependency versions independent of the system Python or other projects. `venv` (stdlib, Python 3.3+) creates one; `pip` installs packages into the active environment.

**Why it matters:** Avoids "dependency hell" — different services in a company (e.g., a Flask API vs a data pipeline) often need conflicting versions of the same library (e.g., `numpy 1.x` vs `2.x`). Virtual environments are the baseline hygiene expected of any SDE-2 in day-to-day work and CI setup.

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it (Unix/macOS)
source .venv/bin/activate

# Activate it (Windows)
# .venv\Scripts\activate

# Install packages into the isolated environment
pip install requests==2.31.0

# Freeze exact versions for reproducibility
pip freeze > requirements.txt

# Recreate the same environment elsewhere
pip install -r requirements.txt

deactivate
```

```python
# Programmatically checking if you're inside a venv
import sys
in_venv = sys.prefix != sys.base_prefix
print("Running inside a virtual environment:", in_venv)
```

**Common interview questions / gotchas:**
- "How does `venv` achieve isolation without copying the whole interpreter?" — it creates a lightweight directory with `pyvenv.cfg`, a `bin/`(or `Scripts/`) with symlinked/copied interpreter, and its own `site-packages`; `sys.prefix` is redirected so package lookups go to the venv's `site-packages` first.
- "Difference between `venv` and `virtualenv`?" — `venv` is stdlib-only (Python 3.3+, simpler, slightly slower to create); `virtualenv` is a third-party tool that predates it, supports Python 2, and has more features/speed.
- "What's wrong with `pip freeze > requirements.txt`?" — it pins *all* installed packages including transitive dependencies, with no distinction between direct and indirect deps, making upgrades and audits harder; tools like `pip-tools` or lockfile-based managers address this.

**Pitfalls:**
- Installing packages globally (`sudo pip install ...`) instead of in a venv, polluting the system Python and risking breaking OS tools that depend on it.
- Committing the `.venv` directory to version control instead of `.gitignore`-ing it and using `requirements.txt`/lockfiles for reproducibility.
- Forgetting to activate the venv before `pip install`, silently installing into the wrong (global) environment.

---

### `requirements.txt`

**Explanation:** A plain-text file listing dependencies, optionally pinned to exact versions (`requests==2.31.0`), version ranges (`requests>=2.0,<3.0`), or unpinned (`requests`). Used with `pip install -r requirements.txt`.

**Why it matters:** It's the most common, lowest-overhead way to make Python environments reproducible across dev machines, CI, and production containers.

```text
# requirements.txt
requests==2.31.0
flask>=2.3,<3.0
python-dateutil
-e .   # install the current project itself in editable mode
```

```bash
pip install -r requirements.txt

# Separate dev-only dependencies
pip install -r requirements-dev.txt
```

**Common interview questions / gotchas:**
- "Pinned vs unpinned versions — tradeoffs?" — pinned gives reproducibility but risks staleness/security patches being missed; unpinned risks "works on my machine" drift.
- "How do you separate prod vs dev dependencies?" — commonly `requirements.txt` + `requirements-dev.txt`, or use `pip-tools`/Poetry's dependency groups.

**Pitfalls:**
- `requirements.txt` alone doesn't pin transitive dependencies unless generated via `pip freeze`, which can make "pinned" builds still non-deterministic depending on how it was produced.
- No built-in dependency resolution conflict detection as robust as Poetry/pip-tools — pip's resolver can still produce broken combinations in edge cases.

---

### Poetry Basics

**Explanation:** Poetry is a third-party dependency management and packaging tool that uses `pyproject.toml` for declaring dependencies and a `poetry.lock` file for fully reproducible, resolved dependency graphs (including transitive dependencies with hashes).

**Why it matters:** It combines dependency resolution, virtual environment management, and package publishing (`build`/`publish` to PyPI) into one tool, replacing the `setup.py` + `requirements.txt` + `venv` + `twine` toolchain. Many modern services (especially at companies adopting stricter reproducibility/security practices) use Poetry or similar (PDM, uv) for lockfile-based determinism.

```toml
# pyproject.toml
[tool.poetry]
name = "myapp"
version = "0.1.0"
description = "Example service"

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

```bash
poetry init                 # interactively create pyproject.toml
poetry add requests         # add a dependency, updates pyproject.toml + lock
poetry add --group dev pytest
poetry install               # install everything from poetry.lock (reproducible)
poetry run python main.py    # run inside the managed venv
poetry shell                 # activate the venv interactively
poetry lock                  # regenerate the lock file
```

**Common interview questions / gotchas:**
- "Why use a lock file at all?" — `pyproject.toml` declares version *constraints*; `poetry.lock` records the exact resolved versions (and hashes) so every install is bit-for-bit reproducible, unlike loose `requirements.txt`.
- "Poetry vs pip + venv + requirements.txt — when would you pick each?" — Poetry for libraries/services needing strict reproducibility and integrated packaging/publishing; pip+venv for simplicity or minimal tooling overhead in small scripts.
- Some interviewers ask about `pyproject.toml` as the modern PEP 517/518 standard replacing `setup.py`.

**Pitfalls:**
- Forgetting to commit `poetry.lock`, defeating the reproducibility guarantee for teammates/CI.
- Mixing `pip install` directly inside a Poetry-managed venv, causing drift between the lock file and the actual installed environment.
- Slow dependency resolution on complex dependency graphs is a known Poetry pain point in very large projects.

---

## Summary Checklist for Interviews

- Explain `sys.path` construction order and how to debug `ModuleNotFoundError`.
- Explain why modules are cached in `sys.modules` and how that creates process-wide singletons.
- Know when relative imports break (`__main__` context) and how to run modules correctly (`python -m`).
- Know `__all__` only affects `import *`, not explicit imports.
- Understand namespace packages (PEP 420) vs regular packages with `__init__.py`.
- Be able to compare `venv`+`pip`+`requirements.txt` against Poetry's lockfile-based workflow, and articulate reproducibility tradeoffs.
