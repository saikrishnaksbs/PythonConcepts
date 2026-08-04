# Concurrency & Parallelism

Python concurrency is one of the most heavily tested SDE-2 topics because it forces
you to reason about the GIL, OS scheduling, memory sharing, and I/O vs CPU bound
workloads simultaneously. This file covers the full toolbox: threads, processes,
asyncio's event loop and coroutines, futures/tasks, executor pools, and
synchronization primitives.

---

## Threads

A Python `Thread` (from the `threading` module) maps to a real OS-level thread
(pthread on Linux/macOS, Windows thread on Windows). All threads in a CPython
process share the same heap/memory space. However, CPython uses a **Global
Interpreter Lock (GIL)** — a single mutex that ensures only one thread executes
Python bytecode at a time. The OS scheduler still context-switches between
threads (CPython also forces a switch roughly every 5ms via
`sys.setswitchinterval`), but true parallel execution of Python bytecode never
happens with threads.

This means threads are excellent for **I/O-bound** work (network calls, disk
reads, `time.sleep`) because the GIL is released while waiting on I/O (the
thread makes a blocking syscall, releases the GIL, and another thread runs). For
**CPU-bound** work, threads give no speedup because of the GIL — only one thread
computes at a time.

### Why it matters for SDE-2 interviews

Every FAANG-style interview (Google, Amazon, Microsoft, Uber, Flipkart) tests
whether you understand *when threading actually helps*. A classic trap question:
"I have 4 threads doing matrix multiplication on 4 cores, why isn't it 4x
faster?" — answer: GIL. Companies like Uber/Flipkart (backend services with lots
of I/O) frequently ask you to design a thread-pool-based downloader/scraper.

### Example

```python
import threading
import time
import requests  # pip install requests; using time.sleep as stand-in below

def io_bound_task(name: str, delay: float) -> None:
    print(f"[{name}] starting I/O wait")
    time.sleep(delay)  # simulates a blocking network call; releases the GIL
    print(f"[{name}] finished after {delay}s")

def cpu_bound_task(name: str, n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    print(f"[{name}] computed sum={total}")
    return total

if __name__ == "__main__":
    # I/O-bound: threads give real speedup
    start = time.perf_counter()
    threads = [
        threading.Thread(target=io_bound_task, args=(f"t{i}", 0.5))
        for i in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"I/O-bound total time: {time.perf_counter() - start:.2f}s (parallel-ish)")

    # CPU-bound: threads do NOT give speedup due to GIL
    start = time.perf_counter()
    threads = [
        threading.Thread(target=cpu_bound_task, args=(f"c{i}", 5_000_000))
        for i in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"CPU-bound total time: {time.perf_counter() - start:.2f}s (no real speedup)")
```

### Common interview questions / gotchas

- "Why doesn't multithreading speed up CPU-bound Python code?" -> GIL.
- "How do threads communicate safely?" -> shared memory + locks/queues, not
  message passing (unlike processes).
- Daemon threads: `thread.daemon = True` means the thread is killed abruptly
  when the main program exits — don't use for tasks that need cleanup.
- `thread.join(timeout=...)` — how do you detect a thread that didn't finish?
- Difference between `threading.Thread` and `concurrent.futures.ThreadPoolExecutor`
  (the latter manages a pool + returns `Future` objects with results/exceptions).

### Pitfalls

- Forgetting to `join()` threads, causing the main thread to exit while workers
  are still running (only matters for non-daemon vs daemon semantics).
- Sharing mutable state without locks -> race conditions (see Synchronization).
- Assuming threads give CPU parallelism — a very common wrong assumption in
  interviews and in production code that silently underperforms.
- Creating unbounded threads per request instead of using a pool -> resource
  exhaustion.

---

## Processes

The `multiprocessing` module spawns **separate OS processes**, each with its own
Python interpreter and its own GIL. This means true parallelism for CPU-bound
work because each process runs on its own core independently. The cost: no
shared memory by default — data must be **pickled** and sent through IPC
(pipes, queues) or explicitly shared via `multiprocessing.shared_memory`,
`Value`, or `Array`. Process startup is also much heavier than thread startup
(fork or spawn a whole new interpreter).

On Linux, the default start method is `fork` (child inherits memory via
copy-on-write — fast). On Windows and macOS (since Python 3.8), default is
`spawn` (child starts a fresh interpreter and re-imports the module — slower,
and requires `if __name__ == "__main__":` guard to avoid infinite re-spawning).

### Why it matters for SDE-2 interviews

Google/Amazon interviewers love asking "how would you parallelize CPU-heavy
work in Python given the GIL?" — the expected answer is `multiprocessing` (or
`ProcessPoolExecutor`). You're also expected to know the cost of serialization
(pickling) when passing large objects between processes, and why processes
don't share memory the way threads do.

### Example

```python
import multiprocessing as mp
import time
import os

def cpu_bound_square_sum(n: int) -> int:
    pid = os.getpid()
    total = sum(i * i for i in range(n))
    print(f"pid={pid} computed total for n={n}")
    return total

if __name__ == "__main__":
    numbers = [8_000_000, 8_000_000, 8_000_000, 8_000_000]

    start = time.perf_counter()
    with mp.Pool(processes=4) as pool:
        results = pool.map(cpu_bound_square_sum, numbers)
    print(f"Processes results: {results}")
    print(f"Multiprocessing time: {time.perf_counter() - start:.2f}s (true parallel speedup)")

    # Sharing state across processes requires explicit IPC primitives
    shared_counter = mp.Value("i", 0)  # shared C int, synchronized with a lock

    def increment(counter, n):
        for _ in range(n):
            with counter.get_lock():
                counter.value += 1

    procs = [mp.Process(target=increment, args=(shared_counter, 100_000)) for _ in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print(f"Shared counter final value: {shared_counter.value}")  # 400000
```

### Common interview questions / gotchas

- "Why is `multiprocessing` slower for small/fast tasks?" -> process spawn +
  pickling overhead can dwarf the actual work.
- How does `fork` differ from `spawn`, and why does Windows only support
  `spawn`?
- How do you share data between processes? `Queue`, `Pipe`, `Value`, `Array`,
  `Manager`, `shared_memory.SharedMemory`.
- Why must objects passed to a process be picklable? (lambdas and local
  closures are NOT picklable — common bug.)
- `if __name__ == "__main__":` guard — why required on Windows/`spawn`.

### Pitfalls

- Passing huge objects (e.g., big DataFrames) between processes -> serialization
  cost can eliminate the benefit of parallelism.
- Using a lambda or nested function as the target -> `PicklingError`.
- Forgetting locks around shared `Value`/`Array` -> race conditions even across
  processes.
- Creating too many processes (more than CPU cores) -> context-switch overhead,
  diminishing returns; rule of thumb is `os.cpu_count()`.

---

## asyncio

`asyncio` is Python's library for **single-threaded, single-process concurrent**
code using cooperative multitasking. Instead of OS threads, asyncio runs many
coroutines on one thread, switching between them at explicit `await` points.
This is ideal for I/O-bound workloads with very high concurrency (e.g., 10,000
open sockets) because coroutines are far cheaper than OS threads (a few KB vs
~8MB stack per thread) and there's no GIL contention or context-switch cost
from the OS.

Internally, asyncio is built around: the **event loop** (schedules and runs
coroutines/callbacks), **coroutines** (functions defined with `async def`),
**Tasks** (wrap coroutines to be scheduled on the loop), and **Futures** (low
level awaitable placeholders for a result that isn't ready yet).

### Why it matters for SDE-2 interviews

Modern backend interviews (Uber, Adobe, Microsoft, Flipkart) increasingly ask
you to write an async web scraper or async API client using `aiohttp`/`asyncio`,
and to explain why asyncio scales better than threads for thousands of
concurrent connections.

### Example

```python
import asyncio
import time

async def fetch_data(name: str, delay: float) -> str:
    print(f"[{name}] request sent")
    await asyncio.sleep(delay)  # non-blocking; yields control to the event loop
    print(f"[{name}] response received")
    return f"data-from-{name}"

async def main() -> None:
    start = time.perf_counter()
    # Run 3 "network calls" concurrently on a single thread
    results = await asyncio.gather(
        fetch_data("service-A", 1.0),
        fetch_data("service-B", 1.0),
        fetch_data("service-C", 1.0),
    )
    print(f"Results: {results}")
    print(f"Elapsed: {time.perf_counter() - start:.2f}s (concurrent, ~1s not 3s)")

if __name__ == "__main__":
    asyncio.run(main())
```

### Common interview questions / gotchas

- Why is asyncio single-threaded yet still "concurrent"? -> cooperative
  scheduling at `await` points, not preemption.
- asyncio vs threading vs multiprocessing — when to use each (I/O-bound
  high-concurrency vs I/O-bound moderate-concurrency vs CPU-bound).
- What happens if you call a blocking function (e.g., `time.sleep` instead of
  `asyncio.sleep`) inside a coroutine? -> blocks the entire event loop, freezing
  all other coroutines.
- How do you run CPU-bound work inside an asyncio app without blocking the
  loop? -> `loop.run_in_executor` with a `ProcessPoolExecutor`.

### Pitfalls

- Mixing blocking calls (`requests.get`, `time.sleep`) inside `async def`
  functions — kills concurrency silently.
- Forgetting `await` on a coroutine call — creates a coroutine object that
  never runs, producing a `RuntimeWarning: coroutine was never awaited`.
- Assuming asyncio gives CPU parallelism — it does not; it's concurrency on one
  thread only.

---

## Event Loop

The event loop is the core scheduler of asyncio. It maintains a queue of ready
callbacks/tasks and repeatedly: (1) runs ready callbacks, (2) polls the OS for
I/O readiness (via `select`/`epoll`/`kqueue` depending on platform), (3) wakes
up coroutines waiting on that I/O, (4) repeats. It's a single-threaded run loop
— similar in spirit to Node.js's event loop or a GUI's message loop.

`asyncio.run()` creates a new event loop, runs the given coroutine until
complete, and then closes the loop — this is the modern, recommended entry
point (Python 3.7+). Manually calling `loop.run_until_complete()` /
`get_event_loop()` is the older, lower-level pattern still worth recognizing in
legacy code.

### Why it matters for SDE-2 interviews

Interviewers probe whether you understand that the event loop is what makes
`await` non-blocking — i.e., "what actually happens when you call `await
asyncio.sleep(1)`?" (the coroutine registers a timer callback and yields
control back to the loop, which runs other ready tasks until the timer fires).

### Example

```python
import asyncio

async def worker(n: int) -> None:
    print(f"worker {n}: before await, loop is running={asyncio.get_running_loop().is_running()}")
    await asyncio.sleep(0.2 * n)
    print(f"worker {n}: resumed")

async def main() -> None:
    loop = asyncio.get_running_loop()
    print(f"Event loop: {loop}")
    # schedule three workers; the loop interleaves them based on their sleep timers
    await asyncio.gather(worker(1), worker(2), worker(3))

    # low-level: scheduling a plain callback (not a coroutine) on the loop
    def callback(msg: str) -> None:
        print(f"callback fired: {msg}")

    loop.call_soon(callback, "scheduled via call_soon")
    await asyncio.sleep(0)  # yield once so the callback gets a chance to run

if __name__ == "__main__":
    asyncio.run(main())
```

### Common interview questions / gotchas

- What OS primitives back the event loop's I/O polling? (`epoll` on Linux,
  `kqueue` on BSD/macOS, IOCP on Windows via `ProactorEventLoop`).
- Difference between `call_soon`, `call_later`, `call_at`.
- Can you have more than one event loop per thread? -> No, one loop per thread
  at a time (asyncio is not thread-safe by default; use
  `loop.call_soon_threadsafe` to schedule from another thread).
- What happens if a coroutine raises an unhandled exception inside a Task not
  being awaited? -> logged as "Task exception was never retrieved" but doesn't
  crash the loop.

### Pitfalls

- Running long synchronous/blocking code directly in a coroutine — starves the
  event loop, so *nothing* else runs (including timers, incoming connections).
- Creating a new event loop per request in a server -> massive overhead;
  should have one loop for the process lifetime.
- Calling asyncio APIs from a non-async thread without `call_soon_threadsafe`
  -> undefined behavior / race conditions.

---

## Coroutines

A coroutine is a special function defined with `async def` that can suspend its
execution at `await` points and resume later, without blocking the underlying
thread. Calling an `async def` function does **not** run its body — it returns
a coroutine object. The body only executes when the coroutine is awaited,
wrapped in a Task, or driven manually via `.send(None)`.

Under the hood, coroutines are built on generators (PEP 492 formalized
`async`/`await` on top of the generator-based coroutine mechanism from PEP 380).
Each `await` is conceptually like a `yield` that suspends and later resumes
with a value or exception.

### Why it matters for SDE-2 interviews

Common trick question: "What does this print?" for code that calls an async
function without awaiting it. You're expected to know a coroutine is inert
until awaited/scheduled — a subtle but very testable distinction.

### Example

```python
import asyncio

async def compute_square(n: int) -> int:
    await asyncio.sleep(0.1)  # simulate suspension
    return n * n

async def main() -> None:
    coro = compute_square(5)
    print(f"type(coro) = {type(coro)}")  # <class 'coroutine'>, not yet executed

    result = await coro  # NOW it actually runs
    print(f"result = {result}")

    # Chaining coroutines
    async def pipeline(n: int) -> int:
        squared = await compute_square(n)
        doubled = squared * 2
        return doubled

    print(f"pipeline(4) = {await pipeline(4)}")

    # Manually driving a coroutine step by step (educational, rarely done in practice)
    manual = compute_square(3)
    try:
        manual.send(None)  # advances to the first await; raises StopIteration on completion normally
    except StopIteration as e:
        print(f"manual coroutine result via StopIteration: {e.value}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Common interview questions / gotchas

- "Is `foo()` where `foo` is `async def` executed immediately?" -> No, it just
  creates a coroutine object.
- How are coroutines related to generators internally?
- Can a coroutine be awaited twice? -> No, raises `RuntimeError: cannot reuse
  already awaited coroutine`.
- Difference between a coroutine object and a Task (Task = coroutine + being
  actively scheduled by the loop).

### Pitfalls

- Calling an async function and forgetting `await` — the classic "why did
  nothing happen" bug (produces a `RuntimeWarning`, not an error, so it's easy
  to miss).
- Trying to await the same coroutine object a second time.
- Blocking inside a coroutine with CPU-heavy synchronous code, defeating the
  purpose of cooperative multitasking.

---

## await

`await` suspends execution of the current coroutine until the awaited object
(coroutine, Task, or Future) completes, yielding control back to the event
loop so other work can run in the meantime. `await` can only be used inside an
`async def` function (or at the top level of an interactive REPL / `asyncio`
in newer Python versions in some contexts). The awaited object must implement
`__await__`.

### Why it matters for SDE-2 interviews

You're expected to explain the *mechanics*: `await` doesn't block the thread;
it registers a continuation and returns control to the loop's scheduler.
Interviewers use this to distinguish candidates who memorized syntax from
those who understand cooperative scheduling.

### Example

```python
import asyncio
import time

async def slow_task(name: str, delay: float) -> str:
    start = time.perf_counter()
    await asyncio.sleep(delay)
    elapsed = time.perf_counter() - start
    return f"{name} done in {elapsed:.2f}s"

async def sequential_vs_concurrent() -> None:
    # Sequential await: total time = sum of delays
    start = time.perf_counter()
    r1 = await slow_task("seq-A", 0.5)
    r2 = await slow_task("seq-B", 0.5)
    print(r1, r2, f"(sequential total={time.perf_counter()-start:.2f}s)")

    # Concurrent await via gather: total time = max of delays
    start = time.perf_counter()
    r3, r4 = await asyncio.gather(slow_task("conc-A", 0.5), slow_task("conc-B", 0.5))
    print(r3, r4, f"(concurrent total={time.perf_counter()-start:.2f}s)")

if __name__ == "__main__":
    asyncio.run(sequential_vs_concurrent())
```

### Common interview questions / gotchas

- Why does awaiting two coroutines back-to-back (`await a(); await b()`) NOT
  run them concurrently, while `asyncio.gather(a(), b())` does?
- What can you `await`? -> anything implementing `__await__`: coroutines,
  Tasks, Futures (not arbitrary objects, and not plain generators unless
  decorated appropriately).
- Can `await` raise exceptions? -> Yes, exceptions propagate from the awaited
  coroutine like a normal function call/raise.

### Pitfalls

- Sequential awaiting when concurrency was intended — very common performance
  bug in production async code.
- Using `await` outside an `async def` -> `SyntaxError`.
- Forgetting that an exception inside a gathered coroutine (without
  `return_exceptions=True`) cancels sibling tasks and propagates immediately.

---

## async

The `async` keyword marks a function definition (`async def`) as a coroutine
function, and is also used for `async with` (asynchronous context managers)
and `async for` (asynchronous iteration). `async def` functions return
coroutine objects when called rather than executing immediately; `async with`
calls `__aenter__`/`__aexit__`; `async for` calls `__anext__` repeatedly on an
async iterator.

### Why it matters for SDE-2 interviews

You should be comfortable writing an async context manager and an async
generator/iterator from scratch — common in interviews at Adobe/Microsoft that
test library-design skills (e.g., "design an async connection pool context
manager").

### Example

```python
import asyncio

class AsyncResource:
    async def __aenter__(self):
        print("acquiring resource (async)")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        print("releasing resource (async)")
        await asyncio.sleep(0.1)
        return False  # don't suppress exceptions

class AsyncCounter:
    def __init__(self, limit: int):
        self.limit = limit
        self.current = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current >= self.limit:
            raise StopAsyncIteration
        await asyncio.sleep(0.05)
        self.current += 1
        return self.current

async def main() -> None:
    async with AsyncResource() as res:
        print(f"using resource: {res}")

    async for value in AsyncCounter(3):
        print(f"async for got: {value}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Common interview questions / gotchas

- Difference between `__aenter__`/`__aexit__` and regular `__enter__`/`__exit__`.
- How would you write an async generator (`async def` with `yield` inside)
  versus a class-based async iterator?
- Can you mix `async for` with a regular (sync) iterable? -> No, the iterable
  must implement `__aiter__`.

### Pitfalls

- Forgetting `async` on `__aenter__`/`__aexit__` when implementing an async
  context manager — a very easy typo that produces confusing errors.
- Using `async def` purely out of habit on functions that do no awaiting —
  unnecessary overhead and misleading API signature.

---

## Future

A `Future` (from `asyncio` or `concurrent.futures`) is a low-level awaitable
object representing a computation that may not have completed yet. It has
states: pending, running, done (with either a result or an exception), or
cancelled. Higher-level constructs (`Task`, `ThreadPoolExecutor.submit`) return
Futures. You rarely create `asyncio.Future` directly in application code — it's
the plumbing that Tasks and executors are built on. Note: `asyncio.Future` and
`concurrent.futures.Future` are different classes with similar APIs but
different threading semantics (the latter is thread-safe and used by
executors; the former is tied to a single event loop).

### Why it matters for SDE-2 interviews

Interviewers check if you understand that a `Task` *is a* `Future` subtype (in
asyncio) and that `ThreadPoolExecutor.submit()`/`ProcessPoolExecutor.submit()`
return `concurrent.futures.Future` objects you can `.result()`, `.done()`, or
attach callbacks to via `.add_done_callback()`.

### Example

```python
import asyncio
import concurrent.futures
import time

def blocking_computation(x: int) -> int:
    time.sleep(0.3)
    return x * x

def demo_concurrent_futures() -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future: concurrent.futures.Future = executor.submit(blocking_computation, 7)
        print(f"future.done() immediately after submit: {future.done()}")

        def on_done(f: concurrent.futures.Future) -> None:
            print(f"callback: computation finished with result={f.result()}")

        future.add_done_callback(on_done)
        result = future.result()  # blocks until ready
        print(f"main thread got result: {result}")

async def demo_asyncio_future() -> None:
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()

    def resolve_later():
        fut.set_result("resolved from a callback")

    loop.call_later(0.2, resolve_later)
    result = await fut  # suspends until fut.set_result() is called
    print(f"asyncio.Future result: {result}")

if __name__ == "__main__":
    demo_concurrent_futures()
    asyncio.run(demo_asyncio_future())
```

### Common interview questions / gotchas

- What states can a Future be in, and what methods query/transition them?
  (`set_result`, `set_exception`, `cancel`, `done`, `result`, `exception`.)
- Why is `concurrent.futures.Future.result()` blocking while awaiting an
  `asyncio.Future` is not?
- Relationship between `Task` and `Future` -> `Task` is a subclass of `Future`
  that wraps and drives a coroutine.

### Pitfalls

- Calling `.result()` on a `concurrent.futures.Future` from the main/event-loop
  thread without a timeout -> can hang indefinitely.
- Mixing `asyncio.Future` and `concurrent.futures.Future` incorrectly (e.g.,
  awaiting a `concurrent.futures.Future` directly — not awaitable; use
  `asyncio.wrap_future()` to bridge them).
- Forgetting that an exception raised inside the submitted callable is stored
  on the Future and only re-raised when `.result()` is called, not at submit
  time.

---

## Task

A `Task` is asyncio's mechanism for actually **scheduling** a coroutine to run
concurrently on the event loop. `asyncio.create_task(coro())` wraps a coroutine
and schedules it immediately (returns control to the caller right away while
the task runs in the background). `asyncio.gather(*coros)` internally creates
Tasks for each coroutine passed. A Task is a subclass of `Future`; when the
coroutine finishes, the Task's Future is resolved with the result or
exception.

### Why it matters for SDE-2 interviews

A very common live-coding exercise: "fire off N async requests, run them
concurrently, collect results, and handle partial failures." You need to know
`create_task` vs `gather` vs `asyncio.wait`/`TaskGroup` (3.11+) tradeoffs.

### Example

```python
import asyncio

async def fetch(id_: int, fail: bool = False) -> str:
    await asyncio.sleep(0.2)
    if fail:
        raise ValueError(f"fetch {id_} failed")
    return f"result-{id_}"

async def main() -> None:
    # create_task: fire-and-run-in-background, scheduled immediately
    task1 = asyncio.create_task(fetch(1))
    task2 = asyncio.create_task(fetch(2))
    print(f"tasks created: {task1.get_name()}, {task2.get_name()} (already running)")
    print(await task1, await task2)

    # gather with error handling
    results = await asyncio.gather(
        fetch(3), fetch(4, fail=True), return_exceptions=True
    )
    for r in results:
        if isinstance(r, Exception):
            print(f"gathered exception: {r}")
        else:
            print(f"gathered result: {r}")

    # Python 3.11+ structured concurrency: TaskGroup
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fetch(5))
            tg.create_task(fetch(6))
    except* ValueError as eg:
        print(f"TaskGroup caught exception group: {eg.exceptions}")

    # Cancellation
    long_task = asyncio.create_task(asyncio.sleep(5))
    await asyncio.sleep(0.1)
    long_task.cancel()
    try:
        await long_task
    except asyncio.CancelledError:
        print("long_task was cancelled as expected")

if __name__ == "__main__":
    asyncio.run(main())
```

### Common interview questions / gotchas

- `create_task` vs directly `await`ing a coroutine -> `create_task` schedules
  it to start running now (concurrently), `await` on a plain coroutine runs it
  inline, blocking further progress until it's done.
- What happens if you never `await`/keep a reference to a Task? -> It may be
  garbage collected mid-execution (asyncio even warns about this); best
  practice is to keep a reference (e.g., in a set) until done.
- How does cancellation propagate? `task.cancel()` raises `CancelledError`
  inside the coroutine at its next suspension point.
- `asyncio.gather` vs `asyncio.wait` vs `TaskGroup` (3.11+) — which cancels
  siblings on failure, which doesn't.

### Pitfalls

- Not keeping a strong reference to a "fire and forget" task -> silent garbage
  collection cancels it (classic asyncio gotcha, called out in the docs).
- Swallowing `CancelledError` accidentally with a bare `except Exception:` —
  breaks cooperative cancellation.
- Assuming `gather()` without `return_exceptions=True` will run all coroutines
  to completion even if one fails — actually it propagates the first exception
  once raised (others continue running in the background but you don't get
  their results at that call site).

---

## ThreadPoolExecutor

`concurrent.futures.ThreadPoolExecutor` manages a fixed-size pool of worker
threads that pull callables off an internal queue and execute them, returning
`Future` objects immediately. It's the standard high-level API for
thread-based concurrency (preferred over manually managing `threading.Thread`
objects for most production code) because it handles pool sizing, queuing, and
cleanup (`shutdown`) for you.

### Why it matters for SDE-2 interviews

Extremely common in system design + coding rounds: "parallelize N independent
I/O calls with bounded concurrency." Expected answer: `ThreadPoolExecutor` with
`max_workers`, using `.map()` or `.submit()` + `as_completed()`.

### Example

```python
import concurrent.futures
import time

def download(url: str) -> str:
    time.sleep(0.3)  # simulate network I/O
    return f"downloaded: {url}"

def main() -> None:
    urls = [f"https://example.com/page/{i}" for i in range(6)]

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Approach 1: map preserves input order
        for result in executor.map(download, urls):
            print(result)

    print(f"map() elapsed: {time.perf_counter() - start:.2f}s")

    # Approach 2: submit + as_completed for results as they finish
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(download, u): u for u in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                print(f"{url} -> {future.result()}")
            except Exception as exc:
                print(f"{url} raised {exc}")

    print(f"submit/as_completed elapsed: {time.perf_counter() - start:.2f}s")

if __name__ == "__main__":
    main()
```

### Common interview questions / gotchas

- How does `ThreadPoolExecutor` choose a default `max_workers`? -> since 3.8,
  `min(32, os.cpu_count() + 4)`.
- `executor.map()` vs `submit()` + `as_completed()` — ordering guarantees
  (`map` preserves order; `as_completed` yields in completion order).
- Does `ThreadPoolExecutor` help CPU-bound work? -> No (GIL) — use
  `ProcessPoolExecutor` instead.
- What happens to exceptions raised inside worker functions? -> stored on the
  Future, re-raised when you call `.result()`.

### Pitfalls

- Using `ThreadPoolExecutor` for CPU-bound tasks and being surprised there's no
  speedup.
- Not using the pool as a context manager (`with ... as executor:`) -> forgetting
  to call `shutdown(wait=True)`, leaking threads.
- Setting `max_workers` too high for I/O-bound tasks hitting a rate-limited
  external API -> thundering herd / getting throttled.

---

## ProcessPoolExecutor

`concurrent.futures.ProcessPoolExecutor` is the process-based sibling of
`ThreadPoolExecutor`, sharing the same `submit`/`map`/`as_completed` API but
running each task in a separate worker process (via `multiprocessing`
underneath). This achieves true CPU parallelism at the cost of IPC/pickling
overhead for arguments and return values. Because the interface mirrors
`ThreadPoolExecutor`, swapping between them is often a one-line change — which
is exactly why interviewers like asking you to justify the choice.

### Why it matters for SDE-2 interviews

Companies like Google/Amazon frequently pose: "You have a CPU-heavy function
(e.g., image resizing, hashing) applied to 10,000 items — parallelize it."
Expected: `ProcessPoolExecutor` sized to `os.cpu_count()`, with attention to
picklability of arguments/results.

### Example

```python
import concurrent.futures
import os
import time

def cpu_heavy(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * i
    return total

def main() -> None:
    work_items = [3_000_000] * 8
    cpu_count = os.cpu_count() or 4
    print(f"CPU count: {cpu_count}")

    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
        results = list(executor.map(cpu_heavy, work_items))
    print(f"ProcessPoolExecutor elapsed: {time.perf_counter() - start:.2f}s, "
          f"sample result: {results[0]}")

    # Comparing against sequential execution for contrast
    start = time.perf_counter()
    sequential_results = [cpu_heavy(n) for n in work_items]
    print(f"Sequential elapsed: {time.perf_counter() - start:.2f}s")

if __name__ == "__main__":
    main()
```

### Common interview questions / gotchas

- Why can't you pass a lambda or an instance method bound to an unpicklable
  object to `ProcessPoolExecutor.submit()`?
- What's the overhead source when using `ProcessPoolExecutor` for very small
  tasks? -> process/IPC overhead can exceed the task's own runtime.
- How would you share large read-only data across worker processes efficiently
  without repeated pickling? -> `multiprocessing.shared_memory`, or rely on
  `fork`'s copy-on-write inheritance (Linux only), or initialize once per
  worker via `initializer=`.
- How do exceptions in worker processes surface to the caller? -> pickled back
  and re-raised on `.result()`, same interface as ThreadPoolExecutor.

### Pitfalls

- Using `ProcessPoolExecutor` for I/O-bound tasks -> wasteful; threads/asyncio
  are cheaper and just as effective there.
- Forgetting the `if __name__ == "__main__":` guard on Windows/macOS `spawn`
  -> infinite process spawning or `RuntimeError`.
- Passing very large arguments/results repeatedly -> serialization cost
  dominates; prefer `initializer`/shared memory for big read-only data.

---

## Synchronization

Synchronization primitives coordinate access to shared, mutable state across
concurrent threads (and, with different tools, across processes) to prevent
race conditions — situations where the outcome depends on unpredictable
timing/interleaving of operations. Python's `threading` module provides
`Lock`, `RLock`, `Semaphore`, `BoundedSemaphore`, `Event`, `Condition`, and
`Barrier`. Even though the GIL prevents two threads from executing Python
bytecode *simultaneously*, a "single" operation like `x += 1` is not atomic at
the bytecode level (it's load, add, store — the GIL can switch threads between
those steps), so races are still very real without proper locking.

### Why it matters for SDE-2 interviews

"Given the GIL, do you still need locks in Python?" is one of the single most
common trick questions across Google/Amazon/Microsoft interviews. The correct
answer is **yes** — compound operations are not atomic, and the GIL only
guarantees atomicity of individual bytecode instructions, not of
higher-level statements.

### Example

```python
import threading
import time

counter = 0

def increment_unsafe(n: int) -> None:
    global counter
    for _ in range(n):
        counter += 1  # NOT atomic: read, add, write -> race condition

def demo_race_condition() -> None:
    global counter
    counter = 0
    threads = [threading.Thread(target=increment_unsafe, args=(100_000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Expected 400000, got {counter} (likely wrong due to race condition)")

lock = threading.Lock()
safe_counter = 0

def increment_safe(n: int) -> None:
    global safe_counter
    for _ in range(n):
        with lock:  # ensures atomicity of the read-modify-write
            safe_counter += 1

def demo_safe_increment() -> None:
    global safe_counter
    safe_counter = 0
    threads = [threading.Thread(target=increment_safe, args=(100_000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Expected 400000, got {safe_counter} (always correct with lock)")

if __name__ == "__main__":
    demo_race_condition()
    demo_safe_increment()
```

### Common interview questions / gotchas

- "The GIL means Python is thread-safe, right?" -> False; the GIL protects
  interpreter internals, not your application's compound operations.
- Which built-in operations ARE atomic under the GIL? -> single bytecode ops
  like `list.append`, dict item assignment — but multi-step statements (`x +=
  1`, "check-then-act" patterns) are not.
- How do you avoid deadlocks when using multiple locks? -> consistent lock
  ordering, timeouts, or higher-level primitives.

### Pitfalls

- Assuming the GIL makes all Python code inherently thread-safe.
- Holding a lock across a blocking I/O call, causing other threads to stall
  needlessly (hold locks for the shortest critical section possible).
- Not releasing locks on exception paths — always use `with lock:` instead of
  manual `acquire()`/`release()`.

---

## Locks

`threading.Lock` is the most basic mutual-exclusion primitive: a binary
semaphore that is either "locked" or "unlocked." `acquire()` blocks until the
lock is free (or a timeout expires); `release()` frees it. A **non-reentrant**
Lock will deadlock if the same thread calls `acquire()` twice without an
intervening `release()` — that's what `RLock` solves (see next section).
Python's `with lock:` context manager syntax is the idiomatic way to use locks
because it guarantees release even if an exception is raised.

### Why it matters for SDE-2 interviews

Locks are the foundation for every higher-level synchronization discussion.
Interviewers expect fluent, correct usage (`with lock:`) and awareness of
deadlock scenarios (e.g., two threads acquiring two locks in opposite order).

### Example

```python
import threading
import time

account_balance = 1000
balance_lock = threading.Lock()

def withdraw(amount: int) -> None:
    global account_balance
    with balance_lock:
        if account_balance >= amount:
            time.sleep(0.01)  # simulate processing time inside critical section
            account_balance -= amount
            print(f"Withdrew {amount}, balance now {account_balance}")
        else:
            print(f"Insufficient funds for {amount}")

def demo_lock() -> None:
    threads = [threading.Thread(target=withdraw, args=(200,)) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Final balance: {account_balance}")

def demo_deadlock_avoidance() -> None:
    lock_a = threading.Lock()
    lock_b = threading.Lock()

    def worker(first: threading.Lock, second: threading.Lock, name: str) -> None:
        with first:
            time.sleep(0.05)
            with second:
                print(f"{name} acquired both locks safely")

    # Both threads acquire in the SAME order (a then b) to avoid deadlock
    t1 = threading.Thread(target=worker, args=(lock_a, lock_b, "worker-1"))
    t2 = threading.Thread(target=worker, args=(lock_a, lock_b, "worker-2"))
    t1.start(); t2.start()
    t1.join(); t2.join()

if __name__ == "__main__":
    demo_lock()
    demo_deadlock_avoidance()
```

### Common interview questions / gotchas

- What happens if a thread calls `lock.acquire()` twice without releasing? ->
  deadlock (with a plain `Lock`).
- How do you implement a timeout on lock acquisition? ->
  `lock.acquire(timeout=2)` returns `False` if it couldn't acquire in time.
- Classic deadlock scenario: two threads each hold one lock and wait for the
  other's lock -> explain and show the fix (consistent ordering, or
  `try`-based backoff).

### Pitfalls

- Manually calling `acquire()`/`release()` without `try/finally` -> exceptions
  leave the lock held forever.
- Inconsistent lock acquisition order across different code paths -> classic
  deadlock source.
- Overly coarse-grained locks (locking too much code) -> kills concurrency,
  effectively serializing everything.

---

## RLock

`threading.RLock` ("reentrant lock") can be acquired multiple times by the
**same thread** without deadlocking — internally it tracks an owner thread ID
and a recursion counter. Each `acquire()` by the owning thread increments the
counter; each `release()` decrements it; the lock is only truly released when
the counter returns to zero. Other threads attempting to acquire it still
block until the owning thread fully releases it. This is essential for
recursive functions or methods that call other locking methods on `self`.

### Why it matters for SDE-2 interviews

Interviewers ask you to identify why a plain `Lock` deadlocks in a recursive
method call chain, and to fix it using `RLock` — testing whether you
understand reentrancy vs mutual exclusion as separate concepts.

### Example

```python
import threading

class SafeCounter:
    def __init__(self):
        self._lock = threading.RLock()
        self._value = 0

    def increment(self):
        with self._lock:
            self._value += 1
            self._log_state()  # calls another method that also acquires the SAME lock

    def _log_state(self):
        with self._lock:  # re-entrant: same thread can acquire again without deadlock
            print(f"current value: {self._value}")

def demo_rlock() -> None:
    counter = SafeCounter()
    threads = [threading.Thread(target=counter.increment) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Final value: {counter._value}")

def demo_plain_lock_would_deadlock() -> None:
    # Illustrative only — NOT executed with .acquire() twice on a plain Lock,
    # since that would hang the script. Shown as commented pseudocode-in-code:
    lock = threading.Lock()
    print("A plain Lock acquired twice by the same thread would deadlock:")
    print("  lock.acquire(); lock.acquire()  # <- hangs forever, second call blocks")
    print("RLock avoids this by tracking the owning thread + a recursion count.")

if __name__ == "__main__":
    demo_rlock()
    demo_plain_lock_would_deadlock()
```

### Common interview questions / gotchas

- Difference between `Lock` and `RLock` -> reentrancy: same thread can
  re-acquire an `RLock`; a plain `Lock` would deadlock.
- Does an `RLock` protect against a DIFFERENT thread acquiring it while owned?
  -> Yes, mutual exclusion across threads is preserved; only same-thread
  re-entry is permitted.
- Must `release()` be called the same number of times as `acquire()` for
  `RLock`? -> Yes, exactly matched, otherwise the lock/counter gets out of
  sync.

### Pitfalls

- Using a plain `Lock` in a class with methods that call each other
  recursively/internally while both hold the lock -> deadlock.
- Mismatched acquire/release counts on `RLock` (e.g., forgetting a
  `with` block somewhere) -> lock never fully releases.
- Assuming `RLock` is a performance-free upgrade over `Lock` — it has slightly
  more overhead due to owner/counter bookkeeping; use it only when reentrancy
  is actually needed.

---

## Semaphore

`threading.Semaphore(value)` maintains an internal counter; `acquire()`
decrements it (blocking if it would go below zero), `release()` increments it.
Unlike a `Lock` (binary: 0 or 1), a Semaphore allows up to `value` concurrent
holders — perfect for **rate limiting** or **bounding concurrency** (e.g.,
"only 5 threads may hit this API at once"). `BoundedSemaphore` is a stricter
variant that raises `ValueError` if `release()` is called more times than
`acquire()` (catches bugs where you accidentally over-release).

### Why it matters for SDE-2 interviews

Extremely common system-design-adjacent coding question: "limit concurrent
DB connections / API calls to N." Semaphore is the textbook answer, and
`asyncio.Semaphore` is the async equivalent for coroutine-based concurrency
limiting.

### Example

```python
import threading
import time
import random

# Simulate a resource pool that only allows 3 concurrent users
pool_semaphore = threading.Semaphore(3)

def access_limited_resource(worker_id: int) -> None:
    print(f"worker {worker_id} waiting for slot...")
    with pool_semaphore:
        print(f"worker {worker_id} ACQUIRED slot at {time.strftime('%X')}")
        time.sleep(random.uniform(0.3, 0.6))
        print(f"worker {worker_id} releasing slot")

def demo_semaphore() -> None:
    threads = [threading.Thread(target=access_limited_resource, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

import asyncio

async def async_worker(id_: int, sem: asyncio.Semaphore) -> None:
    async with sem:
        print(f"async worker {id_} running (bounded concurrency)")
        await asyncio.sleep(0.2)

async def demo_asyncio_semaphore() -> None:
    sem = asyncio.Semaphore(2)  # at most 2 concurrent coroutines
    await asyncio.gather(*(async_worker(i, sem) for i in range(6)))

if __name__ == "__main__":
    demo_semaphore()
    asyncio.run(demo_asyncio_semaphore())
```

### Common interview questions / gotchas

- Semaphore vs Lock -> Lock is a semaphore with `value=1`; Semaphore generalizes
  to N concurrent holders.
- What's the difference between `Semaphore` and `BoundedSemaphore`? ->
  `BoundedSemaphore` raises an error on an extra/erroneous `release()`, catching
  bugs early.
- How would you implement a connection pool limiter using a Semaphore?
- asyncio's `Semaphore` vs threading's `Semaphore` — same concept, different
  scheduling domain (coroutines vs OS threads).

### Pitfalls

- Forgetting to release a semaphore permit on an exception path -> use `with
  sem:` always, never manual acquire/release without try/finally.
- Off-by-one errors in the initial `value` -> allowing more/fewer concurrent
  accesses than intended.
- Using a plain `Semaphore` when you actually want `BoundedSemaphore` to catch
  release-without-acquire bugs during development.

---

## Queue

`queue.Queue` is a thread-safe FIFO queue used for the classic
**producer-consumer** pattern — internally protected by a `Lock`/`Condition`
so multiple threads can safely `put()`/`get()` without external
synchronization. Variants include `LifoQueue` (stack behavior) and
`PriorityQueue` (heap-ordered). For asyncio, `asyncio.Queue` provides the same
API but is coroutine-safe (single-threaded, used with `await queue.get()`/`await
queue.put()`) rather than thread-safe. For multiprocessing,
`multiprocessing.Queue` serializes (pickles) items to move them across process
boundaries.

### Why it matters for SDE-2 interviews

Producer-consumer with a bounded queue is one of the most frequently asked
concurrency coding exercises across Amazon/Microsoft/Walmart/Flipkart —
testing whether you can coordinate multiple producers/consumers, signal
completion (sentinel values or `task_done`/`join`), and avoid busy-waiting.

### Example

```python
import threading
import queue
import time
import random

def producer(q: "queue.Queue[int]", count: int, producer_id: int) -> None:
    for i in range(count):
        item = producer_id * 100 + i
        q.put(item)
        print(f"producer-{producer_id} produced {item}")
        time.sleep(random.uniform(0.01, 0.05))

def consumer(q: "queue.Queue[int]", consumer_id: int) -> None:
    while True:
        item = q.get()
        if item is None:  # sentinel value signals shutdown
            q.task_done()
            break
        print(f"consumer-{consumer_id} consumed {item}")
        time.sleep(random.uniform(0.01, 0.05))
        q.task_done()

def demo_thread_queue() -> None:
    q: "queue.Queue[int]" = queue.Queue(maxsize=5)  # bounded queue applies backpressure
    producers = [threading.Thread(target=producer, args=(q, 5, i)) for i in range(2)]
    consumers = [threading.Thread(target=consumer, args=(q, i)) for i in range(3)]

    for c in consumers:
        c.start()
    for p in producers:
        p.start()
    for p in producers:
        p.join()

    q.join()  # block until all items have been processed (task_done called for each)

    # send sentinels to stop consumers cleanly
    for _ in consumers:
        q.put(None)
    for c in consumers:
        c.join()
    print("all producers/consumers finished cleanly")

import asyncio

async def async_producer(q: "asyncio.Queue[int]") -> None:
    for i in range(5):
        await q.put(i)
        await asyncio.sleep(0.05)
    await q.put(None)  # sentinel

async def async_consumer(q: "asyncio.Queue[int]") -> None:
    while True:
        item = await q.get()
        if item is None:
            break
        print(f"async consumer got {item}")

async def demo_asyncio_queue() -> None:
    q: "asyncio.Queue[int]" = asyncio.Queue(maxsize=3)
    await asyncio.gather(async_producer(q), async_consumer(q))

if __name__ == "__main__":
    demo_thread_queue()
    asyncio.run(demo_asyncio_queue())
```

### Common interview questions / gotchas

- How does `Queue.join()` combined with `task_done()` let you know all work is
  finished without a fixed sentinel-counting scheme?
- Why is a bounded queue (`maxsize=N`) useful? -> applies backpressure,
  preventing a fast producer from exhausting memory.
- How would you cleanly shut down N consumer threads reading from a shared
  queue? -> sentinel values (one per consumer) or a separate stop `Event`.
- `queue.Queue` (thread-safe) vs `asyncio.Queue` (coroutine-safe, not
  thread-safe) vs `multiprocessing.Queue` (process-safe, pickles data) — know
  when each applies.
- `PriorityQueue` internals -> wraps `heapq`, items are typically `(priority,
  data)` tuples; unstable ordering on ties unless you add a tiebreaker.

### Pitfalls

- Using `asyncio.Queue` across real OS threads — it is NOT thread-safe, unlike
  `queue.Queue`.
- Forgetting `task_done()` calls, causing `q.join()` to hang forever.
- Using an unbounded queue with a much faster producer than consumer -> memory
  growth/OOM in production.
- Using `PriorityQueue` with plain unorderable objects as the second tuple
  element when priorities tie -> `TypeError` on comparison; add an explicit
  tiebreaker (e.g., an incrementing counter).

---

## Quick Comparison Cheat Sheet

| Tool | Parallelism model | Best for | Shares memory? |
|---|---|---|---|
| `threading.Thread` | OS threads, GIL-limited | I/O-bound, moderate concurrency | Yes |
| `multiprocessing` | OS processes, real parallel | CPU-bound | No (IPC/pickling) |
| `asyncio` | Single-thread cooperative | I/O-bound, very high concurrency | Yes (single thread) |
| `ThreadPoolExecutor` | Thread pool | I/O-bound, bounded thread count | Yes |
| `ProcessPoolExecutor` | Process pool | CPU-bound, bounded process count | No (IPC/pickling) |

This table itself is a favorite whiteboard-summary ask at the end of a
concurrency interview round — being able to reproduce it, with the "why,"
signals real understanding rather than memorized syntax.
