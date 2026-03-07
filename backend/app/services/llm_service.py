"""
EcoScan LLM Service
Handles communication with the Google Gemini API using the modern google-genai SDK.
Uses native async support for non-blocking FastAPI operations.
"""

import json
import logging
from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.prompts import ECOSCAN_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT_TEMPLATE
from app.models.schemas import LLMAnalysisResult

logger = logging.getLogger("ecoscan.llm")

settings = get_settings()

# Initialize the modern Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def analyze_product_with_llm(
    product_url: str,
    product_text: str,
) -> LLMAnalysisResult:
    """
    Send product text to Gemini for sustainability analysis.
    Uses the modern google-genai async (aio) client.
    Returns a validated LLMAnalysisResult or raises an exception.
    """

    # Build the user message from the template
    user_message = ANALYSIS_USER_PROMPT_TEMPLATE.format(
        product_url=product_url,
        product_text=product_text,
    )

    logger.info(f"Sending analysis request to Gemini ({settings.LLM_MODEL}) for: {product_url}")

    try:
        # Use the native async interface (client.aio)
        response = await client.aio.models.generate_content(
            model=settings.LLM_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=ECOSCAN_SYSTEM_PROMPT,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
                response_mime_type="application/json",
            ),
        )

        # Get the textual content from the response
        raw_content = response.text
        
        if not raw_content:
            logger.error("Gemini returned an empty response.")
            raise ValueError("Empty response from LLM")

        logger.info(f"Gemini response received ({len(raw_content)} chars)")

        # Parse the JSON response
        parsed_json = json.loads(raw_content)

        # Validate against our Pydantic model
        analysis = LLMAnalysisResult.model_validate(parsed_json)

        logger.info(
            f"Analysis complete for '{analysis.product.name}': "
            f"{len(analysis.materials)} materials, "
            f"{len(analysis.certifications)} certifications detected."
        )

        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned invalid JSON: {e}")
        # Log the raw content for debugging if it's not JSON
        logger.debug(f"Raw response content: {raw_content[:500]}...")
        raise ValueError(f"Gemini response was not valid JSON: {e}")

    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        raise
