from sqlalchemy.orm import Session
from typing import Optional, List
from app.database.models import (
    FinancialProfile, Decision, AnalysisRun, AnalysisUniverseResult, 
    StressTestRun, AutoPivotRun, AutoPivotRecommendation
)
from app.schemas.analysis import ProfileSchema, DecisionSchema

def save_profile(db: Session, user_id: str, profile_name: str, profile_data: ProfileSchema, is_default: bool = False) -> FinancialProfile:
    db_profile = FinancialProfile(
        user_id=user_id,
        profile_name=profile_name,
        profile_data=profile_data.model_dump(),
        is_default=is_default
    )
    db.add(db_profile)
    db.commit()
    
    from sqlalchemy import text
    from app.core.config import settings
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SELECT set_config('app.current_user_id', :uid, true);"), {"uid": user_id})
        
    db.refresh(db_profile)
    return db_profile

def get_profiles(db: Session, user_id: str) -> List[FinancialProfile]:
    return db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).order_by(FinancialProfile.created_at.desc()).all()

def get_profile(db: Session, profile_id: str, user_id: str) -> Optional[FinancialProfile]:
    return db.query(FinancialProfile).filter(FinancialProfile.id == profile_id, FinancialProfile.user_id == user_id).first()

def delete_profile(db: Session, profile_id: str, user_id: str) -> bool:
    prof = get_profile(db, profile_id, user_id)
    if not prof:
        return False
    db.delete(prof)
    db.commit()
    return True

def get_analyses(db: Session, user_id: str, limit: int = 20, offset: int = 0) -> List[AnalysisRun]:
    return db.query(AnalysisRun).filter(AnalysisRun.user_id == user_id).order_by(AnalysisRun.created_at.desc()).limit(limit).offset(offset).all()

def get_analysis(db: Session, analysis_id: str, user_id: str) -> Optional[AnalysisRun]:
    return db.query(AnalysisRun).filter(AnalysisRun.id == analysis_id, AnalysisRun.user_id == user_id).first()
