def precision_recall_f1(expected: set[str], predicted: set[str]) -> tuple[float, float, float]:
    if not expected and not predicted:
        return 1.0, 1.0, 1.0
    if not expected:
        return 0.0, 0.0, 0.0
    true_positive = len(expected & predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return precision, recall, f1


def split_terms(value: str) -> set[str]:
    if not value or value.startswith("["):
        return set()
    return {item.strip().lower() for item in value.replace(",", ";").split(";") if item.strip()}

