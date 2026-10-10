from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.api.auth import get_current_user
from app.database.models import User
from app.services.persistence import save_profile, get_profiles, get_profile, delete_profile
from app.schemas.analysis import ProfileSchema
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ProfileResponse(BaseModel):
    id: str
    profile_name: str
    profile_data: ProfileSchema
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProfileCreate(BaseModel):
    profile_name: str
    profile_data: ProfileSchema
    is_default: bool = False

@router.post("", response_model=ProfileResponse)
def create_profile(req: ProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return save_profile(db, current_user.id, req.profile_name, req.profile_data, req.is_default)

@router.get("", response_model=List[ProfileResponse])
def list_profiles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_profiles(db, current_user.id)

@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile_endpoint(profile_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prof = get_profile(db, profile_id, current_user.id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    return prof

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile_endpoint(profile_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = delete_profile(db, profile_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    return
