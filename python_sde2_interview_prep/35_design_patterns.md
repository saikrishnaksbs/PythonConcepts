# Design Patterns in Python

Design patterns are reusable solutions to common software design problems. Because Python is highly dynamic, many classic design patterns (e.g., from the Gang of Four) are simpler to implement in Python or can be bypassed entirely. For SDE-2 interviews, you should know the Pythonic implementations of key Creational, Structural, and Behavioral patterns.

## Table of Contents

- [Creational Patterns (Singleton, Factory, Builder)](#creational-patterns-singleton-factory-builder)
- [Structural Patterns (Adapter, Decorator, Proxy)](#structural-patterns-adapter-decorator-proxy)
- [Behavioral Patterns (Strategy, Observer, Command)](#behavioral-patterns-strategy-observer-command)
- [Architectural Patterns (Repository, Dependency Injection)](#architectural-patterns-repository-dependency-injection)

---

## Creational Patterns (Singleton, Factory, Builder)

### 1. Singleton

Ensures a class has only one instance and provides a global point of access.

#### Pythonic Implementations

1. **Metaclass**: The cleanest way, as it intercepts instantiation.
2. **Module Import**: Python modules are cached in `sys.modules` on first import, acting as natural singletons.

#### Code Example (Metaclass Singleton)

```python
class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self):
        self.connected = True

db1 = DatabaseConnection()
db2 = DatabaseConnection()
print(db1 is db2)  # True
```

---

### 2. Factory Method

Defines an interface for creating an object but lets subclasses decide which class to instantiate.

#### Code Example

```python
class Dog:
    def speak(self): return "Woof"

class Cat:
    def speak(self): return "Meow"

class AnimalFactory:
    @staticmethod
    def get_animal(animal_type):
        animals = {"dog": Dog, "cat": Cat}
        if animal_type in animals:
            return animals[animal_type]()
        raise ValueError(f"Unknown animal: {animal_type}")

pet = AnimalFactory.get_animal("dog")
print(pet.speak())  # "Woof"
```

---

### 3. Builder

Separates the construction of a complex object from its representation, so the same construction process can build different representations step by step.

```python
class Pizza:
    def __init__(self):
        self.toppings = []
        self.size = None

    def __repr__(self):
        return f"Pizza(size={self.size}, toppings={self.toppings})"

class PizzaBuilder:
    def __init__(self):
        self.pizza = Pizza()

    def set_size(self, size):
        self.pizza.size = size
        return self  # enables fluent chaining

    def add_topping(self, topping):
        self.pizza.toppings.append(topping)
        return self

    def build(self):
        return self.pizza

pizza = (
    PizzaBuilder()
    .set_size("large")
    .add_topping("cheese")
    .add_topping("mushroom")
    .build()
)
print(pizza)  # Pizza(size=large, toppings=['cheese', 'mushroom'])
```

**Trap:** In Python, `Builder` is often replaced by simpler idioms — keyword arguments with defaults, or `dataclasses` with `field(default_factory=...)` — reach for a real Builder class only when construction genuinely requires multi-step validation or optional ordering.

---

## Structural Patterns (Adapter, Decorator, Proxy)

### 1. Adapter

Allows incompatible interfaces to work together by converting one interface into another expected by the client.

```python
class EuropeanSocket:
    def voltage(self): return 230

class USASocket:
    def voltage_us(self): return 120

class USAToEuropeanAdapter(EuropeanSocket):
    def __init__(self, usa_socket):
        self.usa_socket = usa_socket

    def voltage(self):
        # Adapts the US interface (voltage_us) to the European interface (voltage)
        return self.usa_socket.voltage_us() * (230 / 120)

adapter = USAToEuropeanAdapter(USASocket())
print(adapter.voltage())  # 230.0
```

---

### 2. Decorator

Dynamically adds behavior to an object without affecting others of the same class. (Distinct from Python's syntactic `@decorators`, though structurally similar — see [24_decorators.md](24_decorators.md) for the language feature).

```python
class Coffee:
    def cost(self): return 2.0
    def description(self): return "Coffee"

class MilkDecorator:
    def __init__(self, coffee):
        self._coffee = coffee
    def cost(self): return self._coffee.cost() + 0.5
    def description(self): return self._coffee.description() + " + Milk"

class SugarDecorator:
    def __init__(self, coffee):
        self._coffee = coffee
    def cost(self): return self._coffee.cost() + 0.2
    def description(self): return self._coffee.description() + " + Sugar"

drink = SugarDecorator(MilkDecorator(Coffee()))
print(drink.description(), drink.cost())  # Coffee + Milk + Sugar 2.7
```

---

### 3. Proxy

Provides a placeholder or surrogate for another object to control access to it (e.g., for lazy initialization, caching, logging, or authorization).

#### Code Example (Lazy Proxy)

```python
class RealService:
    def __init__(self):
        print("Expensive Service Initialized!")
    def perform_action(self):
        return "Action completed"

class LazyProxy:
    def __init__(self):
        self._real_service = None

    def perform_action(self):
        if self._real_service is None:
            self._real_service = RealService()  # Initialize only when needed
        return self._real_service.perform_action()

proxy = LazyProxy()
# 'Expensive Service Initialized!' has not printed yet.
print(proxy.perform_action())
```

---

## Behavioral Patterns (Strategy, Observer, Command)

### 1. Strategy

Defines a family of algorithms, encapsulates each one, and makes them interchangeable at runtime. In Python, since functions are first-class citizens, we don't need to define separate classes; we can simply pass functions.

#### Code Example

```python
# Strategy functions instead of classes
def credit_card_payment(amount):
    return f"Paid {amount} using Credit Card"

def paypal_payment(amount):
    return f"Paid {amount} using PayPal"

class Order:
    def __init__(self, amount):
        self.amount = amount

    def checkout(self, payment_strategy):
        return payment_strategy(self.amount)

order = Order(100)
print(order.checkout(paypal_payment))  # Paid 100 using PayPal
```

---

### 2. Observer

Defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified automatically.

```python
class Subject:
    def __init__(self):
        self._observers = []

    def subscribe(self, observer):
        self._observers.append(observer)

    def notify(self, event):
        for observer in self._observers:
            observer.update(event)

class EmailAlert:
    def update(self, event):
        print(f"Emailing alert: {event}")

class LogAlert:
    def update(self, event):
        print(f"Logging alert: {event}")

subject = Subject()
subject.subscribe(EmailAlert())
subject.subscribe(LogAlert())
subject.notify("Server CPU at 90%")
```

---

### 3. Command

Encapsulates a request as an object, letting you parameterize clients with queues, requests, and operations — supports undo/redo and deferred execution.

```python
class Light:
    def on(self): print("Light ON")
    def off(self): print("Light OFF")

class Command:
    def execute(self): raise NotImplementedError
    def undo(self): raise NotImplementedError

class LightOnCommand(Command):
    def __init__(self, light): self.light = light
    def execute(self): self.light.on()
    def undo(self): self.light.off()

class RemoteControl:
    def __init__(self):
        self.history = []

    def submit(self, command):
        command.execute()
        self.history.append(command)

    def undo_last(self):
        if self.history:
            self.history.pop().undo()

remote = RemoteControl()
remote.submit(LightOnCommand(Light()))
remote.undo_last()  # Light OFF
```

---

## Architectural Patterns (Repository, Dependency Injection)

### 1. Repository Pattern

Separates the business logic from data access logic, providing a collection-like interface to access domain objects (e.g., hiding SQL/ORM queries behind a repository class).

```python
class User:
    def __init__(self, id, name):
        self.id, self.name = id, name

class UserRepository:
    def __init__(self, db_connection):
        self._db = db_connection  # could be a raw SQL connection, ORM session, etc.

    def get_by_id(self, user_id):
        row = self._db.query_one("SELECT id, name FROM users WHERE id = ?", user_id)
        return User(row["id"], row["name"]) if row else None

    def save(self, user):
        self._db.execute("INSERT INTO users (id, name) VALUES (?, ?)", user.id, user.name)

# Business logic depends on the repository interface, not on raw SQL
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def rename_user(self, user_id, new_name):
        user = self.repository.get_by_id(user_id)
        user.name = new_name
        self.repository.save(user)
```

**Trap:** The value of the pattern is swapping the repository implementation (real DB vs. in-memory fake) in tests without touching `UserService` — if tests still need a real database, the abstraction isn't paying for itself.

---

### 2. Dependency Injection (DI)

A design pattern in which an object receives other objects (dependencies) that it requires, rather than constructing them internally. This improves testability by letting you inject mock dependencies during tests.

```python
class EmailSender:
    def send(self, to, message):
        print(f"Sending email to {to}: {message}")

# Bad: OrderService constructs its own dependency -- hard to test/swap
class OrderServiceTightlyCoupled:
    def __init__(self):
        self.sender = EmailSender()

# Good: dependency is injected via constructor
class OrderService:
    def __init__(self, sender):
        self.sender = sender  # any object with a .send(to, message) method works

    def place_order(self, user_email):
        self.sender.send(user_email, "Your order has been placed!")

# In tests, inject a fake instead of a real EmailSender
class FakeSender:
    def __init__(self): self.sent = []
    def send(self, to, message): self.sent.append((to, message))

service = OrderService(FakeSender())
service.place_order("test@example.com")
assert service.sender.sent == [("test@example.com", "Your order has been placed!")]
```

## Common Interview Questions

1. **"Why is Singleton often considered an anti-pattern?"** It introduces hidden global state, makes unit testing harder (state persists across tests unless explicitly reset), and tightly couples code to a specific implementation — dependency injection is usually preferred.
2. **"Difference between Strategy and Command patterns?"** Strategy swaps *how* an algorithm computes a result (interchangeable behavior); Command encapsulates a *request/action* itself as an object (supports queuing, logging, undo).
3. **Pitfall:** Overusing formal GoF patterns in Python where a plain function, closure, or dict lookup would be simpler and more idiomatic — Python's dynamic typing and first-class functions often eliminate the need for class-heavy patterns from statically-typed languages.
4. **Pitfall:** Implementing Singleton via a metaclass but forgetting it breaks under multiprocessing — each process gets its own memory space, so "one instance" only holds within a single process.
