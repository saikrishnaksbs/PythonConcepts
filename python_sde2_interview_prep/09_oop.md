# Object-Oriented Programming

Python's object-oriented programming (OOP) model is highly dynamic. Classes themselves are objects (instances of `type`), attributes are stored in dictionaries, and lookup is resolved dynamically at runtime. For SDE-2 interviews, you need to understand multiple inheritance, the Method Resolution Order (MRO), Mixins, and abstract base classes.

## Table of Contents

- [Classes & Objects (Instance vs Class Variables)](#classes--objects-instance-vs-class-variables)
- [Constructors and Destructors](#constructors-and-destructors)
- [Encapsulation & Abstraction](#encapsulation--abstraction)
- [Inheritance & Multiple Inheritance](#inheritance--multiple-inheritance)
- [Method Resolution Order (MRO) & C3 Linearization](#method-resolution-order-mro--c3-linearization)
- [Polymorphism & Duck Typing](#polymorphism--duck-typing)
- [Composition, Aggregation, and Mixins](#composition-aggregation-and-mixins)

---

## Classes & Objects (Instance vs Class Variables)

### Explanation

- **Class Variables**: Shared by all instances of a class. Defined directly within the class body.
- **Instance Variables**: Unique to each instance. Usually defined inside methods (like `__init__`) using `self`.

### Why it matters / internals

- Attribute resolution order: When you reference `obj.attr`, Python first looks in the instance dictionary (`obj.__dict__`). If not found, it searches the class dictionary (`obj.__class__.__dict__`), and then continues up the MRO.
- **Mutable class variables pitfall**: If a class variable is mutable (like a list), modifying it in-place affects all instances. However, rebinding it (e.g., `self.class_var = new_val`) creates an instance variable overriding the class variable for that instance.

### Code example

```python
class Developer:
    skills = []  # Class variable (mutable)

    def __init__(self, name):
        self.name = name  # Instance variable

d1 = Developer("Alice")
d2 = Developer("Bob")

d1.skills.append("Python")
print(d2.skills)  # ['Python'] (Shared!)

d1.skills = ["Go"]  # Rebinding! Creates an instance variable on d1.
print(d1.skills)  # ['Go']
print(d2.skills)  # ['Python']
```

---

## Constructors and Destructors

### Explanation

- `__new__` is the actual constructor (creates the object).
- `__init__` is the initializer (populates attributes).
- `__del__` is the destructor. It is called when the object's reference count drops to zero.

### Why it matters / internals

- Destructors (`__del__`) are **not** guaranteed to run immediately when an object goes out of scope, only when it is garbage collected.
- Circular references can delay or prevent `__del__` execution until the cyclic garbage collector runs.
- Exceptions raised in `__del__` are ignored; they are printed to `sys.stderr` but do not propagate.

---

## Encapsulation & Abstraction

### Explanation

- **Encapsulation**: Hiding internal state. Python does not enforce private variables; it uses naming conventions:
  - Single underscore (e.g., `_protected`): A warning to other developers not to access it directly.
  - Double underscore (e.g., `__private`): Triggers **name mangling** to prevent accidental overriding in subclasses.
- **Abstraction**: Hiding implementation details. Achieved using Abstract Base Classes (ABCs).

### Why it matters / internals

- **Name Mangling**: Python replaces `__private_var` in class `MyClass` with `_MyClass__private_var` in the object's `__dict__`. It can still be accessed, but prevents name clashes.

```python
class Account:
    def __init__(self):
        self.__balance = 100

a = Account()
# print(a.__balance)  # AttributeError
print(a._Account__balance)  # 100 (Accessing mangled name)
```

---

## Inheritance & Multiple Inheritance

### Explanation

Inheritance allows a subclass to inherit attributes and methods from a superclass. Python supports multiple inheritance, allowing a class to inherit from multiple parent classes.

### The Diamond Problem

When a class inherits from two classes that both inherit from a single base class, a method call could resolve to multiple paths. Python resolves this ambiguity using MRO.

---

## Method Resolution Order (MRO) & C3 Linearization

### Explanation

Python uses the **C3 Linearization** algorithm to compute the MRO (the order in which base classes are searched for a method or attribute).

### Why it matters / internals

- You can view a class's MRO using `Class.__mro__` or `Class.mro()`.
- C3 Linearization guarantees two properties:
  1. **Subclass first**: Children are checked before parents.
  2. **Local precedence**: The order of parents listed in the class definition is preserved.
- When calling `super().method()`, Python does **not** call the method of the parent class; it calls the method of the **next class in the MRO** of the active instance.

### Code example

```python
class A:
    def greet(self):
        print("A")

class B(A):
    def greet(self):
        print("B")
        super().greet()

class C(A):
    def greet(self):
        print("C")
        super().greet()

class D(B, C):
    def greet(self):
        print("D")
        super().greet()

# MRO: D -> B -> C -> A -> object
d = D()
d.greet()  # Outputs: D, B, C, A
```

---

## Polymorphism & Duck Typing

### Explanation

- **Polymorphism**: The ability to present the same interface for different underlying data types.
- **Duck Typing**: "If it walks like a duck and quacks like a duck, it's a duck." Python does not check the declared type of an object; it checks for the presence of the requested method or attribute at runtime.

### Code example

```python
class Dog:
    def speak(self):
        return "Woof"

class Duck:
    def speak(self):
        return "Quack"

def make_speak(animal):
    # Works for any object with a speak() method
    print(animal.speak())

make_speak(Dog())
make_speak(Duck())
```

---

## Composition, Aggregation, and Mixins

### Explanation

- **Composition**: "Has-a" relationship where the lifetime of the owned object is managed by the owner (e.g., a House has Rooms).
- **Aggregation**: "Has-a" relationship where the owned object can exist independently of the owner (e.g., a Department has Employees).
- **Mixins**: Small, focused classes designed to add specific functionality to other classes via multiple inheritance, without being intended for standalone instantiation.

### Code example (Mixin)

```python
import json

class JSONSerializableMixin:
    def to_json(self):
        return json.dumps(self.__dict__)

class User(JSONSerializableMixin):
    def __init__(self, name, email):
        self.name = name
        self.email = email

u = User("Alice", "alice@example.com")
print(u.to_json())  # {"name": "Alice", "email": "alice@example.com"}
```
