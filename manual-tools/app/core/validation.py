from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
import re

from app.schemas.toc import TocFile


class ValidationIssue:
    def __init__(self, level: str, msg: str):
        self.level = level  # "WARN" / "ERROR"
        self.msg = msg

    def __repr__(self) -> str:
        return f"[{self.level}] {self.msg}"


# NOTE:
# Previously we enforced a loose style check that section titles should start with
# something like "第1章 ...". This produced a lot of noisy warnings for manuals
# that do not follow that pattern (e.g. compliance manuals, guidelines, etc.).
# That check has been intentionally removed to avoid unnecessary startup noise.
# If you ever want to re-enable it, you can reintroduce a pattern like:
# _CHAPTER_IN_TITLE = re.compile(r"^第\d+章(?:-\d+)?\s+")

_ID_PREFIX = re.compile(r"^(?P<num>\d{2})(?:-(?P<sub>\d+))?")
_ALLOWED_EXTENSIONS = {".txt", ".md", ".json"}


def validate_toc_relaxed(toc: TocFile, manuals_root: Path) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    if not isinstance(toc.toc, list) or len(toc.toc) == 0:
        raise ValueError("toc must be a non-empty array")

    seen_ids = set()
    for e in toc.toc:
        # file format / existence (missing files stay as WARN, do not block startup)
        ext = Path(e.file).suffix.lower()
        if "/" in e.file or "\\" in e.file or ext not in _ALLOWED_EXTENSIONS:
            issues.append(ValidationIssue("WARN", f"file suspicious: {e.file}"))
        p = manuals_root / toc.manual / e.file
        if not p.exists():
            issues.append(ValidationIssue("WARN", f"file missing: {p}"))

        # duplicate id check
        if e.id in seen_ids:
            issues.append(ValidationIssue("WARN", f"duplicate id: {e.id}"))
        seen_ids.add(e.id)

        # NOTE: Title style check ("第...章") has been intentionally disabled
        # to avoid noisy warnings for non-chapter-style manuals.
        # If needed, re-enable something like:
        # if not _CHAPTER_IN_TITLE.match(e.title):
        #     issues.append(ValidationIssue("WARN", f"title may not start with '第...章': {e.title}"))

    return issues
