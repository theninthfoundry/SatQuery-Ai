from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    aoi_id: str
    question: str


class QueryResponse(BaseModel):
    answer: str
    tool_called: str
    evidence_id: Optional[str] = None


class AOICreateRequest(BaseModel):
    name: str
    geometry: Dict[str, Any]


class AOICreateResponse(BaseModel):
    aoi_id: str
