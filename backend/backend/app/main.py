from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="FutureFund API",
    description="Backend for FutureFund, an AI-powered financial decision simulator.",
    version="1.0.0",
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/api/v1/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", message="FutureFund API is running.")

from app.api.endpoints import router as api_router
from app.api.auth import router as auth_router
from app.api.profiles import router as profiles_router
from app.api.analyses import router as analyses_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles_router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(analyses_router, prefix="/api/v1/analyses", tags=["analyses"])
app.include_router(api_router, tags=["decisions"])
