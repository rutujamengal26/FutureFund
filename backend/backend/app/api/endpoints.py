from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.orchestrator import OrchestratorRequest, OrchestratorResponse
from app.schemas.ai import DecisionParseResult, SecondOpinionRequest, SecondOpinionResponse
from app.schemas.analysis import ProfileSchema
from app.services.decision_orchestrator import analyze_decision
from app.ai.decision_parser import parse_decision_text
from app.ai.second_opinion import generate_second_opinion

from app.database.session import get_db
from app.api.auth import get_current_user_optional
from app.database.models import User

router = APIRouter()

class ParseDecisionRequest(BaseModel):
    text: str
    profile: Optional[ProfileSchema] = None

@router.post("/api/v1/gemini/parse-decision", response_model=DecisionParseResult)
def api_parse_decision(req: ParseDecisionRequest):
    try:
        return parse_decision_text(req.text, req.profile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/v1/gemini/second-opinion", response_model=SecondOpinionResponse)
def api_second_opinion(req: SecondOpinionRequest):
    try:
        return generate_second_opinion(req.analysis_evidence)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/v1/decisions/analyze", response_model=OrchestratorResponse)
def api_analyze(
    request: OrchestratorRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    try:
        return analyze_decision(request, db=db, current_user=current_user)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
