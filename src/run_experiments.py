import logging
import random
import time
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> bool:
        return False

from src.evaluators.code_eval import contains_expected_fragments, count_syntax_errors
from src.evaluators.dsl_eval import dsl_match_rate, paper_dsl_syntax_validity
from src.metrics.classification import precision_recall_f1, split_terms
from src.pipelines.model_clients import build_client
from src.pipelines.variants import (
    apply_business_rule_change,
    apply_business_rule_change_with_model,
    run_full_pipeline,
    run_multilayer_dsl_pipeline,
    run_no_dsl_pipeline,
)
from src.utils.config import ROOT, ensure_dirs, load_yaml
from src.utils.logging import configure_logging
from src.utils.plotting import write_figures


LOGGER = logging.getLogger(__name__)


REAL_PROVIDERS = {"openai", "ollama", "openai_compatible"}


def _estimate_cost(model: dict, input_tokens: int, output_tokens: int) -> float:
    in_cost = float(model.get("cost_per_1k_input_tokens_usd") or 0)
    out_cost = float(model.get("cost_per_1k_output_tokens_usd") or 0)
    return (input_tokens / 1000 * in_cost) + (output_tokens / 1000 * out_cost)


def _coverage(expected: set[str], artifact: str) -> float:
    if not expected:
        return 0.0
    artifact_lower = (artifact or "").lower()
    hits = sum(1 for term in expected if term in artifact_lower)
    return hits / len(expected)


def _strip_python_comments(code: str) -> str:
    lines = []
    for line in (code or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def _evaluate(row: dict, gold: dict, output, elapsed: float, model: dict, experiment: str) -> dict:
    provider = model.get("provider", "")
    result_status = "empirical_model_run" if provider in REAL_PROVIDERS else "baseline_or_mock_only"
    expected_entities = split_terms(gold.get("expected_entities", ""))
    predicted_entities = split_terms(output.extracted_entities)
    precision, recall, f1 = precision_recall_f1(expected_entities, predicted_entities)
    dsl_expected = gold.get("expected_requirements_dsl", "")
    dsl_text = output.requirements_dsl or output.design_dsl
    paper_style_dsl = output.design_dsl if experiment == "C_multilayer_dsl" else output.requirements_dsl
    dsl_rate = dsl_match_rate(dsl_text, dsl_expected)
    dsl_syntax_validity = paper_dsl_syntax_validity(paper_style_dsl) if experiment != "B_no_dsl" else 0.0
    code_rate = contains_expected_fragments(output.code, gold.get("expected_code_contains", ""))
    syntax_errors = count_syntax_errors(output.code)
    semantic_expected = split_terms(gold.get("expected_semantic_rules", ""))
    semantic_coverage = _coverage(semantic_expected, output.code + "\n" + dsl_text)
    semantic_errors = 0 if semantic_coverage >= 0.5 else 1
    inconsistencies = 0
    if experiment == "D_business_rule_change":
        changed_rule_terms = split_terms(row.get("changed_business_rule", ""))
        code_without_comments = _strip_python_comments(output.code)
        changed_rule_coverage = _coverage(changed_rule_terms, code_without_comments)
        inconsistencies = 0 if changed_rule_coverage >= 0.5 else 1

    stage_failures = sum(
        [
            1 if f1 < 0.5 else 0,
            1 if experiment != "B_no_dsl" and dsl_syntax_validity < 1.0 else 0,
            1 if code_rate < 0.3 else 0,
            syntax_errors,
            inconsistencies,
        ]
    )
    end_to_end = 1 if stage_failures == 0 else 0
    input_tokens = len(str(row.get("cim_text", "")).split())
    output_tokens = len(output.code.split()) + len(dsl_text.split())

    return {
        "case_id": row["case_id"],
        "difficulty": row.get("difficulty", ""),
        "model": model["name"],
        "provider": provider,
        "result_status": result_status,
        "experiment": experiment,
        "input_cim": row.get("cim_text", ""),
        "generated_entities": output.extracted_entities,
        "generated_requirements_dsl": output.requirements_dsl,
        "generated_design_dsl": output.design_dsl,
        "generated_code": output.code,
        "entity_precision": precision,
        "entity_recall": recall,
        "entity_f1": f1,
        "dsl_correct_rate": dsl_rate,
        "dsl_syntax_validity": dsl_syntax_validity,
        "code_correct_rate": code_rate,
        "syntax_errors": syntax_errors,
        "semantic_errors": semantic_errors,
        "semantic_rule_coverage": semantic_coverage,
        "business_rule_inconsistencies": inconsistencies,
        "execution_time_seconds": elapsed,
        "estimated_cost_usd": _estimate_cost(model, input_tokens, output_tokens),
        "end_to_end_success": end_to_end,
        "stage_failure_count": stage_failures,
        "notes": output.notes,
    }


def main() -> None:
    load_dotenv()
    configure_logging()
    ensure_dirs()

    config = load_yaml(ROOT / "config" / "experiment_config.yaml")
    runtime_config = config.get("runtime", {})
    random.seed(config.get("seed", 42))

    input_cases = pd.read_csv(ROOT / "data" / "input_cases_template.csv").fillna("")
    max_cases = int(runtime_config.get("max_cases") or 0)
    if max_cases > 0:
        input_cases = input_cases.head(max_cases)

    gold_df = pd.read_csv(ROOT / "data" / "gold_standard_template.csv").fillna("")
    gold_by_case = {row["case_id"]: row for row in gold_df.to_dict(orient="records")}
    models = [m for m in load_yaml(ROOT / "config" / "models.yaml").get("models", []) if m.get("enabled")]

    configured_experiments = config.get("experiments", {})
    all_experiment_fns = {
        "A_full_pipeline": run_full_pipeline,
        "B_no_dsl": run_no_dsl_pipeline,
        "C_multilayer_dsl": run_multilayer_dsl_pipeline,
        "E_generalization": run_full_pipeline,
    }
    experiment_fns = {
        name: fn
        for name, fn in all_experiment_fns.items()
        if configured_experiments.get(name, True)
    }

    run_business_rule_change = configured_experiments.get("D_business_rule_change", True)
    skip_business_rule_model_update = bool(runtime_config.get("skip_business_rule_model_update", False))
    write_partial_results = bool(runtime_config.get("write_partial_results", True))
    results_dir = ROOT / "results"

    rows = []
    for model in models:
        client = build_client(model)
        for case in input_cases.to_dict(orient="records"):
            gold = gold_by_case.get(case["case_id"], {})

            for experiment, fn in experiment_fns.items():
                start = time.perf_counter()
                try:
                    output = fn(case.get("cim_text", ""), client)
                except Exception as exc:
                    LOGGER.exception("Falha no experimento %s caso %s", experiment, case["case_id"])
                    output = run_no_dsl_pipeline(f"ERRO: {exc}", client)
                    output.notes += f" | exception={exc}"

                elapsed = time.perf_counter() - start
                rows.append(_evaluate(case, gold, output, elapsed, model, experiment))

            if run_business_rule_change:
                start = time.perf_counter()
                base_output = run_full_pipeline(case.get("cim_text", ""), client)

                if skip_business_rule_model_update:
                    changed = apply_business_rule_change(
                        base_output,
                        case.get("changed_business_rule", ""),
                        case.get("user_modification", ""),
                    )
                    changed.notes += " | skipped_model_update_fast_mode"
                else:
                    changed = apply_business_rule_change_with_model(
                        base_output,
                        case.get("changed_business_rule", ""),
                        case.get("user_modification", ""),
                        client,
                    )

                elapsed = time.perf_counter() - start
                rows.append(_evaluate(case, gold, changed, elapsed, model, "D_business_rule_change"))

            if write_partial_results:
                pd.DataFrame(rows).to_csv(
                    results_dir / "raw_results_partial.csv",
                    index=False,
                    encoding="utf-8",
                )

    raw = pd.DataFrame(rows)
    raw.to_csv(results_dir / "raw_results.csv", index=False, encoding="utf-8")

    summary = (
        raw.groupby(["model", "experiment"], as_index=False)
        .agg(
            entity_precision=("entity_precision", "mean"),
            entity_recall=("entity_recall", "mean"),
            entity_f1=("entity_f1", "mean"),
            dsl_correct_rate=("dsl_correct_rate", "mean"),
            dsl_syntax_validity=("dsl_syntax_validity", "mean"),
            code_correct_rate=("code_correct_rate", "mean"),
            syntax_errors=("syntax_errors", "mean"),
            semantic_errors=("semantic_errors", "mean"),
            semantic_rule_coverage=("semantic_rule_coverage", "mean"),
            business_rule_inconsistencies=("business_rule_inconsistencies", "mean"),
            execution_time_seconds=("execution_time_seconds", "mean"),
            estimated_cost_usd=("estimated_cost_usd", "sum"),
            end_to_end_success=("end_to_end_success", "mean"),
            stage_failure_count=("stage_failure_count", "mean"),
        )
    )
    summary["model_experiment"] = summary["model"] + " / " + summary["experiment"]
    summary.to_csv(results_dir / "summary_metrics.csv", index=False, encoding="utf-8")

    validity_notes = pd.DataFrame(
        [
            {
                "scope": "default_run",
                "warning": "Se apenas providers local/mock estiverem habilitados, os resultados servem para validar o pipeline, nao para conclusao empirica.",
                "action": "Habilite pelo menos um provider real em config/models.yaml: openai, ollama ou openai_compatible.",
            },
            {
                "scope": "bert_paper_reference",
                "warning": "bert_paper_reference e mock_llm nao sao BERT/LLM reais; sao placeholders deterministivos.",
                "action": "Nao use esses resultados como comparacao com o paper na apresentacao.",
            },
            {
                "scope": "business_rule_change",
                "warning": "A metrica agora ignora comentarios Python; mencionar a regra em comentario nao conta como consistencia.",
                "action": "Verifique business_rule_inconsistencies e semantic_rule_coverage.",
            },
            {
                "scope": "fast_mode",
                "warning": "skip_business_rule_model_update=true reduz chamadas de API e acelera a execucao, mas nao mede a capacidade do modelo de reconciliar mudancas de regra.",
                "action": "Use esse modo para obter resultados rapidos; rode skip_business_rule_model_update=false apenas se houver tempo.",
            },
        ]
    )
    validity_notes.to_csv(results_dir / "validity_warnings.csv", index=False, encoding="utf-8")

    error_analysis = raw[raw["stage_failure_count"] > 0].copy()
    error_analysis["error_category"] = error_analysis.apply(
        lambda row: "syntax"
        if row["syntax_errors"]
        else "business_rule"
        if row["business_rule_inconsistencies"]
        else "quality",
        axis=1,
    )
    error_analysis.to_csv(results_dir / "error_analysis.csv", index=False, encoding="utf-8")

    ablation = raw[raw["experiment"].isin(["A_full_pipeline", "B_no_dsl", "C_multilayer_dsl"])]
    ablation.to_csv(results_dir / "ablation_results.csv", index=False, encoding="utf-8")

    model_comparison = raw.groupby("model", as_index=False).agg(
        entity_f1=("entity_f1", "mean"),
        dsl_syntax_validity=("dsl_syntax_validity", "mean"),
        code_correct_rate=("code_correct_rate", "mean"),
        business_rule_inconsistencies=("business_rule_inconsistencies", "mean"),
        end_to_end_success=("end_to_end_success", "mean"),
        stage_failure_count=("stage_failure_count", "mean"),
    )
    model_comparison.to_csv(results_dir / "model_comparison.csv", index=False, encoding="utf-8")

    write_figures(raw, summary, results_dir / "figures")
    LOGGER.info("Resultados gerados em %s", results_dir)

if __name__ == "__main__":
    main()
