import re


STOPWORDS = {
    "sistema", "deve", "com", "para", "quando", "usuario", "usuário",
    "pode", "ser", "uma", "um", "the", "and", "or", "nao", "não",
    "each", "can", "and", "their", "only", "is", "to", "of", "a", "an",
    "has", "have", "includes", "multiple", "several", "also",
}


def extract_terms(text: str) -> list[str]:
    terms = []
    for token in re.findall(r"[A-Za-zÀ-ÿ_][A-Za-zÀ-ÿ0-9_]+", text or ""):
        normalized = token.lower()
        if normalized not in STOPWORDS and len(normalized) > 2 and normalized not in terms:
            terms.append(normalized)
    return terms


def make_entity_name(term: str) -> str:
    return "".join(part.capitalize() for part in term.split("_"))


def infer_relation_type(text: str) -> str:
    lowered = (text or "").lower()
    if any(word in lowered for word in ["contains", "contains multiple", "composed", "consists", "contém"]):
        return "composition"
    if any(word in lowered for word in ["inherits", "extends", "is a", "subclass"]):
        return "inheritance"
    if any(word in lowered for word in ["aggregates", "group", "collection"]):
        return "aggregation"
    return "association"
