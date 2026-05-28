"""Operator Schema Compiler-And-Runner ("OSCAR") for the math domain.

Compiles an LLM-emitted operator schema into a Python program, evaluates
it, and returns the numeric result. The DSL is a small whitelist
(`ALLOWED_DSL_OPS` — `add`, `sub`, `mul`, `div`, `ceil_div`, `floor_div`,
`remainder`, `next_multiple`, `complement`, `difference`, `percent_of`,
`percent_left`, `avg`, ...) so the compiler can validate the schema before
ever executing anything. Provides:

- `parse_schema_fields` / `schema_to_preview` — schema (de)serialization,
- `assign_semantic_cluster` — coarse cluster label for retrieval,
- `deterministic_compile_and_execute` — the actual compile + run step.

Every math runner downstream of OSCAR (heir, atlas, atlas_rg, cass,
cass_r2, cass_r4) reaches into this module for its compile step.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import re
from typing import Any

from dart_research.eir.python_exec import execute_python_snippet
from dart_research.parsing.normalization import extract_numeric


ALLOWED_DSL_OPS = {
    "add",
    "sub",
    "mul",
    "div",
    "ceil_div",
    "floor_div",
    "remainder",
    "next_multiple",
    "complement",
    "difference",
    "percent_of",
    "percent_left",
    "avg",
    "area_rect",
    "area_square",
    "area_triangle",
    "perimeter_rect",
    "area_circle",
    "circumference_circle",
    "identity",
}


@dataclass(slots=True)
class QuantitySpec:
    name: str
    value_text: str
    unit: str
    role: str
    entity: str


@dataclass(slots=True)
class OperatorSchema:
    target_variable: str
    final_target_type: str
    quantities: list[QuantitySpec]
    operator_family: str
    relation_chain: str
    discretization_flags: list[str]
    postprocess_flags: list[str]
    geometry_formula_family: str
    unresolved_items_count: int
    complete: int


def sanitize_identifier(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_]+", "_", str(value).strip().lower()).strip("_")
    if not token:
        return "value"
    if token[0].isdigit():
        token = f"v_{token}"
    return token


def parse_flag_list(raw: str) -> list[str]:
    items = []
    for token in re.split(r"[,;/\n]+", str(raw)):
        clean = token.strip().lower()
        if clean:
            items.append(clean)
    return items or ["none"]


def parse_quantity_specs(raw: str) -> list[QuantitySpec]:
    specs: list[QuantitySpec] = []
    for chunk in re.split(r"[;\n]+", str(raw).strip()):
        chunk = chunk.strip()
        if not chunk:
            continue
        data: dict[str, str] = {"name": "", "value": "", "unit": "none", "role": "none", "entity": "none"}
        for idx, part in enumerate(chunk.split("|")):
            piece = part.strip()
            if not piece:
                continue
            weird = re.match(r"name=([^=]+)=value=(.+)", piece, flags=re.IGNORECASE)
            if weird:
                data["name"] = weird.group(1).strip()
                data["value"] = weird.group(2).strip()
                continue
            if idx == 0 and "=" in piece and not piece.lower().startswith(("unit=", "role=", "entity=", "value=", "name=")):
                left, right = piece.split("=", 1)
                data["name"] = left.strip()
                data["value"] = right.strip()
                continue
            if "=" in piece:
                key, value = piece.split("=", 1)
                data[key.strip().lower()] = value.strip()
        raw_name = str(data.get("name", "")).strip()
        raw_role = str(data.get("role", "")).strip()
        name = sanitize_identifier(raw_name) if raw_name else (sanitize_identifier(raw_role) if raw_role else "")
        value_text = data.get("value", "").strip()
        if not value_text and "=" in str(data.get("name", "")):
            left, right = str(data["name"]).split("=", 1)
            name = sanitize_identifier(left)
            value_text = right.strip()
        if not name or not value_text:
            continue
        specs.append(
            QuantitySpec(
                name=name,
                value_text=value_text,
                unit=data.get("unit", "none").strip() or "none",
                role=sanitize_identifier(data.get("role", "none")) or "none",
                entity=sanitize_identifier(data.get("entity", "none")) or "none",
            )
        )
    return specs


def parse_numeric_literal(raw: str) -> float:
    text = str(raw).strip().replace(",", "")
    if not text:
        raise ValueError("empty numeric literal")
    if re.fullmatch(r"-?\d+(?:\.\d+)?\s*/\s*-?\d+(?:\.\d+)?", text):
        left, right = re.split(r"/", text, maxsplit=1)
        return float(left) / float(right)
    if text.endswith("%"):
        return float(text[:-1]) / 100.0
    numeric = extract_numeric(text)
    return float(numeric)


def _compile_ast_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Expression):
        return _compile_ast_expr(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return repr(float(node.value))
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.fullmatch(r"-?\d+(?:\.\d+)?%?", node.value.strip()):
        return repr(parse_numeric_literal(node.value))
    if isinstance(node, ast.Name):
        return sanitize_identifier(node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return f"(-{_compile_ast_expr(node.operand)})"
    if isinstance(node, ast.BinOp):
        left = _compile_ast_expr(node.left)
        right = _compile_ast_expr(node.right)
        if isinstance(node.op, ast.Add):
            return f"({left} + {right})"
        if isinstance(node.op, ast.Sub):
            return f"({left} - {right})"
        if isinstance(node.op, ast.Mult):
            return f"({left} * {right})"
        if isinstance(node.op, ast.Div):
            return f"({left} / {right})"
        if isinstance(node.op, ast.Pow):
            return f"({left} ** {right})"
        raise ValueError("unsupported infix operator")
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        func = sanitize_identifier(node.func.id)
        args = [_compile_ast_expr(arg) for arg in node.args]
        return _compile_dsl_expr(f"{func}({','.join(args)})")
    raise ValueError("unsupported infix expression")


def parse_schema_fields(fields: dict[str, Any]) -> OperatorSchema:
    operator_family = str(fields.get("operator_family", "other")).strip().lower() or "other"
    operator_family = re.split(r"[|,/]", operator_family)[0].strip() or "other"
    unresolved_raw = extract_numeric(str(fields.get("unresolved_items_count", "0")) or "0")
    unresolved_items_count = int(unresolved_raw) if re.fullmatch(r"-?\d+", unresolved_raw) else 0
    return OperatorSchema(
        target_variable=sanitize_identifier(fields.get("target_variable", "result")) or "result",
        final_target_type=str(fields.get("final_target_type", "other")).strip().lower() or "other",
        quantities=parse_quantity_specs(str(fields.get("quantities", ""))),
        operator_family=operator_family,
        relation_chain=str(fields.get("relation_chain", "")).strip(),
        discretization_flags=parse_flag_list(str(fields.get("discretization_flags", "none"))),
        postprocess_flags=parse_flag_list(str(fields.get("postprocess_flags", "none"))),
        geometry_formula_family=str(fields.get("geometry_formula_family", "none")).strip().lower() or "none",
        unresolved_items_count=unresolved_items_count,
        complete=int(str(fields.get("complete", "")).strip().lower() in {"yes", "true", "1"}),
    )


def schema_to_preview(schema: OperatorSchema) -> str:
    quantities = "; ".join(
        f"{item.name}={item.value_text}|unit={item.unit}|role={item.role}|entity={item.entity}" for item in schema.quantities
    )
    return (
        f"target_variable={schema.target_variable}; "
        f"final_target_type={schema.final_target_type}; "
        f"operator_family={schema.operator_family}; "
        f"relation_chain={schema.relation_chain}; "
        f"discretization_flags={','.join(schema.discretization_flags)}; "
        f"postprocess_flags={','.join(schema.postprocess_flags)}; "
        f"geometry_formula_family={schema.geometry_formula_family}; "
        f"unresolved_items_count={schema.unresolved_items_count}; "
        f"complete={schema.complete}; "
        f"quantities={quantities}"
    )


def assign_semantic_cluster(question: str) -> str:
    text = str(question).lower()
    if re.search(r"\b(rectangle|triangle|circle|radius|diameter|perimeter|area|square feet|square units)\b", text):
        return "geometry_formula_family"
    if re.search(r"\baverage|mean|on average|times as many|twice|thrice|three times|double|triple\b", text):
        return "average_repeated_times"
    if re.search(r"\bpercent|%|fraction|half|quarter|third|remaining percent|what fraction\b", text):
        return "percent_fraction_complement"
    if re.search(r"\bremainder\b|\bdivisible\b|\bdivided evenly\b|\bnext multiple\b|\bgroup(s)? of\b|\bpackage\b|\bbox(es)?\b|\bbag(s)?\b|\bcarton(s)?\b", text):
        return "remainder_packaging_divisibility"
    if re.search(r"\bceil\b|\bfloor\b|\bat least\b|\bminimum\b|\bfull\b|\bwhole\b|\btrip(s)?\b|\bbus(es)?\b|\bseat(s)?\b", text):
        return "ceil_floor_partial_group"
    if re.search(r"\bhow many more|left over|leftover|difference|more than|less than|remain|remaining\b", text):
        return "comparison_leftover_more"
    if re.search(r"\bper\b|\beach hour\b|\bper hour\b|\bper day\b|\brate\b|\bspeed\b|\bmiles per\b|\bfor every\b|\bratio\b|\bproportion\b", text):
        return "ratio_proportion_rate"
    return "direct_exact_arithmetic"


def _quantity_python_lines(schema: OperatorSchema) -> list[str]:
    lines: list[str] = []
    for item in schema.quantities:
        raw = item.value_text.strip()
        if any(symbol in raw for symbol in ["+", "-", "*", "/", "(", ")"]) and not re.fullmatch(r"-?\d+(?:\.\d+)?%?", raw):
            try:
                expr = _compile_dsl_expr(raw)
                lines.append(f"{item.name} = {expr}")
                continue
            except Exception:
                pass
        try:
            value = parse_numeric_literal(item.value_text)
            lines.append(f"{item.name} = {repr(value)}")
            continue
        except Exception:
            pass
        try:
            expr = _compile_dsl_expr(item.value_text)
            lines.append(f"{item.name} = {expr}")
        except Exception:
            continue
    return lines


def _dsl_args(raw: str) -> list[str]:
    inner = raw.strip()
    if not inner:
        return []
    items: list[str] = []
    buf: list[str] = []
    depth = 0
    for char in inner:
        if char == "," and depth == 0:
            token = "".join(buf).strip()
            if token:
                items.append(token)
            buf = []
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        buf.append(char)
    token = "".join(buf).strip()
    if token:
        items.append(token)
    return items


def _resolve_arg(token: str) -> str:
    clean = token.strip()
    if re.fullmatch(r"-?\d+(?:\.\d+)?%?", clean):
        return repr(parse_numeric_literal(clean))
    if any(symbol in clean for symbol in ["+", "-", "*", "/", "(", ")"]):
        return _compile_dsl_expr(clean)
    return sanitize_identifier(clean)


def _normalize_relation_text(text: str) -> str:
    normalized = str(text).strip()
    normalized = normalized.replace("加", "+").replace("−", "-").replace("×", "*").replace("÷", "/")
    return normalized


def _compile_dsl_expr(expr: str) -> str:
    token = _normalize_relation_text(expr)
    if re.fullmatch(r"-?\d+(?:\.\d+)?%?", token):
        return repr(parse_numeric_literal(token))
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
        return sanitize_identifier(token)
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\((.*)\)", token)
    if not match:
        try:
            return _compile_ast_expr(ast.parse(token, mode="eval"))
        except Exception as error:
            raise ValueError(f"unsupported expression: {expr}") from error
    op = match.group(1).strip().lower()
    args = [_resolve_arg(arg) for arg in _dsl_args(match.group(2))]
    if op not in ALLOWED_DSL_OPS:
        raise ValueError(f"unsupported op: {op}")
    if op == "add":
        return "(" + " + ".join(args) + ")"
    if op == "sub":
        return f"({args[0]} - {args[1]})"
    if op == "mul":
        return "(" + " * ".join(args) + ")"
    if op == "div":
        return f"({args[0]} / {args[1]})"
    if op == "ceil_div":
        return f"math.ceil({args[0]} / {args[1]})"
    if op == "floor_div":
        return f"math.floor({args[0]} / {args[1]})"
    if op == "remainder":
        return f"({args[0]} % {args[1]})"
    if op == "next_multiple":
        return f"(math.ceil({args[0]} / {args[1]}) * {args[1]})"
    if op == "complement":
        return f"({args[0]} - {args[1]})"
    if op == "difference":
        return f"abs({args[0]} - {args[1]})"
    if op == "percent_of":
        return f"(({args[0]} / 100.0) * {args[1]})"
    if op == "percent_left":
        return f"(({args[0]} / 100.0) * {args[1]})"
    if op == "avg":
        return f"((" + " + ".join(args) + f") / {len(args)})"
    if op == "area_rect":
        return f"({args[0]} * {args[1]})"
    if op == "area_square":
        return f"({args[0]} ** 2)"
    if op == "area_triangle":
        return f"(({args[0]} * {args[1]}) / 2)"
    if op == "perimeter_rect":
        return f"(2 * ({args[0]} + {args[1]}))"
    if op == "area_circle":
        return f"(math.pi * ({args[0]} ** 2))"
    if op == "circumference_circle":
        return f"(2 * math.pi * {args[0]})"
    if op == "identity":
        return f"{args[0]}"
    raise ValueError(f"unhandled op: {op}")


def compile_relation_chain_to_code(schema: OperatorSchema, relation_chain: str | None = None) -> tuple[str, str]:
    chain = _normalize_relation_text(relation_chain if relation_chain is not None else schema.relation_chain)
    if not chain:
        chain = fallback_relation_chain(schema)
    if not chain:
        raise ValueError("empty relation chain")
    lines = _quantity_python_lines(schema)
    try:
        for stmt in re.split(r"[;\n]+", chain):
            clean = stmt.strip()
            if not clean:
                continue
            if "=" not in clean:
                raise ValueError(f"invalid assignment: {clean}")
            lhs, rhs = clean.split("=", 1)
            name = sanitize_identifier(lhs)
            expr = _compile_dsl_expr(rhs)
            lines.append(f"{name} = {expr}")
    except Exception:
        fallback = fallback_relation_chain(schema)
        if not fallback or fallback == chain:
            raise
        lines = _quantity_python_lines(schema)
        chain = fallback
        for stmt in re.split(r"[;\n]+", chain):
            clean = stmt.strip()
            if not clean:
                continue
            lhs, rhs = clean.split("=", 1)
            name = sanitize_identifier(lhs)
            expr = _compile_dsl_expr(rhs)
            lines.append(f"{name} = {expr}")
    if not any(line.startswith("result =") for line in lines):
        target = sanitize_identifier(schema.target_variable or "result")
        if any(line.startswith(f"{target} =") for line in lines):
            lines.append(f"result = {target}")
        else:
            raise ValueError("no result assignment")
    return "\n".join(lines) + "\n", chain


def fallback_relation_chain(schema: OperatorSchema) -> str:
    names = [item.name for item in schema.quantities]
    if len(names) < 2:
        if len(names) == 1:
            return f"result=identity({names[0]})"
        return ""
    flags = set(schema.discretization_flags + schema.postprocess_flags)
    family = schema.operator_family
    target = sanitize_identifier(schema.target_variable)
    for item in schema.quantities:
        if target and (target == item.name or target in item.role or item.role in target):
            return f"result=identity({item.name})"
    if "ceil" in flags:
        return f"result=ceil_div({names[0]},{names[1]})"
    if "floor" in flags:
        return f"result=floor_div({names[0]},{names[1]})"
    if "remainder" in flags:
        return f"result=remainder({names[0]},{names[1]})"
    if "complement" in flags or "leftover" in flags:
        return f"result=complement({names[0]},{names[1]})"
    if "difference" in flags or family == "comparison":
        return f"result=difference({names[0]},{names[1]})"
    if family in {"rate", "ratio"} and len(names) >= 2:
        return f"result=div({names[0]},{names[1]})"
    if family == "average":
        return "result=avg(" + ",".join(names) + ")"
    if family == "geometry":
        formula = schema.geometry_formula_family
        if formula == "rectangle_area" and len(names) >= 2:
            return f"result=area_rect({names[0]},{names[1]})"
        if formula == "square_area" and names:
            return f"result=area_square({names[0]})"
        if formula == "triangle_area" and len(names) >= 2:
            return f"result=area_triangle({names[0]},{names[1]})"
        if formula == "rectangle_perimeter" and len(names) >= 2:
            return f"result=perimeter_rect({names[0]},{names[1]})"
        if formula == "circle_area" and names:
            return f"result=area_circle({names[0]})"
        if formula == "circle_circumference" and names:
            return f"result=circumference_circle({names[0]})"
    if family == "additive":
        return "result=add(" + ",".join(names) + ")"
    if family in {"multiplicative", "partition", "counting"}:
        return f"result=mul({names[0]},{names[1]})"
    if family in {"arithmetic", "other"} and target:
        for item in schema.quantities:
            if target and (target == item.name or target in item.role or item.role in target):
                return f"result=identity({item.name})"
    return ""


def deterministic_compile_and_execute(schema: OperatorSchema, relation_chain: str | None = None) -> dict[str, Any]:
    code, used_chain = compile_relation_chain_to_code(schema, relation_chain=relation_chain)
    payload = execute_python_snippet(code)
    payload["code"] = code
    payload["used_relation_chain"] = used_chain
    return payload
