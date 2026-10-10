import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    profiles = relationship("FinancialProfile", back_populates="user", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("AnalysisRun", back_populates="user", cascade="all, delete-orphan")

class FinancialProfile(Base):
    __tablename__ = "financial_profiles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_name = Column(String, nullable=False)
    profile_data = Column(JSON, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="profiles")
    decisions = relationship("Decision", back_populates="profile")

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(String, ForeignKey("financial_profiles.id", ondelete="SET NULL"), nullable=True)
    original_text = Column(String, nullable=True)
    normalized_data = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="decisions")
    profile = relationship("FinancialProfile", back_populates="decisions")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(String, ForeignKey("financial_profiles.id", ondelete="SET NULL"), nullable=True)
    decision_id = Column(String, ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False)
    simulation_horizon = Column(Integer, nullable=False)
    request_snapshot = Column(JSON, nullable=False)
    response_snapshot = Column(JSON, nullable=True)
    metadata_info = Column(JSON, nullable=True) # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="analyses")
    universes = relationship("AnalysisUniverseResult", back_populates="analysis", cascade="all, delete-orphan")
    stress_tests = relationship("StressTestRun", back_populates="analysis", cascade="all, delete-orphan")
    auto_pivot_runs = relationship("AutoPivotRun", back_populates="analysis", cascade="all, delete-orphan")

class AnalysisUniverseResult(Base):
    __tablename__ = "analysis_universe_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    universe_code = Column(String, nullable=False)
    result_metrics = Column(JSON, nullable=False)
    monthly_trajectory = Column(JSON, nullable=False)
    
    analysis = relationship("AnalysisRun", back_populates="universes")

class StressTestRun(Base):
    __tablename__ = "stress_test_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(String, nullable=False)
    config_snapshot = Column(JSON, nullable=False)
    baseline_result = Column(JSON, nullable=False)
    stressed_result = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    analysis = relationship("AnalysisRun", back_populates="stress_tests")

class AutoPivotRun(Base):
    __tablename__ = "auto_pivot_runs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    analysis_id = Column(String, ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    constraints_snapshot = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    summary_result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    analysis = relationship("AnalysisRun", back_populates="auto_pivot_runs")
    recommendations = relationship("AutoPivotRecommendation", back_populates="run", cascade="all, delete-orphan")

class AutoPivotRecommendation(Base):
    __tablename__ = "auto_pivot_recommendations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    auto_pivot_run_id = Column(String, ForeignKey("auto_pivot_runs.id", ondelete="CASCADE"), nullable=False)
    rank = Column(Integer, nullable=True)
    candidate_inputs = Column(JSON, nullable=False)
    computed_result = Column(JSON, nullable=False)
    is_eligible = Column(Boolean, nullable=False)
    rejection_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    run = relationship("AutoPivotRun", back_populates="recommendations")
