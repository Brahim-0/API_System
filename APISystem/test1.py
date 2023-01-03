def decorator(f):
    def wrapper():
        print("this line was executed.")
        f()

    return wrapper


@decorator
def func():
    print("in")

@decorator
def func1():
    print("i2")

print(func.__name__)



