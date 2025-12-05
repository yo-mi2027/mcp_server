from __future__ import annotations
import json, logging, re, hashlib, time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from app.schemas.toc import TocFile, TocEntry
from app.core.config import Settings
from app.core.validation import validate_toc_relaxed

log = logging.getLogger(__name__)

class ManualNotFound(Exception): ...
class SectionNotFound(Exception): ...
class TocLoadError(Exception): ...

@dataclass
class _ManualCache:
    sha: str
    mtime: float
    toc: TocFile
    id_to_entry: Dict[str, TocEntry]
    num_to_id: Dict[str, str]  # "2-1" -> "02-1" or "02-1_入院" など

def _calc_sha(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha256(data).hexdigest()

class ManualRepository:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = Path(settings.manuals_root)
        self._cache: Dict[str, _ManualCache] = {}

    # -------- Discover manuals
    def list_manuals(self) -> List[str]:
        if not self.root.exists():
            return []
        manuals = []
        for sub in self.root.iterdir():
            if sub.is_dir() and (sub / "00_目次.json").exists():
                manuals.append(sub.name)
        manuals.sort()
        return manuals

    # -------- Loading & cache
    def _load_toc_file(self, manual: str) -> TocFile:
        path = Path(self.settings.toc.path_pattern.format(manual=manual))
        if not path.exists():
            raise ManualNotFound(f"manual '{manual}' not found (missing {path})")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            toc = TocFile(**data)
        except Exception as e:
            raise TocLoadError(str(e)) from e

        # relaxed validation
        issues = validate_toc_relaxed(toc, self.root)
        for it in issues:
            level = logging.WARNING if it.level == "WARN" else logging.ERROR
            log.log(level, f"[validate] manual={manual} {it.msg}")

        return toc

    def _ensure_loaded(self, manual: str) -> _ManualCache:
        path = Path(self.settings.toc.path_pattern.format(manual=manual))
        if not path.exists():
            raise ManualNotFound(f"manual '{manual}' not found")

        mtime = path.stat().st_mtime
        sha = _calc_sha(path)

        cached = self._cache.get(manual)
        if cached and cached.mtime == mtime and cached.sha == sha:
            return cached

        toc = self._load_toc_file(manual)
        # index maps
        id_to_entry: Dict[str, TocEntry] = {e.id: e for e in toc.toc}
        num_to_id: Dict[str, str] = {}
        # "第2章-1 ..." → "2-1", "第10章 ..." → "10"
        for e in toc.toc:
            m = re.match(r"^第(?P<n>\d+)章(?:-(?P<s>\d+))?", e.title)
            if m:
                k = f"{m.group('n')}-{m.group('s')}" if m.group("s") else m.group("n")
                num_to_id[k] = e.id

        cache = _ManualCache(sha=sha, mtime=mtime, toc=toc,
                             id_to_entry=id_to_entry, num_to_id=num_to_id)
        self._cache[manual] = cache
        return cache

    # -------- Public API
    def load_toc(self, manual: str) -> TocFile:
        return self._ensure_loaded(manual).toc

    def list_sections(self, manual: str) -> List[str]:
        c = self._ensure_loaded(manual)
        return [e.id for e in c.toc.toc]

    def get_section(self, manual: str, section_id: str) -> dict:
        c = self._ensure_loaded(manual)
        entry = c.id_to_entry.get(section_id)
        if not entry:
            raise SectionNotFound(f"section '{section_id}' not found in '{manual}'")
        p = self.root / manual / entry.file
        if not p.exists():
            # relaxed: 404で返す
            raise SectionNotFound(f"file not found: {entry.file}")
        text = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        return {"id": entry.id, "file": entry.file, "text": text, "encoding": "utf-8"}

    def get_outline(self, manual: str, section_id: str) -> dict:
        c = self._ensure_loaded(manual)
        entry = c.id_to_entry.get(section_id)
        if not entry:
            raise SectionNotFound(f"section '{section_id}' not found in '{manual}'")
        return {"id": entry.id, "children": entry.children or []}

    def resolve_reference(self, manual: str, ref_text: str) -> Optional[str]:
        """
        "第2章" / "第2章-1" を section_id に解決（簡易）
        """
        c = self._ensure_loaded(manual)
        m = re.search(r"第\s*(\d+)\s*章(?:\s*-\s*(\d+))?", ref_text)
        if not m: 
            return None
        key = f"{m.group(1)}-{m.group(2)}" if m.group(2) else m.group(1)
        return c.num_to_id.get(key)