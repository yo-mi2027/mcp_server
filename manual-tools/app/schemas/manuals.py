# app/schemas/manuals.py

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class SectionResponse(BaseModel):
    """
    GET /get_section のレスポンス用モデル（API 契約）

    必須:
        - manual: マニュアル名（例: "給付金編"）
        - section_id: 章ID（例: "03-1"）
        - title: 章タイトル（ToCのtitle）
        - text: 章本文（改行統一済み）

    任意:
        - file: 章本文ファイル名（ToCのfile）
        - encoding: テキストのエンコーディング（例: "utf-8"）
        - id: 章ID（section_id と同値を入れてよい）
    """

    manual: str
    section_id: str
    title: str
    text: str

    file: Optional[str] = None
    encoding: Optional[str] = None
    id: Optional[str] = None


class ListSectionsResponse(BaseModel):
    """
    GET /list_sections のレスポンス用モデル（API 契約）

    - manual: マニュアル名（例: "給付金編"）
    - sections: section_id の配列（例: ["01", "02-1", "02-2", ...]）
    """

    manual: str
    sections: List[str]
