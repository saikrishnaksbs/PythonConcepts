# def log_execution(func):
#     def wrapper(*args, **kwargs):
#         print(f"Calling {func.__name__}")
#         result = func(*args, **kwargs)
#         print(f"{func.__name__} completed")
#         return result
#     return wrapper

# # @log_execution
# # def greet(name):
# #     return f"Hello, {name}"

# def greet(name):
#     print("name", name)
#     return f"Hello, {name}"
# # 2. Wrap it and overwrite the original variable name
# # print(greet("Alice"))
# greet = log_execution(greet)

# print(greet("Alice"))

# def add_repr(cls):
#     # Dynamically inject or override __repr__
#     cls.__repr__ = lambda self: f"{self.__class__.__name__}({self.__dict__})"
#     return cls

# @add_repr
# class Point:
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y

# p = Point(1, 2)
# print(p)  # Point({'x': 1, 'y': 2})

def repeat(times):
    def decorator_repeat(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator_repeat

@repeat(times=3)
def greet(name):
    print(f"Hi {name}")

greet("Bob")  # Prints "Hi Bob" 3 times

