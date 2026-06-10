from pathlib import Path
import struct
import zlib

import pandas as pd


def write_figures(raw: pd.DataFrame, summary: pd.DataFrame, out_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        _write_fallback_figures(raw, summary, out_dir)
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    title_suffix = ""
    if "result_status" in raw.columns and not (raw["result_status"] == "empirical_model_run").any():
        title_suffix = " (baseline apenas)"

    def bar(data, x, y, title, filename):
        plt.figure(figsize=(9, 5))
        data.plot(kind="bar", x=x, y=y, legend=False)
        plt.title(title + title_suffix)
        plt.ylim(bottom=0)
        plt.tight_layout()
        plt.savefig(out_dir / filename)
        plt.close()

    if not summary.empty:
        bar(summary, "model_experiment", "entity_f1", "F1-score por modelo/experimento", "f1_by_model.png")
        bar(summary, "model_experiment", "end_to_end_success", "Sucesso end-to-end", "end_to_end_success.png")

    if not raw.empty:
        errors = raw.groupby("experiment", as_index=False)[["syntax_errors", "semantic_errors"]].sum()
        errors["total_errors"] = errors["syntax_errors"] + errors["semantic_errors"]
        bar(errors, "experiment", "total_errors", "Erros por etapa do pipeline", "errors_by_stage.png")

        ablation = raw[raw["experiment"].isin(["A_full_pipeline", "B_no_dsl", "C_multilayer_dsl"])]
        if not ablation.empty:
            ablation_summary = ablation.groupby("experiment", as_index=False)["end_to_end_success"].mean()
            bar(ablation_summary, "experiment", "end_to_end_success", "Impacto da remocao/uso da DSL", "dsl_ablation.png")

        changes = raw[raw["experiment"] == "D_business_rule_change"]
        if not changes.empty:
            change_summary = changes.groupby("model", as_index=False)["business_rule_inconsistencies"].mean()
            bar(change_summary, "model", "business_rule_inconsistencies", "Impacto da mudanca de regra", "business_rule_change_impact.png")


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def _write_simple_png(path: Path, values: list[float]) -> None:
    width, height = 900, 500
    pixels = bytearray([255, 255, 255] * width * height)
    if not values:
        values = [0.0]
    max_value = max(max(values), 1.0)
    bar_width = max(12, int((width - 120) / max(len(values), 1)))
    for idx, value in enumerate(values):
        x0 = 60 + idx * bar_width
        x1 = min(x0 + int(bar_width * 0.7), width - 40)
        bar_height = int((height - 120) * (value / max_value))
        y0 = height - 60 - bar_height
        y1 = height - 60
        color = (42, 96, 151)
        for y in range(max(0, y0), min(height, y1)):
            for x in range(max(0, x0), min(width, x1)):
                pos = (y * width + x) * 3
                pixels[pos : pos + 3] = bytes(color)

    rows = []
    stride = width * 3
    for y in range(height):
        rows.append(b"\x00" + bytes(pixels[y * stride : (y + 1) * stride]))
    raw = b"".join(rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def _write_fallback_figures(raw: pd.DataFrame, summary: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if summary.empty:
        summary_values = [0.0]
    else:
        summary_values = summary["entity_f1"].fillna(0).tolist()
    _write_simple_png(out_dir / "f1_by_model.png", summary_values)
    _write_simple_png(out_dir / "end_to_end_success.png", summary.get("end_to_end_success", pd.Series([0])).fillna(0).tolist())

    if raw.empty:
        _write_simple_png(out_dir / "errors_by_stage.png", [0.0])
        _write_simple_png(out_dir / "dsl_ablation.png", [0.0])
        _write_simple_png(out_dir / "business_rule_change_impact.png", [0.0])
        return

    errors = raw.groupby("experiment")[["syntax_errors", "semantic_errors"]].sum().sum(axis=1).tolist()
    _write_simple_png(out_dir / "errors_by_stage.png", errors)
    ablation = raw[raw["experiment"].isin(["A_full_pipeline", "B_no_dsl", "C_multilayer_dsl"])]
    _write_simple_png(out_dir / "dsl_ablation.png", ablation.groupby("experiment")["end_to_end_success"].mean().tolist())
    changes = raw[raw["experiment"] == "D_business_rule_change"]
    _write_simple_png(out_dir / "business_rule_change_impact.png", changes.groupby("model")["business_rule_inconsistencies"].mean().tolist())
