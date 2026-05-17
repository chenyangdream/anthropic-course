def calculate_pi(digits: int = 5) -> float:
    """
    Calculate Pi to a given number of decimal digits using the
    Leibniz formula for Pi:
        pi = 4 * (1 - 1/3 + 1/5 - 1/7 + 1/9 - ...)

    Args:
        digits (int): Number of decimal digits to round Pi to. Default is 5.

    Returns:
        float: Pi rounded to the specified number of decimal digits.
    """
    pi = 0.0
    iterations = 1_000_000  # More iterations = more precision
    for i in range(iterations):
        pi += ((-1) ** i) / (2 * i + 1)
    pi *= 4
    return round(pi, digits)


if __name__ == "__main__":
    pi_value = calculate_pi(5)
    print(f"Pi to the 5th digit: {pi_value}")
