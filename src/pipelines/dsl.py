from dataclasses import dataclass, field


RELATION_TYPES = {"association", "composition", "aggregation", "inheritance"}


@dataclass
class UmlClass:
    name: str
    attributes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class UmlRelation:
    source: str
    relation_type: str
    target: str


@dataclass
class UmlModel:
    classes: list[UmlClass]
    relations: list[UmlRelation]
    validation_errors: list[str]


def to_class_name(term: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in term)
    parts = [part for part in cleaned.split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Artefato"


def make_method_name(term: str) -> str:
    parts = [part for part in term.replace("_", " ").split() if part]
    if not parts:
        return "operation"
    return parts[0].lower() + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def build_paper_style_dsl(classes: list[UmlClass], relations: list[UmlRelation]) -> str:
    lines: list[str] = []
    for uml_class in classes:
        lines.append(f"Class {uml_class.name}:")
        if uml_class.attributes:
            lines.append(f"Attributes: {', '.join(uml_class.attributes)}")
        if uml_class.methods:
            lines.append(f"Methods: {', '.join(uml_class.methods)}")
    for relation in relations:
        lines.append(f"Relation: {relation.source} {relation.relation_type} {relation.target}")
    return "\n".join(lines)


def parse_paper_style_dsl(dsl: str) -> UmlModel:
    classes: list[UmlClass] = []
    relations: list[UmlRelation] = []
    errors: list[str] = []
    current: UmlClass | None = None

    for number, raw_line in enumerate((dsl or "").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Class ") and line.endswith(":"):
            name = line.removeprefix("Class ").removesuffix(":").strip()
            if not name:
                errors.append(f"line {number}: empty class name")
                current = None
                continue
            current = UmlClass(name=name)
            classes.append(current)
        elif line.startswith("Attributes:"):
            if current is None:
                errors.append(f"line {number}: attributes without class")
                continue
            current.attributes.extend(_split_list(line.removeprefix("Attributes:")))
        elif line.startswith("Methods:"):
            if current is None:
                errors.append(f"line {number}: methods without class")
                continue
            current.methods.extend(_split_list(line.removeprefix("Methods:")))
        elif line.startswith("Relation:"):
            parts = line.removeprefix("Relation:").strip().split()
            if len(parts) != 3 or parts[1] not in RELATION_TYPES:
                errors.append(f"line {number}: invalid relation")
                continue
            relations.append(UmlRelation(source=parts[0], relation_type=parts[1], target=parts[2]))
        else:
            errors.append(f"line {number}: unknown DSL statement")

    class_names = {uml_class.name for uml_class in classes}
    for relation in relations:
        if relation.source not in class_names or relation.target not in class_names:
            errors.append(f"relation references undefined class: {relation.source} -> {relation.target}")
    return UmlModel(classes=classes, relations=relations, validation_errors=errors)


def dsl_syntax_error_count(dsl: str) -> int:
    return len(parse_paper_style_dsl(dsl).validation_errors)


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]

