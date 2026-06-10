from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if yaml is None:
        return _load_project_yaml_fallback(path)
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def ensure_dirs() -> None:
    for rel in ["results", "results/figures"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"')
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _load_project_yaml_fallback(path: Path) -> dict[str, Any]:
    # Fallback intentionally supports only the simple config files in this repo.
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.name == "models.yaml":
        models = []
        current = None
        for raw in lines:
            stripped = raw.strip()
            if not stripped or stripped.startswith("#") or stripped == "models:":
                continue
            if stripped.startswith("- "):
                if current:
                    models.append(current)
                current = {}
                key, value = stripped[2:].split(":", 1)
                current[key.strip()] = _parse_scalar(value)
            elif current is not None and ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = _parse_scalar(value)
        if current:
            models.append(current)
        return {"models": models}

    data: dict[str, Any] = {}
    current_section = None
    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if raw.startswith(" ") and current_section and ":" in raw:
            key, value = raw.strip().split(":", 1)
            data[current_section][key.strip()] = _parse_scalar(value)
        elif ":" in raw:
            key, value = raw.split(":", 1)
            key = key.strip()
            if value.strip():
                data[key] = _parse_scalar(value)
                current_section = None
            else:
                data[key] = {}
                current_section = key
    return data
