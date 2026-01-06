from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class TocItem(BaseModel):
    n: int = Field(..., ge=1)
    label: str
    loc: Optional[str] = None  # 例: "2-1-22"（当面未使用）

class TocChild(BaseModel):
    anchor: str                # "PRE" or "I".."XV"
    label: str
    items: Optional[List[TocItem]] = None

class TocEntry(BaseModel):
    id: str                    # 形式は自由（"02-1" でも "02-1_入院" でもOK）
    title: str                 # "第2章-1 入院(...)" など
    file: str                  # "02-1_入院.txt" (or .md / .json)
    children: Optional[List[TocChild]] = None

class TocFile(BaseModel):
    manual: str
    toc: List[TocEntry]
