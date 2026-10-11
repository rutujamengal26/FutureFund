import json
import logging
import time
import httpx
from typing import Optional, Type, TypeVar, Any
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class AIConfigurationError(Exception):
    pass

class AIAPIError(Exception):
    pass

class AITimeoutError(Exception):
    pass

class AIValidationError(Exception):
    pass

def get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise AIConfigurationError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def generate_structured_content(
    prompt: str,
    response_model: Type[T],
    max_retries: int = 3,
    system_instruction: Optional[str] = None
) -> T:
    """
    Generates structured content from the configured AI provider.
    """
    if settings.AI_PROVIDER == "groq":
        return _generate_with_groq(prompt, response_model, max_retries, system_instruction)
    if settings.AI_PROVIDER == "gemini":
        return _generate_with_gemini(prompt, response_model, max_retries, system_instruction)
    raise AIConfigurationError(
        f"Unsupported AI_PROVIDER '{settings.AI_PROVIDER}'. Configure 'gemini' or 'groq'."
    )

def _generate_with_gemini(
    prompt: str,
    response_model: Type[T],
    max_retries: int,
    system_instruction: Optional[str]
) -> T:
    client = get_gemini_client()
    model_name = settings.GEMINI_MODEL
    
    config_dict = {
        "response_mime_type": "application/json",
        "response_schema": response_model,
        "temperature": 0.0
    }
    if system_instruction:
        config_dict["system_instruction"] = system_instruction
        
    config = types.GenerateContentConfig(**config_dict)

    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            
            if not response.text:
                raise AIAPIError("Received empty response text from Gemini.")
            
            if hasattr(response, "parsed") and response.parsed is not None:
                if isinstance(response.parsed, response_model):
                    return response.parsed
                if isinstance(response.parsed, dict):
                    return response_model.model_validate(response.parsed)
                    
            return response_model.model_validate_json(response.text)
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            raise AIValidationError(f"Invalid structured output: {e}")
        except httpx.TimeoutException as e:
            logger.warning(f"Gemini API timeout on attempt {attempt+1}: {e}")
            last_error = AITimeoutError(f"Timeout connecting to Gemini: {e}")
        except Exception as e:
            logger.warning(f"Gemini API call failed on attempt {attempt+1}: {e}")
            last_error = e
        attempt += 1
        if attempt < max_retries:
            time.sleep(2 ** attempt)

    if isinstance(last_error, AITimeoutError):
        raise last_error
    raise AIAPIError(f"Failed to generate content after {max_retries} attempts. Last error: {last_error}")

def get_groq_client() -> Any:
    try:
        import groq
    except ImportError:
        raise AIConfigurationError("The 'groq' library is not installed.")
    
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise AIConfigurationError("GROQ_API_KEY is not set.")
    return groq.Groq(api_key=api_key)

def _generate_with_groq(
    prompt: str,
    response_model: Type[T],
    max_retries: int,
    system_instruction: Optional[str]
) -> T:
    client = get_groq_client()
    model_name = settings.GROQ_MODEL
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    
    schema_json = response_model.model_json_schema()
    schema_prompt = f"\n\nYou MUST return ONLY valid JSON matching this schema:\n{json.dumps(schema_json)}"
    
    if messages and messages[0]["role"] == "system":
        messages[0]["content"] += schema_prompt
    else:
        messages.insert(0, {"role": "system", "content": schema_prompt})
    
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            import groq
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=850
            )

            
            content = response.choices[0].message.content
            if not content:
                raise AIAPIError("Received empty response content from Groq.")
                
            return response_model.model_validate_json(content)
            
        except ValidationError as e:
            logger.error(f"Pydantic validation failed for Groq output: {e}")
            raise AIValidationError(f"Invalid structured output from Groq: {e}")
        except groq.APIConnectionError as e:
            logger.warning(f"Groq API connection error on attempt {attempt+1}: {e}")
            last_error = e
        except groq.RateLimitError as e:
            logger.warning(f"Groq rate limit on attempt {attempt+1}: {e}")
            last_error = e
            # Increase wait time for rate limits
            time.sleep(4 ** attempt)
            attempt += 1
            continue
        except groq.APIError as e:
            logger.warning(f"Groq API error on attempt {attempt+1}: {e}")
            last_error = e
            # Don't retry authentication errors
            if e.status_code in (401, 403):
                raise AIAPIError(f"Groq authentication error: {e}")
        except Exception as e:
            logger.warning(f"Groq API call failed on attempt {attempt+1}: {e}")
            last_error = e
            
        attempt += 1
        if attempt < max_retries:
            time.sleep(2 ** attempt)
            
    if last_error:
        raise last_error
    raise AIAPIError(f"Failed to generate content with Groq after {max_retries} attempts.")
