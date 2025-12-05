from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class SearchTextRequest(BaseModel):
    manual_name: str
    query: str
    section_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    # ↓ ここを regex|plain|loose に拡張
    mode: str = Field("regex", pattern="^(regex|plain|loose)$", description="regex: 正規表現, plain: 文字列一致, loose: 空白/区切り無視のゆるい一致")
    case_sensitive: bool = False

class SearchHit(BaseModel):
    section_id: str
    snippet: str

class SearchTextResponse(BaseModel):
    results: List[SearchHit]

class FindExceptionsRequest(BaseModel):
    manual_name: str
    section_id: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)

class ExceptionHit(BaseModel):
    section_id: str
    text: str

class FindExceptionsResponse(BaseModel):
    results: List[ExceptionHit]
