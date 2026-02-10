"""A simple calculator module with a bug."""


def add(a, b):
    """Add two numbers."""
    return a + b


def subtract(a, b):
    """Subtract b from a."""
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    return a * b


def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b


def power(base, exponent):
    """Calculate base raised to the power of exponent."""
    result = 1
    for _ in range(exponent):
        result *= base
    return result


if __name__ == "__main__":
    print("Testing calculator:")
    print(f"add(5, 3) = {add(5, 3)}")
    print(f"subtract(10, 4) = {subtract(10, 4)}")
    print(f"multiply(6, 7) = {multiply(6, 7)}")
    print(f"divide(15, 3) = {divide(15, 3)}")
    print(f"power(2, 8) = {power(2, 8)}")

    # This should now raise ValueError instead of ZeroDivisionError
    print("\nTrying to divide by zero...")
    try:
        result = divide(10, 0)
        print(f"divide(10, 0) = {result}")
    except ValueError as e:
        print(f"divide(10, 0) raised ValueError: {e}")
