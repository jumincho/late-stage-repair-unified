"""Sandbox executor for the `PYTHON_RECOMPUTE` action.

Compiles and runs an LLM-produced Python snippet inside a tightly-scoped
namespace: `__builtins__` is replaced with a whitelist of safe primitives
(`abs`, `min`, `max`, `sum`, `round`, `len`, `int`, `float`, `math`) so the
snippet cannot reach the filesystem or network. Execution is wall-clock
limited via `timeout_s`. The result dict contains the captured stdout, the
exception class name if one was raised, and the final value of `result` if
the snippet set it.
"""

from __future__ import annotations

import ast
import contextlib
import io
import math
import time
from typing import Any


SAFE_GLOBALS = {
    "__builtins__": {},
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "round": round,
    "len": len,
    "int": int,
    "float": float,
    "math": math,
}


def execute_python_snippet(code: str, timeout_s: float = 1.0) -> dict[str, Any]:
    text = (code or "").strip()
    if not text:
        return {
            "success": 0,
            "result": "",
            "stdout": "",
            "error": "empty_code",
            "latency_s": 0.0,
        }
    start = time.perf_counter()
    namespace: dict[str, Any] = {}
    stdout = io.StringIO()
    try:
        tree = ast.parse(text, mode="exec")
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith, ast.Try, ast.While, ast.For, ast.AsyncFor, ast.Lambda, ast.ClassDef)):
                raise ValueError(f"disallowed_node:{type(node).__name__}")
        compiled = compile(tree, "<eir-python>", "exec")
        with contextlib.redirect_stdout(stdout):
            exec(compiled, SAFE_GLOBALS, namespace)
        if "result" in namespace:
            result = namespace["result"]
        elif stdout.getvalue().strip():
            result = stdout.getvalue().strip().splitlines()[-1]
        else:
            expr_result = _try_eval_expression(text, namespace)
            result = expr_result if expr_result is not None else ""
        latency = time.perf_counter() - start
        if latency > timeout_s:
            return {
                "success": 0,
                "result": "",
                "stdout": stdout.getvalue().strip(),
                "error": "timeout_budget_exceeded",
                "latency_s": latency,
            }
        return {
            "success": int(result != ""),
            "result": str(result).strip(),
            "stdout": stdout.getvalue().strip(),
            "error": "",
            "latency_s": latency,
        }
    except Exception as exc:  # pragma: no cover - branch exercises runtime failures
        return {
            "success": 0,
            "result": "",
            "stdout": stdout.getvalue().strip(),
            "error": str(exc),
            "latency_s": time.perf_counter() - start,
        }


def _try_eval_expression(code: str, namespace: dict[str, Any]) -> Any | None:
    text = code.strip()
    if "\n" in text or "=" in text:
        return None
    try:
        compiled = compile(ast.parse(text, mode="eval"), "<eir-python-expr>", "eval")
        return eval(compiled, SAFE_GLOBALS, namespace)
    except Exception:
        return None
