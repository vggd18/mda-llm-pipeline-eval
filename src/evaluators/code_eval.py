import ast


def count_syntax_errors(code: str) -> int:
    try:
        ast.parse(code or "")
        return 0
    except SyntaxError:
        return 1


def contains_expected_fragments(code: str, expected_contains: str) -> float:
    fragments = [item.strip() for item in (expected_contains or "").split(";") if item.strip()]
    if not fragments:
        return 0.0
    hits = sum(1 for item in fragments if item in code)
    return hits / len(fragments)

