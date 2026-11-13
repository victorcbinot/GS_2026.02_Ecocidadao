from __future__ import annotations

import ast
import math
import operator
from collections.abc import Callable
from typing import Any


class CalculationError(ValueError):
    pass


_MAX_EXPRESSION_LENGTH = 300
_MAX_EXPONENT = 100
_MAX_ABSOLUTE_RESULT = 1e18
_BINARY_OPERATORS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
}
_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
}


def _validate_number(value: Any) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalculationError("A expressao deve produzir um numero.")
    if not math.isfinite(float(value)):
        raise CalculationError("O resultado nao pode ser infinito ou NaN.")
    if abs(float(value)) > _MAX_ABSOLUTE_RESULT:
        raise CalculationError("O resultado excede o limite permitido.")
    return value


def _evaluate(node: ast.AST) -> int | float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)

    if isinstance(node, ast.Constant):
        return _validate_number(node.value)

    if isinstance(node, ast.BinOp):
        operator_function = _BINARY_OPERATORS.get(type(node.op))
        if operator_function is None:
            raise CalculationError("Operador nao permitido.")
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow):
            if abs(float(right)) > _MAX_EXPONENT:
                raise CalculationError("Expoente acima do limite permitido.")
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise CalculationError("Divisao por zero nao permitida.")
        try:
            result = operator_function(left, right)
        except (ArithmeticError, ValueError) as error:
            raise CalculationError("Operacao matematica invalida.") from error
        return _validate_number(result)

    if isinstance(node, ast.UnaryOp):
        operator_function = _UNARY_OPERATORS.get(type(node.op))
        if operator_function is None:
            raise CalculationError("Operador unario nao permitido.")
        return _validate_number(operator_function(_evaluate(node.operand)))

    if isinstance(node, ast.Name):
        if node.id not in _CONSTANTS:
            raise CalculationError("Variavel nao permitida na expressao.")
        return _CONSTANTS[node.id]

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise CalculationError("Chamada de funcao nao permitida.")
        function = _FUNCTIONS.get(node.func.id)
        if function is None:
            raise CalculationError("Funcao nao permitida.")
        if node.keywords:
            raise CalculationError("Argumentos nomeados nao sao permitidos.")
        arguments = [_evaluate(argument) for argument in node.args]
        if node.func.id == "round":
            if not 1 <= len(arguments) <= 2:
                raise CalculationError("round espera um ou dois argumentos.")
            if len(arguments) == 2:
                digits = arguments[1]
                if not isinstance(digits, int) or not -10 <= digits <= 10:
                    raise CalculationError(
                        "O numero de casas decimais deve estar entre -10 e 10."
                    )
        elif node.func.id in {"min", "max"}:
            if not arguments:
                raise CalculationError(
                    f"{node.func.id} espera pelo menos um argumento."
                )
        elif len(arguments) != 1:
            raise CalculationError(
                f"{node.func.id} espera exatamente um argumento."
            )
        try:
            result = function(*arguments)
        except (ArithmeticError, ValueError, TypeError) as error:
            raise CalculationError("Funcao matematica invalida.") from error
        return _validate_number(result)

    raise CalculationError("Expressao contem elemento nao permitido.")


def calculate(expression: str) -> int | float:
    if not isinstance(expression, str):
        raise CalculationError("A expressao deve ser texto.")
    normalized = " ".join(expression.split())
    if not normalized:
        raise CalculationError("A expressao nao pode ser vazia.")
    if len(normalized) > _MAX_EXPRESSION_LENGTH:
        raise CalculationError("A expressao excede o limite de caracteres.")
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as error:
        raise CalculationError("Expressao matematica invalida.") from error
    return _evaluate(tree)


def format_number(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


__all__ = ["CalculationError", "calculate", "format_number"]
