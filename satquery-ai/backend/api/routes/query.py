"""Agent query entrypoint for natural-language remote sensing questions."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_db
from ...agent import agent_orchestrator

router = APIRouter(prefix="/api/v1/query", tags=["query"])


class AgentQueryRequest(BaseModel):
    query: str
    image_ids: List[str]
    aoi_id: Optional[str] = None


@router.post("")
def handle_agent_query(payload: AgentQueryRequest, db: Session = Depends(get_db)):
    """Dispatch natural-language query to the autonomous agent orchestrator."""
    try:
        result = agent_orchestrator.dispatch_query(
            query=payload.query,
            image_ids=payload.image_ids,
            db=db,
            aoi_id=payload.aoi_id,
        )
        return result
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent query execution failed: {str(e)}",
        )
