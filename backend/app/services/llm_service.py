"""
EcoScan LLM Service (Phase 7 — Streaming Support)
Handles communication with the Google Gemini API using the modern google-genai SDK.
Supports both batch and streaming modes for real-time UI updates.
"""

import json
import logging
from typing import AsyncGenerator

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.prompts import ECOSCAN_SYSTEM_PROMPT, ANALYSIS_USER_PROMPT_TEMPLATE
from app.core.security import strip_pii_from_text
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
    Send product text to Gemini for sustainability analysis (batch mode).
    Returns a validated LLMAnalysisResult or raises an exception.
    """

    # Phase 7: Strip PII before sending to external LLM
    clean_text = strip_pii_from_text(product_text)

    # Build the user message from the template
    user_message = ANALYSIS_USER_PROMPT_TEMPLATE.format(
        product_url=product_url,
        product_text=clean_text,
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
        logger.debug(f"Raw response content: {raw_content[:500]}...")
        raise ValueError(f"Gemini response was not valid JSON: {e}")

    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        raise


async def analyze_product_streaming(
    product_url: str,
    product_text: str,
) -> AsyncGenerator[str, None]:
    """
    Stream LLM analysis via Server-Sent Events.
    Yields SSE-formatted events as the LLM generates chunks.

    Event types sent to the client:
      - "stage"   : Pipeline stage updates (extracting, analyzing, scoring)
      - "chunk"   : Raw LLM text chunks as they arrive
      - "result"  : Final complete JSON result
      - "error"   : Error messages
    """

    # Phase 7: Strip PII before sending to external LLM
    clean_text = strip_pii_from_text(product_text)

    user_message = ANALYSIS_USER_PROMPT_TEMPLATE.format(
        product_url=product_url,
        product_text=clean_text,
    )

    logger.info(f"[STREAM] Starting streaming analysis for: {product_url}")

    # Stage 1: Extracting
    yield _sse_event("stage", {"stage": "extracting", "message": "Extracting product data..."})

    # Stage 2: Analyzing
    yield _sse_event("stage", {"stage": "analyzing", "message": "Running AI analysis..."})

    try:
        # Stream from Gemini
        accumulated = ""

        async for chunk in client.aio.models.generate_content_stream(
            model=settings.LLM_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=ECOSCAN_SYSTEM_PROMPT,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
                response_mime_type="application/json",
            ),
        ):
            if chunk.text:
                accumulated += chunk.text
                # Send the chunk to client for progress indication
                yield _sse_event("chunk", {
                    "text": chunk.text,
                    "total_length": len(accumulated),
                })

        logger.info(f"[STREAM] Gemini streaming complete ({len(accumulated)} chars)")

        if not accumulated:
            yield _sse_event("error", {"message": "Empty response from LLM"})
            return

        # Stage 3: Scoring
        yield _sse_event("stage", {"stage": "scoring", "message": "Calculating sustainability scores..."})

        # Parse and validate
        parsed_json = json.loads(accumulated)
        analysis = LLMAnalysisResult.model_validate(parsed_json)

        logger.info(
            f"[STREAM] Analysis complete for '{analysis.product.name}': "
            f"{len(analysis.materials)} materials, "
            f"{len(analysis.certifications)} certifications detected."
        )

        # Return the validated analysis as a serializable dict
        yield _sse_event("analysis_ready", {
            "analysis": json.loads(analysis.model_dump_json()),
        })

    except json.JSONDecodeError as e:
        logger.error(f"[STREAM] Invalid JSON from Gemini: {e}")
        yield _sse_event("error", {"message": f"LLM returned invalid data: {e}"})

    except Exception as e:
        logger.error(f"[STREAM] Analysis failed: {e}")
        yield _sse_event("error", {"message": f"Analysis failed: {str(e)}"})


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    json_data = json.dumps(data)
    return f"event: {event_type}\ndata: {json_data}\n\n"
