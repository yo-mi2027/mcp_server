from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, Union

try:
    from pydantic import BaseModel
except ModuleNotFoundError as exc:  # pragma: no cover - indicates missing deps
    raise RuntimeError(
        "pydantic is not installed. Activate your virtualenv and run "
        "`pip install -r requirements.txt` before starting manual-tools."
    ) from exc

try:  # PyYAML is optional at import time so we can emit a clearer error later.
    import yaml
except ModuleNotFoundError:  # pragma: no cover - only hit in missing dependency envs
    yaml = None  # type: ignore[assignment]

class OverridesConfig(BaseModel):
    enabled: bool = False

class TocConfig(BaseModel):
    source: str = "json_only"
    path_pattern: str = "manuals/{manual}/00_目次.json"
    hierarchical_default: bool = False
    use_loc: bool = False
    overrides: OverridesConfig = OverridesConfig()

class LoggingConfig(BaseModel):
    level: str = "INFO"

class Settings(BaseModel):
    manuals_root: str = "manuals"
    toc: TocConfig = TocConfig()
    validation_mode: str = "relaxed"  # relaxed / strict
    logging: LoggingConfig = LoggingConfig()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def _resolve_with_base(base: Path, target: Union[str, os.PathLike[str]]) -> Path:
    candidate = Path(target)
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()

def load_settings(path: Union[str, os.PathLike[str], None] = None) -> Settings:
    config_path = (
        _resolve_with_base(PROJECT_ROOT, path)
        if path
        else (PROJECT_ROOT / "config.yaml").resolve()
    )

    data: Dict[str, Any] = {}
    if config_path.exists():
        if yaml is None:
            raise RuntimeError(
                "config.yaml is present but PyYAML is not installed. "
                "Activate your virtualenv and run `pip install -r requirements.txt`."
            )
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    # 環境変数の簡易オーバーライド（必要最小限）
    mr = os.getenv("MANUALS_ROOT")
    if mr:
        data.setdefault("manuals_root", mr)

    settings = Settings(**data)
    config_dir = config_path.parent

    manuals_root_path = Path(settings.manuals_root)
    if not manuals_root_path.is_absolute():
        manuals_root_path = (config_dir / manuals_root_path).resolve()

    path_pattern = settings.toc.path_pattern
    pattern_path = Path(path_pattern)
    if not pattern_path.is_absolute():
        path_pattern = str((config_dir / pattern_path).resolve())

    return settings.model_copy(
        update={
            "manuals_root": str(manuals_root_path),
            "toc": settings.toc.model_copy(update={"path_pattern": path_pattern}),
        }
    )
