from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.schemas.analysis import ProfileSchema, DecisionSchema, AssumptionsSchema
from app.schemas.ai import DecisionParseResult, SecondOpinionResponse
from app.schemas.simulation import UniverseSimulationResult
from app.schemas.stress_test import UniverseStressComparison
from app.schemas.auto_pivot import UserConstraints, SearchConfiguration, AutoPivotResponse

class OrchestratorRequest(BaseModel):
    text: Optional[str] = Field(None, description="Natural language decision text.")
    profile: Optional[ProfileSchema] = None
    decision: Optional[DecisionSchema] = None
    assumptions: Optional[AssumptionsSchema] = None
    stress_scenario_id: Optional[str] = None
    auto_pivot_constraints: Optional[UserConstraints] = None
    auto_pivot_config: Optional[SearchConfiguration] = None

class MLModelMetadata(BaseModel):
    risk_target: str
    estimated_probability: float
    predicted_class: int
    classification_threshold: float
    model_version: str
    limitation: str = "Synthetic-model estimate of simulator-defined target. Not a validated real-world default probability."

class OrchestratorResponse(BaseModel):
    status: str = Field(..., description="Overall status: READY or CLARIFICATION_REQUIRED")
    analysis_id: str
    
    # Input Echo & Clarification
    parsed_result: Optional[DecisionParseResult] = None
    validated_profile: Optional[ProfileSchema] = None
    validated_decision: Optional[DecisionSchema] = None
    assumptions: Optional[AssumptionsSchema] = None
    
    # Financial Simulation
    universes: List[UniverseSimulationResult] = Field(default_factory=list)
    
    # ML Estimates
    ml_estimates: Dict[str, MLModelMetadata] = Field(default_factory=dict, description="ML estimates per universe id")
    
    # Optional Steps
    stress_tests: Dict[str, UniverseStressComparison] = Field(default_factory=dict)
    auto_pivot: Optional[AutoPivotResponse] = None
    second_opinion: Optional[SecondOpinionResponse] = None
    
    warnings: List[str] = Field(default_factory=list)
