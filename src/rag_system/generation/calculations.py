"""Bounded decimal arithmetic over operands linked to validated evidence.

This checks numeric membership and arithmetic, not metric/column entailment.
Never execute provider expressions with eval or accept calls/attributes.
"""

import ast
import os
import re
from decimal import ROUND_HALF_UP, Decimal, DecimalException, localcontext

NUMBER = re.compile(r"(?<![\w.])\(?[+-]?\d+(?:,\d{3})*(?:\.\d+)?\)?(?![\w.])")
SCALAR = re.compile(r"-?\d{1,24}(?:\.\d{1,12})?\Z")
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,19}\Z")
# Structural constants only: averages, percentages, day counts, unit conversion.
CONSTANTS = {1, 2, 3, 4, 12, 100, 360, 365, 366, 1000, 1000000, 1000000000}


def _decimal(value):
    if os.getenv("FINANCIAL_DECIMAL_INPUT") == "1" and isinstance(value, str) and len(value) <= 64:
        magnitude = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
        if re.fullmatch(r"\(" + magnitude + r"\)", value):
            value = "-" + value[1:-1].replace(",", "")
        elif re.fullmatch(r"-?" + magnitude, value):
            value = value.replace(",", "")
    if not isinstance(value, str) or not SCALAR.fullmatch(value):
        raise ValueError("invalid decimal")
    return Decimal(value)


def _quote_numbers(quote):
    values = set()
    for match in NUMBER.finditer(quote):
        token = match.group().replace(",", "")
        if token.startswith("(") and token.endswith(")"):
            token = "-" + token[1:-1]
        token = token.strip("()")
        try:
            values.add(Decimal(token))
        except DecimalException:
            pass
    return values


def evaluate(expression, operands):
    """Evaluate only bounded +, -, *, / and unary signs with Decimal."""
    if not isinstance(expression, str) or not 0 < len(expression) <= 200:
        raise ValueError("invalid expression")
    tree = ast.parse(expression, mode="eval")
    if len(list(ast.walk(tree))) > 80:
        raise ValueError("expression too large")
    used = set()

    def visit(node):
        if isinstance(node, ast.Name) and node.id in operands:
            used.add(node.id)
            return operands[node.id]
        if isinstance(node, ast.Constant) and type(node.value) is int:
            if node.value in CONSTANTS:
                return Decimal(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                value = left + right
            elif isinstance(node.op, ast.Sub):
                value = left - right
            elif isinstance(node.op, ast.Mult):
                value = left * right
            elif isinstance(node.op, ast.Div):
                value = left / right
            else:
                raise ValueError("unsupported operator")
            if not value.is_finite() or abs(value) > Decimal("1e30"):
                raise ValueError("result out of bounds")
            return value
        raise ValueError("unsupported expression")

    with localcontext() as ctx:
        ctx.prec = 50
        result = visit(tree.body)
    if used != set(operands) or not used:
        raise ValueError("unused operands")
    return result


def directional_contradiction(answer):
    """Reject explicit increase/decrease from A to B contradictions, not general entailment."""
    number = r"(-?\d+(?:,\d{3})*(?:\.\d+)?)"
    pattern = (
        r"\b(increased|decreased|rose|fell)\b[^.;!?]{0,100}?\bfrom\s*\$?"
        + number
        + r"\s*(%|percent|million|billion|thousand)?"
        + r"(?:\s+in\s+\d{4})?\s+to\s*\$?"
        + number
        + r"\s*(%|percent|million|billion|thousand)?\b"
    )
    for match in re.finditer(pattern, answer, re.I):
        direction, old, old_unit, new, new_unit = match.groups()
        # Different scales need a separate conversion; do not guess.
        if (old_unit or "").lower() != (new_unit or "").lower():
            continue
        old, new = Decimal(old.replace(",", "")), Decimal(new.replace(",", ""))
        if (
            direction.lower() in ("increased", "rose")
            and new <= old
            or direction.lower() in ("decreased", "fell")
            and new >= old
        ):
            return True
    return False


def validate_calculations(payload):
    """Return a rendered answer and diagnostic after source quotes are validated."""
    calculations = payload.get("calculations")
    if not isinstance(calculations, list) or len(calculations) > 4:
        return None, "invalid_calculations"
    answer = payload["answer"]
    seen = set()
    for calc in calculations:
        try:
            if not isinstance(calc, dict):
                raise ValueError("invalid calculation")
            name = calc.get("id")
            if not isinstance(name, str) or not NAME.fullmatch(name) or name in seen:
                raise ValueError("invalid id")
            seen.add(name)
            marker = "{{" + name + "}}"
            if answer.count(marker) != 1:
                raise ValueError("missing or repeated result marker")
            places = calc.get("decimal_places")
            if type(places) is not int or not 0 <= places <= 8:
                raise ValueError("invalid precision")
            entries = calc.get("operands")
            if not isinstance(entries, list) or not 1 <= len(entries) <= 12:
                raise ValueError("invalid operands")
            operands = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("invalid operand")
                key = entry.get("name")
                if not isinstance(key, str) or not NAME.fullmatch(key) or key in operands:
                    raise ValueError("invalid operand name")
                index = entry.get("evidence_index")
                if type(index) is not int or not 0 <= index < len(payload["evidence"]):
                    raise ValueError("invalid evidence index")
                for field in ("metric", "period", "unit"):
                    if not isinstance(entry.get(field), str) or not entry[field].strip():
                        raise ValueError("missing operand metadata")
                value = _decimal(entry.get("value"))
                if value not in _quote_numbers(payload["evidence"][index]["quote"]):
                    return None, "calculation_operand_not_in_evidence"
                operands[key] = value
            result = evaluate(calc.get("expression"), operands)
            with localcontext() as ctx:
                ctx.prec = 50
                rounded = result.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
            # Never trust or render a provider-supplied result. Legacy result
            # fields are ignored; only the validated expression determines output.
            answer = answer.replace(marker, format(rounded, f".{places}f"))
        except (ValueError, SyntaxError, DecimalException, RecursionError):
            return None, "invalid_calculations"
    if "{{" in answer or "}}" in answer:
        return None, "invalid_calculations"
    if directional_contradiction(answer):
        return None, "directional_contradiction"
    return answer, "accepted"


def calculation_repair_issues(payload, sources):
    """Bounded diagnostics only; never change operands or trust an unverified quote."""
    issues = []
    if not isinstance(payload, dict) or not isinstance(payload.get("calculations"), list):
        return [{"code": "missing_calculations_array"}]
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        return [{"code": "invalid_evidence_array"}]
    verified_numbers = {}
    for ei, entry in enumerate(evidence[:48]):
        if not isinstance(entry, dict):
            continue
        quote, label = entry.get("quote"), entry.get("source_id")
        if (
            isinstance(quote, str)
            and quote.strip()
            and isinstance(label, str)
            and label in sources
            and " ".join(quote.split()) in " ".join(sources[label].chunk.text.split())
        ):
            verified_numbers[ei] = _quote_numbers(quote)
    for ci, calc in enumerate(payload["calculations"][:4], 1):
        if not isinstance(calc, dict):
            issues.append({"calculation": ci, "code": "invalid_calculation_object"})
            continue
        entries = calc.get("operands", [])
        if not isinstance(entries, list):
            issues.append({"calculation": ci, "code": "invalid_operands_array"})
            continue
        names = set()
        for oi, operand in enumerate(entries[:12], 1):
            at = {"calculation": ci, "operand": oi}
            if not isinstance(operand, dict):
                issues.append({**at, "code": "invalid_operand_object"})
                continue
            name = operand.get("name")
            if not isinstance(name, str) or not NAME.fullmatch(name) or name in names:
                issues.append({**at, "code": "invalid_or_duplicate_operand_name"})
            else:
                names.add(name)
            try:
                value = _decimal(operand.get("value"))
            except (ValueError, DecimalException):
                issues.append({**at, "code": "invalid_decimal_string"})
                continue
            index = operand.get("evidence_index")
            matches = [ei for ei, numbers in verified_numbers.items() if value in numbers]
            signed_matches = [ei for ei, numbers in verified_numbers.items() if -value in numbers]
            if index not in matches and (matches or signed_matches):
                issues.append(
                    {
                        **at,
                        "code": "check_operand_evidence_link",
                        "matching_evidence_indices": matches,
                        "opposite_sign_evidence_indices": signed_matches,
                    }
                )
            if type(index) is not int or not 0 <= index < len(evidence):
                issues.append({**at, "code": "invalid_evidence_index"})
                continue
            entry = evidence[index]
            if not isinstance(entry, dict):
                continue
            quote, label = entry.get("quote"), entry.get("source_id")
            if (
                not isinstance(quote, str)
                or not quote.strip()
                or not isinstance(label, str)
                or label not in sources
                or " ".join(quote.split()) not in " ".join(sources[label].chunk.text.split())
            ):
                continue
            numbers = _quote_numbers(quote)
            if value not in numbers:
                if -value in numbers:
                    issues.append(
                        {
                            **at,
                            "code": "signed_operand_mismatch",
                            "evidence_index": index,
                            "quoted_signed_value": str(-value),
                        }
                    )
                else:
                    issues.append(
                        {**at, "code": "operand_absent_from_quote", "evidence_index": index}
                    )
        expression = calc.get("expression")
        if not isinstance(expression, str) or not 0 < len(expression) <= 200:
            issues.append({"calculation": ci, "code": "invalid_expression"})
            continue
        try:
            nodes = list(ast.walk(ast.parse(expression, mode="eval")))
        except (SyntaxError, ValueError, RecursionError):
            issues.append({"calculation": ci, "code": "invalid_expression_syntax"})
            continue
        if len(nodes) > 80:
            issues.append({"calculation": ci, "code": "expression_too_large"})
            continue
        if any(
            isinstance(n, ast.Constant) and (type(n.value) is not int or n.value not in CONSTANTS)
            for n in nodes
        ):
            issues.append({"calculation": ci, "code": "financial_literals_in_expression"})
        used = {n.id for n in nodes if isinstance(n, ast.Name)}
        if used != names or not used:
            issues.append({"calculation": ci, "code": "expression_operand_names_mismatch"})
    return issues[:64]


CALCULATION_PROMPT = (
    '\nCALCULATION PROTOCOL: Add "calculations":[] for a direct lookup or qualitative answer. '
    "For EVERY derived number, provide a calculation and put its {{id}} placeholder in the "
    "answer instead of writing the result yourself. Use placeholders for intermediate results "
    "too, or omit intermediates. Do not omit calculations for ratios, arithmetic comparisons "
    "or unit conversions. Each calculation has id, expression, "
    "decimal_places (0-8), and operands. Each operand has name, value (decimal string without "
    "commas), evidence_index (zero-based index into evidence), metric, period and unit. "
    "Set each evidence_index from the FINAL evidence array order, not the source-label "
    "number. Recheck every link after reordering quotes. A capex operand must point to "
    "its capex quote, not a revenue quote. Each calculation is independent: inline "
    "arithmetic over quoted inputs instead of citing computed intermediate values. "
    "Quote every input including sign and intervening columns; parentheses denote negatives. "
    "Keep that negative sign in the operand. To report a positive expenditure magnitude, "
    "negate the signed outflow in the expression. Free cash flow is operating cash flow "
    "plus a signed capex outflow. Do not flip signs on balances or losses. "
    "For a ratio using the magnitude of dividends paid or an expense shown as negative, "
    "record the negative quoted operand and negate it in the expression, only if the "
    "requested definition requires that magnitude. Operand names must start with a "
    "ASCII letter, not a year: use rate_new rather than 2022_rate. Names are case-sensitive "
    "and at most 20 letters, digits or underscores. Use concise names consistently. "
    "Operand values must match their quoted numeric tokens exactly, before unit conversion. "
    "Use only operand names, parentheses, + - * / in expressions. Allowed literal constants "
    "are 1,2,3,4,12,100,360,365,366,1000,1000000,1000000000 for averages, percent/day factors "
    "and scaling; all financial values must be cited operands. Use every declared operand. "
    "Use at most four calculations and twelve operands each. Do not supply a result: "
    "the application computes it, rounds half up and replaces the placeholder. "
    'Example calculation shape: {"id":"growth","expression":"(new-old)/old*100",'
    '"decimal_places":1,"operands":['
    '{"name":"new","value":"100","evidence_index":0,"metric":"revenue",'
    '"period":"current year","unit":"USD millions"},'
    '{"name":"old","value":"80","evidence_index":1,"metric":"revenue",'
    '"period":"prior year","unit":"USD millions"}]}. '
    'Example answer template: "Revenue increased by {{growth}}%." '
    "The example values are schema illustrations only, never evidence for the question."
)
