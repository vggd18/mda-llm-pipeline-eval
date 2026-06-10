def dsl_match_rate(generated: str, expected: str) -> float:
    if not expected or expected.startswith("["):
        return 0.0
    expected_terms = {term.strip().lower() for term in expected.replace(",", " ").split() if term.strip()}
    generated_lower = (generated or "").lower()
    if not expected_terms:
        return 0.0
    hits = sum(1 for term in expected_terms if term in generated_lower)
    return hits / len(expected_terms)


def paper_dsl_syntax_validity(generated: str) -> float:
    if not generated:
        return 0.0
    from src.pipelines.dsl import dsl_syntax_error_count

    return 1.0 if dsl_syntax_error_count(generated) == 0 else 0.0
