# app/services/search.py
from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Tuple, Optional

from app.schemas.search import (
    SearchTextRequest,
    SearchHit,
    FindExceptionsRequest,
    ExceptionHit,
)
from app.repositories.manual import ManualRepository, SectionNotFound

# 許容する“区切り”の集合
# 空白(\s) / 全角空白(\u3000) / 中点 / スラッシュ(全半角) / 各種ハイフン
_SEP_CLASS = r"[\s\u3000・/／\-\u2010\u2011\u2012\u2013\u2014]*"


def _nfkc(s: str) -> str:
    """NFKC 正規化＋改行コード統一。"""
    return unicodedata.normalize(
        "NFKC",
        s.replace("\r\n", "\n").replace("\r", "\n"),
    )


def _iter_sections(
    repo: ManualRepository,
    manual: str,
    section_id: Optional[str],
) -> Iterable[Tuple[str, str]]:
    """
    検索対象となる (section_id, 正規化済み本文) を順に返す。

    - section_id が指定されていればその章のみ
    - 指定なしなら list_sections() の順に全章
    """
    if section_id is not None:
        try:
            sec = repo.get_section(manual, section_id)
        except SectionNotFound:
            # 存在しない場合は何も返さない
            return
        yield section_id, _nfkc(sec["text"])
        return

    for sid in repo.list_sections(manual):
        try:
            sec = repo.get_section(manual, sid)
        except SectionNotFound:
            # ToC にはあるがファイルが無い章はスキップ
            continue
        yield sid, _nfkc(sec["text"])


def _make_snippet(text: str, start: int, end: int, width: int = 80) -> str:
    """
    マッチ位置の前後 width 文字からスニペットを生成。
    端が切れている場合は '…' を付与。
    """
    left = max(0, start - width)
    right = min(len(text), end + width)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(text) else ""
    return prefix + text[left:right].strip() + suffix


def _build_loose_regex(query: str) -> str:
    """
    文字間に任意の区切り（空白/中点/スラッシュ/ハイフン等）が入っても
    マッチする正規表現を生成する。

    例: '帝王切開' → '帝{sep}王{sep}切{sep}開'
    """
    q = _nfkc(query)
    # 各文字をエスケープして、区切りクラスで join
    parts = [re.escape(ch) for ch in q]
    return _SEP_CLASS.join(parts)


def search_text(repo: ManualRepository, req: SearchTextRequest) -> List[SearchHit]:
    """
    /search_text のコアロジック。
    """
    # 大文字小文字は日本語中心なのであまり影響しないが、一応フラグで制御
    flags = 0 if getattr(req, "case_sensitive", False) else re.IGNORECASE

    # モードごとにパターン生成
    mode = req.mode or "regex"
    if mode == "plain":
        pattern = re.escape(req.query)
    elif mode == "loose":
        pattern = _build_loose_regex(req.query)
    else:  # "regex"
        pattern = req.query

    # 不正な正規表現 -> プレーン一致にフォールバック（仕様どおり）
    try:
        regex = re.compile(pattern, flags)
    except re.error:
        regex = re.compile(re.escape(req.query), flags)

    results: List[SearchHit] = []
    limit = req.limit or 10

    for sid, text in _iter_sections(repo, req.manual_name, req.section_id):
        m = regex.search(text)
        if not m:
            continue

        snippet = _make_snippet(text, m.start(), m.end())
        results.append(SearchHit(section_id=sid, snippet=snippet))

        if len(results) >= limit:
            break

    return results


# 例外抽出用キーワード（必要に応じて拡張）
_EXCEPTION_TERMS = [
    r"留意",
    r"注意",
    r"例外",
    r"対象外",
    r"禁止",
    r"適用しない",
    r"支払われない",
    r"支給されない",
    r"不支給",
    r"不適用",
    r"除外",
    r"取り扱わない",
]
_EXCEPTION_RE = re.compile("|".join(_EXCEPTION_TERMS))


def find_exceptions(
    repo: ManualRepository,
    req: FindExceptionsRequest,
) -> List[ExceptionHit]:
    """
    /find_exceptions のコアロジック。
    """
    hits: List[ExceptionHit] = []
    limit = req.limit or 10

    for sid, text in _iter_sections(repo, req.manual_name, req.section_id):
        lines = text.split("\n")

        for i, ln in enumerate(lines):
            if not _EXCEPTION_RE.search(ln):
                continue

            # 前後1行ずつを含めた文脈を生成
            ctx = []
            if i - 1 >= 0:
                ctx.append(lines[i - 1].strip())
            ctx.append(ln.strip())
            if i + 1 < len(lines):
                ctx.append(lines[i + 1].strip())

            snippet = " ".join([c for c in ctx if c])
            if not snippet:
                continue

            hits.append(ExceptionHit(section_id=sid, text=snippet))
            if len(hits) >= limit:
                return hits

    return hits
