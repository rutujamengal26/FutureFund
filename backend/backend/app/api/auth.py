from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt

from app.core.config import settings
from app.database.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token, TokenData
from app.services.auth_service import create_user, get_user_by_email, verify_password, create_access_token
from app.database.models import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

from sqlalchemy import text

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    # Set login context to bypass RLS for fetching user record
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SET LOCAL app.is_login = '1';"))
        
    user = get_user_by_email(db, email=token_data.email)
    
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SET LOCAL app.is_login = '';"))
        
    if user is None:
        raise credentials_exception
        
    # Establish transaction-local RLS identity for this authenticated request
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SELECT set_config('app.current_user_id', :uid, true);"), {"uid": user.id})
        
    return user

def get_current_user_optional(token: str = Depends(OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)), db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SET LOCAL app.is_login = '1';"))
        
    db_user = get_user_by_email(db, email=user.email)
    
    if db_user:
        if not settings.DATABASE_URL.startswith("sqlite"):
            db.execute(text("SET LOCAL app.is_login = '';"))
        raise HTTPException(status_code=400, detail="Email already registered")
        
    res = create_user(db=db, user=user)
    
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SET LOCAL app.is_login = '';"))
        
    return res

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SET LOCAL app.is_login = '1';"))
        
    user = get_user_by_email(db, email=form_data.username)
    
    if not settings.DATABASE_URL.startswith("sqlite"):
        db.execute(text("SET LOCAL app.is_login = '';"))
        
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
