import json
from typing import Optional
from app.schemas.analysis import ProfileSchema, DecisionSchema
from app.schemas.ai import DecisionParseResult, ParsedProfile, ParsedDecision
from app.ai.client import generate_structured_content

SYSTEM_INSTRUCTION = """
You are a highly precise financial extraction assistant for the FutureFund simulation engine.
Your task is to extract numerical financial data and explicit decision parameters from the user's natural language input.

Rules:
1. Extract values EXACTLY as intended in Indian Rupees (INR) and convert units accurately.
   - Example: "5 lakh" -> 500000
   - Example: "1.5L" -> 150000
   - Example: "3 years" -> 36 months
2. Extract decision types based strictly on supported types: "car", "home", "personal", "education".
3. ONLY extract values explicitly stated by the user. DO NOT infer missing fields, guess interest rates, or calculate EMIs yourself.
4. If a piece of required information is missing or ambiguous, list it in missing_fields or ambiguous_fields and provide a clarification_question.
5. If the request lacks enough information to form a simulation (e.g., missing loan amount or tenure), set status to "CLARIFICATION_REQUIRED".
6. Return status "READY" only if the minimum actionable data is present or cleanly merged with existing profile context.
"""

def parse_decision_text(text: str, existing_profile: Optional[ProfileSchema] = None) -> DecisionParseResult:
    """
    Extracts financial decisions and profile updates from natural language text using Gemini.
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")
        
    prompt = f"User input: {text}\n"
    if existing_profile:
        prompt += f"\nExisting user profile context:\n{existing_profile.model_dump_json()}"
        
    result = generate_structured_content(
        prompt=prompt,
        response_model=DecisionParseResult,
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    # Check if the extracted values require clarification
    if not result.decision or not result.decision.type or not result.decision.amount_inr or not result.decision.tenure_months:
        result.status = "CLARIFICATION_REQUIRED"
        if not result.missing_fields:
            if not result.decision or not result.decision.amount_inr:
                result.missing_fields.append("amount_inr")
            if not result.decision or not result.decision.tenure_months:
                result.missing_fields.append("tenure_months")
            if not result.decision or not result.decision.type:
                result.missing_fields.append("type")
        if not result.clarification_question:
            result.clarification_question = "Could you please specify the loan amount, tenure, and purpose of the loan?"
            
    return result
