"""
EcoScan API Routes
Defines /analyze, /health, and /feedback endpoints.
"""

import time
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schemas import (
    ProductAnalysisRequest,
    ProductAnalysisResponse,
    AnalysisMetadata,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
)
from app.models.database import Feedback, AnalysisLog, get_engine, create_tables, get_session_factory
from app.services.llm_service import analyze_product_with_llm
from app.services.scoring_engine import compute_ecoscan_score
from app.services.cache_service import (
    get_cached_analysis,
    save_analysis_to_cache,
    log_analysis_event,
)

logger = logging.getLogger("ecoscan.api")
settings = get_settings()

# ──────────────────────────────────────────
# Database Setup
# ──────────────────────────────────────────
engine = get_engine("sqlite:///./ecoscan.db")
create_tables(engine)
SessionFactory = get_session_factory(engine)

# ──────────────────────────────────────────
# In-Memory Counters (for /health)
# ──────────────────────────────────────────
_startup_time = time.time()
_analysis_count = 0
_feedback_count = 0


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────
# Router
# ──────────────────────────────────────────
router = APIRouter()


# ──────────────────────────────────────────
# GET /health
# ──────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check with uptime and usage statistics."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        llm_model=settings.LLM_MODEL,
        uptime_seconds=round(time.time() - _startup_time, 1),
        total_analyses=_analysis_count,
        total_feedbacks=_feedback_count,
    )


# ──────────────────────────────────────────
# POST /analyze
# ──────────────────────────────────────────
@router.post("/analyze", response_model=ProductAnalysisResponse)
async def analyze_product(
    request: ProductAnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Main analysis endpoint.
    Pipeline: Cache Check → LLM Analysis → Scoring Engine → Cache Save → Response.
    """
    global _analysis_count
    _analysis_count += 1
    start_time = time.time()

    logger.info(f"[#{_analysis_count}] Analysis request for: {request.product_url}")

    try:
        # Step 1: Check database cache
        cached_scoring = get_cached_analysis(db, request.product_url)

        if cached_scoring:
            duration_ms = int((time.time() - start_time) * 1000)

            log_analysis_event(
                db=db,
                product_url=request.product_url,
                was_cached=True,
                duration_ms=duration_ms,
                final_score=cached_scoring.final_score,
            )

            return ProductAnalysisResponse(
                success=True,
                product_url=request.product_url,
                scoring=cached_scoring,
                metadata=AnalysisMetadata(
                    analysis_duration_ms=duration_ms,
                    llm_model=settings.LLM_MODEL,
                    cached=True,
                ),
            )

        # Step 2: Fresh LLM Analysis
        llm_result = await analyze_product_with_llm(
            product_url=request.product_url,
            product_text=request.product_text,
        )

        # Step 3: Scoring Engine
        scoring_result = compute_ecoscan_score(llm_result, raw_product_text=request.product_text)

        duration_ms = int((time.time() - start_time) * 1000)

        # Step 4: Save to cache
        try:
            save_analysis_to_cache(
                db=db,
                product_url=request.product_url,
                scoring_result=scoring_result,
                llm_model=settings.LLM_MODEL,
                duration_ms=duration_ms,
            )
            log_analysis_event(
                db=db,
                product_url=request.product_url,
                was_cached=False,
                duration_ms=duration_ms,
                final_score=scoring_result.final_score,
            )
        except Exception as cache_err:
            logger.warning(f"Cache save failed (non-critical): {cache_err}")

        # Step 5: Build response
        return ProductAnalysisResponse(
            success=True,
            product_url=request.product_url,
            scoring=scoring_result,
            metadata=AnalysisMetadata(
                analysis_duration_ms=duration_ms,
                llm_model=settings.LLM_MODEL,
                cached=False,
            ),
        )

    except ValueError as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.warning(f"Analysis failed (validation): {e}")
        return ProductAnalysisResponse(
            success=False,
            product_url=request.product_url,
            error=f"Analysis error: {str(e)}",
            metadata=AnalysisMetadata(
                analysis_duration_ms=duration_ms,
                llm_model=settings.LLM_MODEL,
                cached=False,
            ),
        )

    except Exception as e:
        logger.error(f"Analysis failed (unexpected): {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal analysis error: {str(e)}",
        )


# ──────────────────────────────────────────
# POST /feedback
# ──────────────────────────────────────────
@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """
    Accept user feedback on analysis results.
    Stores feedback in the database for review and model improvement.
    """
    global _feedback_count
    _feedback_count += 1

    feedback_id = str(uuid.uuid4())

    logger.info(
        f"Feedback received [{request.feedback_type.value}] "
        f"for {request.product_url[:60]}..."
    )

    try:
        feedback = Feedback(
            feedback_id=feedback_id,
            product_url=request.product_url,
            feedback_type=request.feedback_type.value,
            message=request.message,
            expected_score=request.expected_score,
            user_id_hash=request.user_id_hash,
        )
        db.add(feedback)
        db.commit()

        return FeedbackResponse(
            success=True,
            feedback_id=feedback_id,
            message="Thank you! Your feedback has been recorded and will help improve EcoScan.",
        )

    except Exception as e:
        logger.error(f"Feedback save failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}",
        )
