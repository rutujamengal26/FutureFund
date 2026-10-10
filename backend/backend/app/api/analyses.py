from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models import User
from app.services.persistence import get_analyses, get_analysis
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AnalysisSummaryResponse(BaseModel):
    id: str
    status: str
    simulation_horizon: int
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[AnalysisSummaryResponse])
def list_analyses(
    limit: int = Query(20, ge=1, le=100), 
    offset: int = Query(0, ge=0), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return get_analyses(db, current_user.id, limit=limit, offset=offset)

@router.get("/{analysis_id}")
def get_analysis_detail(analysis_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = get_analysis(db, analysis_id, current_user.id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    return {
        "id": analysis.id,
        "status": analysis.status,
        "simulation_horizon": analysis.simulation_horizon,
        "request_snapshot": analysis.request_snapshot,
        "response_snapshot": analysis.response_snapshot,
        "created_at": analysis.created_at
    }
