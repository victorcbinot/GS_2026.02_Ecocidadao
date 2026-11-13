from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.agent.calculator import (
    CalculationError,
    calculate,
    format_number,
)


class CalculatorTests(unittest.TestCase):
    def test_simple_arithmetic_and_parentheses(self) -> None:
        self.assertEqual(calculate("2 + 3 * 4"), 14)
        self.assertEqual(calculate("(2 + 3) * 4"), 20)
        self.assertEqual(calculate("10 / 4"), 2.5)
        self.assertEqual(calculate("10 // 4"), 2)
        self.assertEqual(calculate("10 % 4"), 2)
        self.assertEqual(calculate("2 ** 10"), 1024)

    def test_safe_functions(self) -> None:
        self.assertEqual(calculate("sqrt(81)"), 9)
        self.assertEqual(calculate("round(1.2345, 2)"), 1.23)
        self.assertEqual(calculate("min(3, 5, 1)"), 1)
        self.assertEqual(calculate("max(3, 5, 1)"), 5)
        self.assertEqual(calculate("abs(-7)"), 7)
        self.assertEqual(calculate("ceil(2.1)"), 3)
        self.assertEqual(calculate("floor(2.9)"), 2)

    def test_rejects_code_execution_and_attributes(self) -> None:
        for expression in (
            "__import__('os').system('whoami')",
            "open('arquivo.txt')",
            "(1).__class__",
            "lambda: 1",
            "x = 1",
            "[1, 2, 3]",
            "{'a': 1}",
            "True",
        ):
            with self.subTest(expression=expression):
                with self.assertRaises(CalculationError):
                    calculate(expression)

    def test_rejects_invalid_operations_and_limits(self) -> None:
        for expression in (
            "",
            "   ",
            "1 / 0",
            "1 // 0",
            "1 % 0",
            "2 ** 101",
            "1e309",
            "(",
            "2 +",
            "sum(1, 2)",
            "round(1.2, 20)",
        ):
            with self.subTest(expression=expression):
                with self.assertRaises(CalculationError):
                    calculate(expression)

    def test_rejects_oversized_expression(self) -> None:
        with self.assertRaises(CalculationError):
            calculate("1 + " * 200 + "1")

    def test_format_number(self) -> None:
        self.assertEqual(format_number(4), "4")
        self.assertEqual(format_number(4.0), "4")
        self.assertEqual(format_number(4.25), "4.25")
        self.assertEqual(format_number(1 / 3), "0.333333")


if __name__ == "__main__":
    unittest.main()
