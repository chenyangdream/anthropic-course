import unittest
from main import calculate_pi


class TestCalculatePi(unittest.TestCase):

    def test_pi_to_5th_digit(self):
        """Pi rounded to 5 decimal places should equal 3.14159."""
        result = calculate_pi(5)
        self.assertEqual(result, 3.14159)

    def test_pi_to_2nd_digit(self):
        """Pi rounded to 2 decimal places should equal 3.14."""
        result = calculate_pi(2)
        self.assertEqual(result, 3.14)

    def test_pi_to_0_digits(self):
        """Pi rounded to 0 decimal places should equal 3.0."""
        result = calculate_pi(0)
        self.assertEqual(result, 3.0)

    def test_return_type_is_float(self):
        """The return type should always be a float."""
        result = calculate_pi(5)
        self.assertIsInstance(result, float)

    def test_default_digits_is_5(self):
        """Calling calculate_pi() with no arguments should default to 5 digits."""
        result = calculate_pi()
        self.assertEqual(result, 3.14159)


if __name__ == "__main__":
    unittest.main()
