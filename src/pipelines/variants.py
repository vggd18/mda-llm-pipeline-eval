from dataclasses import dataclass

from src.pipelines.dsl import (
    UmlClass,
    UmlRelation,
    build_paper_style_dsl,
    dsl_syntax_error_count,
    make_method_name,
    parse_paper_style_dsl,
    to_class_name,
)
from src.pipelines.heuristics import extract_terms, infer_relation_type
from src.pipelines.model_clients import BaseModelClient

CLASS_HINTS = [
    "computer", "motherboard", "processor", "memory", "storage device", "peripheral device",
    "document", "section", "paragraph", "figure", "reference", "author", "editor", "reviewer",
    "library", "book", "member", "loan", "penalty",
    "order", "item", "customer", "message",
    "car", "sensor event", "alert", "operator", "incident",
]

METHOD_HINTS = [
    "start", "shut down", "report status", "write", "review", "validate", "manage",
    "borrow", "return", "pay", "confirm", "receive", "get speed", "trigger",
    "acknowledge", "escalate",
]


def _extract_text_block(text: str) -> str:
    if "```" not in text:
        return text.strip()
    parts = text.split("```")
    for part in parts:
        cleaned = part.strip()
        if cleaned.startswith("text"):
            cleaned = cleaned.removeprefix("text").strip()
        if cleaned.startswith("python"):
            cleaned = cleaned.removeprefix("python").strip()
        if cleaned:
            return cleaned
    return text.strip()


def _generate_dsl_with_model(cim_text: str, model: BaseModelClient) -> tuple[str, str]:
    prompt = f"""Generate only a UML DSL block using exactly this grammar:
Class Name:
Attributes: attr1, attr2
Methods: methodName
Relation: Source association Target

Allowed relations: association, composition, aggregation, inheritance.
Do not explain. Do not use Markdown.

Specification:
{cim_text}
"""
    response = model.generate(prompt)
    return _extract_text_block(response.text), response.text


def _generate_code_with_model(cim_text: str, model: BaseModelClient) -> tuple[str, str]:
    prompt = f"""Generate only syntactically valid Python code from this specification.
Each domain concept should become a class.
Use __init__ for attributes and empty methods with pass.
Do not explain. Do not use Markdown.

Specification:
{cim_text}
"""
    response = model.generate(prompt)
    return _extract_text_block(response.text), response.text


@dataclass
class PipelineOutput:
    extracted_entities: str
    requirements_dsl: str
    design_dsl: str
    code: str
    notes: str


def _code_from_terms(class_name: str, terms: list[str], rule: str = "") -> str:
    fields = terms[:5] or ["campo"]
    assignments = "\n".join(f"        self.{field} = {field}" for field in fields)
    args = ", ".join(fields)
    rule_comment = f"    # Regra de negocio: {rule}\n" if rule else ""
    return f"class {class_name}:\n{rule_comment}    def __init__(self, {args}):\n{assignments}\n"


def _code_from_dsl(dsl: str, rule: str = "") -> str:
    model = parse_paper_style_dsl(dsl)
    blocks: list[str] = []
    relation_attrs: dict[str, list[str]] = {}
    for relation in model.relations:
        relation_attrs.setdefault(relation.source, []).append(relation.target[:1].lower() + relation.target[1:])

    for uml_class in model.classes:
        attributes = list(dict.fromkeys(uml_class.attributes + relation_attrs.get(uml_class.name, [])))
        init_args = ", ".join(attributes)
        signature = f"    def __init__(self, {init_args}):" if init_args else "    def __init__(self):"
        assignments = [f"        self.{attribute} = {attribute}" for attribute in attributes] or ["        pass"]
        methods = [f"\n    def {make_method_name(method)}(self):\n        pass" for method in uml_class.methods]
        parent = ""
        inheritance = next((rel for rel in model.relations if rel.source == uml_class.name and rel.relation_type == "inheritance"), None)
        if inheritance:
            parent = f"({inheritance.target})"
        rule_comment = f"    # Regra de negocio: {rule}\n" if rule else ""
        blocks.append(f"class {uml_class.name}{parent}:\n{rule_comment}{signature}\n" + "\n".join(assignments) + "".join(methods) + "\n")
    return "\n".join(blocks) if blocks else _code_from_terms("Artefato", [], rule)


def _model_from_terms(cim_text: str) -> tuple[list[UmlClass], list[UmlRelation], list[str]]:
    terms = extract_terms(cim_text)
    lowered = (cim_text or "").lower()
    class_terms = [hint for hint in CLASS_HINTS if hint in lowered]
    if not class_terms:
        class_terms = terms[:3] or ["artefato"]
    classes = [UmlClass(name=to_class_name(term)) for term in class_terms[:5]]
    if classes:
        used_class_words = {word for term in class_terms for word in term.split()}
        classes[0].attributes = [term for term in terms if term not in used_class_words][:5]
        classes[0].methods = [make_method_name(hint) for hint in METHOD_HINTS if hint in lowered][:4]
    relations = []
    if len(classes) >= 2:
        relations.append(UmlRelation(classes[0].name, infer_relation_type(cim_text), classes[1].name))
    if len(classes) >= 3:
        relations.append(UmlRelation(classes[0].name, "association", classes[2].name))
    return classes, relations, terms


def run_full_pipeline(cim_text: str, model: BaseModelClient) -> PipelineOutput:
    classes, relations, terms = _model_from_terms(cim_text)
    dsl = build_paper_style_dsl(classes, relations)
    model_hint = "heuristic_dsl"
    if model.uses_real_generation:
        candidate_dsl, model_hint = _generate_dsl_with_model(cim_text, model)
        if candidate_dsl and dsl_syntax_error_count(candidate_dsl) == 0:
            dsl = candidate_dsl
        else:
            model_hint += " | fallback_to_heuristic_dsl"
    code = _code_from_dsl(dsl, "Pipeline aproximado inspirado no artigo; codigo esqueleto Python.")
    return PipelineOutput(";".join(terms), dsl, "", code, model_hint)


def run_no_dsl_pipeline(cim_text: str, model: BaseModelClient) -> PipelineOutput:
    terms = extract_terms(cim_text)
    entity = to_class_name(terms[0]) if terms else "Artefato"
    code = _code_from_terms(entity, terms[1:6], "Gerado diretamente do CIM sem DSL")
    model_hint = "heuristic_direct_code"
    if model.uses_real_generation:
        candidate_code, model_hint = _generate_code_with_model(cim_text, model)
        if candidate_code.startswith("class "):
            code = candidate_code
        else:
            model_hint += " | fallback_to_heuristic_code"
    return PipelineOutput(";".join(terms), "", "", code, model_hint)


def run_multilayer_dsl_pipeline(cim_text: str, model: BaseModelClient) -> PipelineOutput:
    classes, relations, terms = _model_from_terms(cim_text)
    model_hint = "heuristic_multilayer_dsl"
    requirements_dsl = "\n".join([f"RequirementEntity: {uml_class.name}" for uml_class in classes])
    requirements_dsl += "\n# TODO: extensão experimental; o artigo usa uma DSL intermediaria principal, nao multiplas camadas."
    design_dsl = build_paper_style_dsl(classes, relations)
    code = _code_from_dsl(design_dsl, "Derivada de DSL de requisitos e design")
    return PipelineOutput(";".join(terms), requirements_dsl, design_dsl, code, model_hint)


def apply_business_rule_change(output: PipelineOutput, changed_rule: str, user_modification: str) -> PipelineOutput:
    changed_code = output.code + f"\n# Mudanca posterior: {changed_rule}\n# Modificacao do usuario: {user_modification}\n"
    notes = output.notes + " | business_rule_change_applied"
    return PipelineOutput(output.extracted_entities, output.requirements_dsl, output.design_dsl, changed_code, notes)
