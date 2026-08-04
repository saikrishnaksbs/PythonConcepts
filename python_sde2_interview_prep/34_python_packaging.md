# Python Packaging

Python packaging has evolved significantly. From raw scripts and manual installation, it moved to structured packages, and now to modern dependency managers and declarative build files. For SDE-2 interviews, you should understand how dependencies are managed, the role of virtual environments, and the difference between legacy and modern build configuration standards.

## Table of Contents

- [Virtual Environments](#virtual-environments)
- [Requirements Files vs Modern Pyproject.toml](#requirements-files-vs-modern-pyprojecttoml)
- [Legacy vs Modern Build tools (`setup.py` vs `pyproject.toml`)](#legacy-vs-modern-build-tools-setuppy-vs-pyprojecttoml)
- [Distribution Formats (Source Distribution vs Wheel)](#distribution-formats-source-distribution-vs-wheel)
- [Dependency Managers (pip, Poetry)](#dependency-managers-pip-poetry)

---

## Virtual Environments

### Explanation

Python installations are global by default. If you install dependencies globally, different projects requiring different versions of the same package will conflict.

A **Virtual Environment** isolates the Python interpreter and site-packages directory for a specific project.
- Created via the built-in module: `python -m venv .venv`.
- Activated via `source .venv/bin/activate` (on Unix) or `.venv\Scripts\activate` (on Windows).
- Activation modifies your shell environment, prefixing your `$PATH` so the shell looks for python binaries inside the virtual environment directory first.

---

## Requirements Files vs Modern Pyproject.toml

### Explanation

- **`requirements.txt`**: A list of package dependencies, often output using `pip freeze > requirements.txt`. It contains flat, exact dependencies but lacks distinction between production dependencies, development tools, and transitive dependencies.
- **`pyproject.toml`**: The modern standard (defined in PEP 518 and PEP 621). A declarative configuration file containing build system specifications, package metadata, dependencies, and configuration for formatting/linting tools (like `ruff`, `black`, `mypy`).

---

## Legacy vs Modern Build tools (`setup.py` vs `pyproject.toml`)

### Explanation

- **Legacy (`setup.py`)**: An executable Python script using `setuptools` to package and build projects. Executing it (e.g., `python setup.py install`) runs arbitrary Python code, causing security, bootstrapping, and performance issues.
- **Modern (`pyproject.toml` + build backend)**: Completely declarative. It specifies which build backend to use (e.g., `setuptools`, `poetry-core`, `hatchling`, `flit`).

---

## Distribution Formats (Source Distribution vs Wheel)

### Explanation

When you download a package from PyPI, it comes in one of two formats:
1. **Source Distribution (sdist, `.tar.gz`)**: Contains the raw source code. If the package contains C extensions, the user's machine must compile them during installation, requiring compilation tools (gcc, make) and headers to be installed locally.
2. **Wheel (built distribution, `.whl`)**: A pre-compiled zip archive. It is ready to install instantly (just unzipped into `site-packages`). C extensions are already compiled for specific architectures (e.g., manylinux, macos-arm64). Always prefer wheels for fast, reliable deployments.

---

## Dependency Managers (pip, Poetry)

### Explanation

- **`pip`**: The default package installer. It downloads and installs dependencies but historically struggled with complex dependency resolution and did not maintain lockfiles.
- **`Poetry`**: A modern dependency manager. It automatically resolves dependency graphs, manages virtual environments, and writes a lockfile (`poetry.lock`). Lockfiles pin the exact versions of all dependencies (and their transitive dependencies), guaranteeing identical environments across local development and production.

---

## Minimal `pyproject.toml` Example

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "myapp"
version = "0.1.0"
dependencies = [
    "requests>=2.31",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest", "black", "mypy"]
```

## `pip` Essentials

```bash
pip install requests==2.31.0     # exact version
pip install -e .                 # editable/development install of current project
pip freeze > requirements.txt    # snapshot exact installed versions
pip install -r requirements.txt  # install from lockfile-like requirements
```

## Common Interview Questions

1. **"Why does a `requirements.txt` sometimes break builds later even though nothing changed?"** Unpinned or loosely pinned transitive dependencies (`requests` pulling in whatever latest `urllib3` at install time) can silently upgrade — a proper lockfile (Poetry, pip-tools) pins the full transitive graph.
2. **"What's the difference between a wheel and an sdist practically?"** Installing a wheel is a simple unzip (fast, no compiler needed); installing an sdist with C extensions requires a working build toolchain on the target machine, which is slower and can fail in minimal container images.
3. **Pitfall:** Forgetting to activate/use a virtual environment leads to installing packages globally, causing "works on my machine" version conflicts between unrelated projects.
4. **Pitfall:** `python setup.py install` executes arbitrary code from the package at install time — modern tooling (`pip install`, PEP 517 build backends) isolates this in a build environment, but legacy `setup.py`-based installs still carry that risk.
