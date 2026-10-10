import json
from typing import Dict, Any
from app.schemas.ai import SecondOpinionRequest, SecondOpinionResponse
from app.ai.client import generate_structured_content

SYSTEM_INSTRUCTION = """
You are the AI Second Opinion engine for FutureFund. Your role is to explain deterministic financial calculations to users.

GROUNDING RULES:
1. Explain computed financial values from the supplied evidence rather than recalculating them yourself.
2. Use ONLY the supplied evidence for numerical claims. If a value is missing, state it is unavailable.
3. Distinguish deterministic calculations (e.g. simulated cash balances, EMIs) from ML estimates (e.g. XGBoost risk labels).
4. The ML estimate (if present) is a predictor of a synthetic reserve-breach target. Do NOT describe it as a validated real-world credit default probability.
5. Distinguish baseline projections from hypothetical stress scenarios.
6. Never claim an alternative or scenario is guaranteed to be 100% safe.
7. Explain any material assumptions used in the simulation (e.g. inflation, income growth).
8. Do not invent EMIs, interest totals, ending savings, reserve-breach months, or risk probabilities.
9. Keep explanations concise, suitable for a dashboard. Do NOT return long essays.
"""

def generate_second_opinion(evidence: Dict[str, Any]) -> SecondOpinionResponse:
    """
    Generates a structured, evidence-grounded Second Opinion from Gemini.
    """
    prompt = f"Please analyze the following validated financial evidence and return a structured Second Opinion:\n\n{json.dumps(evidence, indent=2, default=str)}"
    
    return generate_structured_content(
        prompt=prompt,
        response_model=SecondOpinionResponse,
        system_instruction=SYSTEM_INSTRUCTION
    )
