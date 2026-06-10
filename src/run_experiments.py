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
    run_full_pipeline,
    run_multilayer_dsl_pipeline,
    run_no_dsl_pipeline,
)
from src.utils.config import ROOT, ensure_dirs, load_yaml
from src.utils.logging import configure_logging
from src.utils.plotting import write_figures


LOGGER = logging.getLogger(__name__)


def _estimate_cost(model: dict, input_tokens: int, output_tokens: int) -> float:
    in_cost = float(model.get("cost_per_1k_input_tokens_usd") or 0)
    out_cost = float(model.get("cost_per_1k_output_tokens_usd") or 0)
    return (input_tokens / 1000 * in_cost) + (output_tokens / 1000 * out_cost)


def _evaluate(row: dict, gold: dict, output, elapsed: float, model: dict, experiment: str) -> dict:
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
    semantic_errors = 0 if semantic_expected else 1
    inconsistencies = 0
    if experiment == "D_business_rule_change":
        changed_rule = row.get("changed_business_rule", "")
        inconsistencies = 0 if changed_rule and changed_rule in output.code else 1

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
    random.seed(config.get("seed", 42))

    input_cases = pd.read_csv(ROOT / "data" / "input_cases_template.csv").fillna("")
    gold_df = pd.read_csv(ROOT / "data" / "gold_standard_template.csv").fillna("")
    gold_by_case = {row["case_id"]: row for row in gold_df.to_dict(orient="records")}
    models = [m for m in load_yaml(ROOT / "config" / "models.yaml").get("models", []) if m.get("enabled")]

    experiment_fns = {
        "A_full_pipeline": run_full_pipeline,
        "B_no_dsl": run_no_dsl_pipeline,
        "C_multilayer_dsl": run_multilayer_dsl_pipeline,
        "E_generalization": run_full_pipeline,
        "F_model_comparison": run_full_pipeline,
    }

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

            start = time.perf_counter()
            base_output = run_full_pipeline(case.get("cim_text", ""), client)
            changed = apply_business_rule_change(
                base_output,
                case.get("changed_business_rule", ""),
                case.get("user_modification", ""),
            )
            elapsed = time.perf_counter() - start
            rows.append(_evaluate(case, gold, changed, elapsed, model, "D_business_rule_change"))

    raw = pd.DataFrame(rows)
    results_dir = ROOT / "results"
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
            business_rule_inconsistencies=("business_rule_inconsistencies", "mean"),
            execution_time_seconds=("execution_time_seconds", "mean"),
            estimated_cost_usd=("estimated_cost_usd", "sum"),
            end_to_end_success=("end_to_end_success", "mean"),
            stage_failure_count=("stage_failure_count", "mean"),
        )
    )
    summary["model_experiment"] = summary["model"] + " / " + summary["experiment"]
    summary.to_csv(results_dir / "summary_metrics.csv", index=False, encoding="utf-8")

    error_analysis = raw[raw["stage_failure_count"] > 0].copy()
    error_analysis["error_category"] = error_analysis.apply(
        lambda row: "syntax" if row["syntax_errors"] else "business_rule" if row["business_rule_inconsistencies"] else "quality",
        axis=1,
    )
    error_analysis.to_csv(results_dir / "error_analysis.csv", index=False, encoding="utf-8")

    ablation = raw[raw["experiment"].isin(["A_full_pipeline", "B_no_dsl", "C_multilayer_dsl"])]
    ablation.to_csv(results_dir / "ablation_results.csv", index=False, encoding="utf-8")

    write_figures(raw, summary, results_dir / "figures")
    LOGGER.info("Resultados gerados em %s", results_dir)


if __name__ == "__main__":
    main()
