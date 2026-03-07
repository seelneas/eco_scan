"""
EcoScan API Routes (Phase 7 — Streaming, Rate Limiting, Privacy)
Defines /analyze, /analyze/stream, /health, /feedback, /brands, and /alternatives endpoints.
"""

import time
import uuid
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    validate_api_key,
    analysis_limiter,
    general_limiter,
    get_client_id,
    strip_pii_from_text,
)
from app.models.schemas import (
    ProductAnalysisRequest,
    ProductAnalysisResponse,
    AnalysisMetadata,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    BrandProfileResponse,
    BrandListResponse,
    AlternativeProduct,
    ScoringResult,
)
from app.models.database import (
    Feedback,
    AnalysisLog,
    get_engine,
    create_tables,
    get_session_factory,
)
from app.services.llm_service import analyze_product_with_llm, analyze_product_streaming
from app.services.scoring_engine import compute_ecoscan_score
from app.services.cache_service import (
    get_cached_analysis,
    save_analysis_to_cache,
    log_analysis_event,
)
from app.services.brand_service import (
    update_brand_profile,
    get_brand_profile,
    get_all_brands,
)
from app.services.alternatives_engine import (
    store_product_category,
    find_alternatives,
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
_cache_hit_count = 0


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────
# Rate Limit Dependency
# ──────────────────────────────────────────
async def check_analysis_rate_limit(
    request: Request,
    api_key_id: Optional[str] = Depends(validate_api_key),
):
    """Dependency that enforces rate limiting on analysis endpoints."""
    client_id = get_client_id(request, api_key_id)
    allowed, info = analysis_limiter.check(client_id)

    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_id}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded. Please slow down.",
                "limit": info["limit"],
                "retry_after_seconds": info.get("retry_after", 60),
            },
            headers={"Retry-After": str(info.get("retry_after", 60))},
        )

    return {"client_id": client_id, "rate_info": info}


async def check_general_rate_limit(
    request: Request,
    api_key_id: Optional[str] = Depends(validate_api_key),
):
    """Dependency that enforces rate limiting on general endpoints."""
    client_id = get_client_id(request, api_key_id)
    allowed, info = general_limiter.check(client_id)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down.",
            headers={"Retry-After": str(info.get("retry_after", 60))},
        )

    return {"client_id": client_id, "rate_info": info}


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
# POST /analyze (batch — existing behavior)
# ──────────────────────────────────────────
@router.post("/analyze", response_model=ProductAnalysisResponse)
async def analyze_product(
    request: ProductAnalysisRequest,
    response: Response,
    db: Session = Depends(get_db),
    rate_limit: dict = Depends(check_analysis_rate_limit),
):
    """
    Main analysis endpoint (batch mode).
    Pipeline: Cache Check → LLM Analysis → Scoring → Brand Update → Alternatives → Cache Save → Response.
    """
    global _analysis_count, _cache_hit_count
    _analysis_count += 1
    start_time = time.time()

    logger.info(f"[#{_analysis_count}] Analysis request for: {request.product_url}")
    _add_rate_headers(response, rate_limit)

    try:
        # Step 1: Check database cache
        cached_scoring = get_cached_analysis(db, request.product_url)

        if cached_scoring:
            _cache_hit_count += 1
            duration_ms = int((time.time() - start_time) * 1000)

            log_analysis_event(
                db=db,
                product_url=request.product_url,
                was_cached=True,
                duration_ms=duration_ms,
                final_score=cached_scoring.final_score,
                user_id_hash=request.user_id_hash,
            )

            brand_response = _build_brand_response(db, cached_scoring)
            alternatives = _build_alternatives(
                db, request.product_url, cached_scoring
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
                brand_profile=brand_response,
                alternatives=alternatives,
            )

        # Step 2: Fresh LLM Analysis
        llm_result = await analyze_product_with_llm(
            product_url=request.product_url,
            product_text=request.product_text,
        )

        # Step 3: Scoring Engine
        scoring_result = compute_ecoscan_score(llm_result, raw_product_text=request.product_text)

        duration_ms = int((time.time() - start_time) * 1000)

        # Step 4: Phase 6 — Update Brand Profile & Category Index
        try:
            brand_name = scoring_result.llm_analysis.product.brand
            if brand_name:
                update_brand_profile(db, brand_name, scoring_result)
            store_product_category(db, request.product_url, scoring_result)
        except Exception as p6_err:
            logger.warning(f"Phase 6 update failed (non-critical): {p6_err}")

        # Step 5: Build brand + alternatives for response
        brand_response = _build_brand_response(db, scoring_result)
        alternatives = _build_alternatives(db, request.product_url, scoring_result)

        # Step 6: Save to cache
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
                user_id_hash=request.user_id_hash,
            )
        except Exception as cache_err:
            logger.warning(f"Cache save failed (non-critical): {cache_err}")

        # Step 7: Build response
        return ProductAnalysisResponse(
            success=True,
            product_url=request.product_url,
            scoring=scoring_result,
            metadata=AnalysisMetadata(
                analysis_duration_ms=duration_ms,
                llm_model=settings.LLM_MODEL,
                cached=False,
            ),
            brand_profile=brand_response,
            alternatives=alternatives,
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
# POST /analyze/stream (SSE — Phase 7)
# ──────────────────────────────────────────
@router.post("/analyze/stream")
async def analyze_product_stream(
    request: ProductAnalysisRequest,
    db: Session = Depends(get_db),
    rate_limit: dict = Depends(check_analysis_rate_limit),
):
    """
    Streaming analysis endpoint using Server-Sent Events.
    Sends real-time progress updates as the LLM generates the analysis.

    SSE event types:
      - stage: Pipeline progress ("extracting", "analyzing", "scoring", "complete")
      - chunk: Raw LLM text chunks (for progress bar)
      - result: Final scored result (same structure as /analyze)
      - error: Error message
    """
    global _analysis_count
    _analysis_count += 1
    start_time = time.time()

    logger.info(f"[#{_analysis_count}] STREAM analysis for: {request.product_url}")

    # Check cache first — if cached, send result immediately via SSE
    cached_scoring = get_cached_analysis(db, request.product_url)

    if cached_scoring:
        async def cached_stream():
            duration_ms = int((time.time() - start_time) * 1000)
            brand_response = _build_brand_response(db, cached_scoring)
            alternatives = _build_alternatives(db, request.product_url, cached_scoring)

            result = _build_final_response(
                request.product_url, cached_scoring, duration_ms,
                True, brand_response, alternatives,
            )
            yield _sse("stage", {"stage": "complete", "message": "Results loaded from cache!"})
            yield _sse("result", result)

        return StreamingResponse(
            cached_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Fresh analysis with streaming
    async def analysis_stream():
        nonlocal start_time

        try:
            # Stream the LLM analysis
            analysis_result = None
            async for sse_event in analyze_product_streaming(
                product_url=request.product_url,
                product_text=request.product_text,
            ):
                # Forward stage and chunk events directly
                yield sse_event

                # Check if this is the analysis_ready event
                if "analysis_ready" in sse_event:
                    # Parse the analysis from the SSE event
                    data_line = [l for l in sse_event.split("\n") if l.startswith("data:")][0]
                    data_json = json.loads(data_line[5:].strip())
                    from app.models.schemas import LLMAnalysisResult
                    analysis_result = LLMAnalysisResult.model_validate(
                        data_json["analysis"]
                    )

            if analysis_result is None:
                yield _sse("error", {"message": "Analysis did not complete."})
                return

            # Score the analysis
            scoring_result = compute_ecoscan_score(
                analysis_result, raw_product_text=request.product_text
            )
            duration_ms = int((time.time() - start_time) * 1000)

            # Phase 6 updates
            try:
                brand_name = scoring_result.llm_analysis.product.brand
                if brand_name:
                    update_brand_profile(db, brand_name, scoring_result)
                store_product_category(db, request.product_url, scoring_result)
            except Exception:
                pass

            # Build full response
            brand_response = _build_brand_response(db, scoring_result)
            alternatives = _build_alternatives(db, request.product_url, scoring_result)

            # Cache
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
                    user_id_hash=request.user_id_hash,
                )
            except Exception:
                pass

            # Send the final result
            result = _build_final_response(
                request.product_url, scoring_result, duration_ms,
                False, brand_response, alternatives,
            )
            yield _sse("stage", {"stage": "complete", "message": "Analysis complete!"})
            yield _sse("result", result)

        except Exception as e:
            logger.error(f"[STREAM] Error: {e}")
            yield _sse("error", {"message": str(e)})

    # Prepare headers including rate limit info
    sse_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    if rate_limit:
        info = rate_limit.get("rate_info", {})
        sse_headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
        sse_headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))

    return StreamingResponse(
        analysis_stream(),
        media_type="text/event-stream",
        headers=sse_headers,
    )


# ──────────────────────────────────────────
# SSE Helper
# ──────────────────────────────────────────
def _sse(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def _build_final_response(
    product_url, scoring, duration_ms, cached, brand_response, alternatives,
) -> dict:
    """Build the final result dict for SSE delivery."""
    response = ProductAnalysisResponse(
        success=True,
        product_url=product_url,
        scoring=scoring,
        metadata=AnalysisMetadata(
            analysis_duration_ms=duration_ms,
            llm_model=settings.LLM_MODEL,
            cached=cached,
        ),
        brand_profile=brand_response,
        alternatives=alternatives,
    )
    return json.loads(response.model_dump_json())


def _add_rate_headers(response: Response, rate_limit: dict):
    """Add rate limit info to response headers."""
    if not rate_limit:
        return
    info = rate_limit.get("rate_info", {})
    response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
    response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
    response.headers["X-RateLimit-Reset"] = str(info.get("window", 60))


# ──────────────────────────────────────────
# Helper: Build Brand Response
# ──────────────────────────────────────────
def _build_brand_response(db: Session, scoring: "ScoringResult") -> BrandProfileResponse | None:
    """Build a BrandProfileResponse from the database if the brand exists."""
    brand_name = scoring.llm_analysis.product.brand
    if not brand_name:
        return None

    profile = get_brand_profile(db, brand_name)
    if not profile:
        return None

    return BrandProfileResponse(
        brand_name=profile.brand_name_display,
        avg_final_score=round(profile.avg_final_score, 1),
        avg_materials_score=round(profile.avg_materials_score, 1),
        avg_certifications_score=round(profile.avg_certifications_score, 1),
        avg_transparency_score=round(profile.avg_transparency_score, 1),
        avg_ethics_score=round(profile.avg_ethics_score, 1),
        avg_gwr_index=round(profile.avg_gwr_index, 2),
        total_products_scanned=profile.total_products_scanned,
        best_score=round(profile.best_score, 1),
        worst_score=round(profile.worst_score, 1),
        overall_grade=profile.overall_grade,
        most_common_grade=profile.most_common_grade,
        risk_level=profile.risk_level,
    )


# ──────────────────────────────────────────
# Helper: Build Alternatives
# ──────────────────────────────────────────
def _build_alternatives(
    db: Session, product_url: str, scoring: "ScoringResult"
) -> list[AlternativeProduct]:
    """Find and return better alternatives for the current product."""
    product_name = scoring.llm_analysis.product.name or "Unknown"
    alts = find_alternatives(
        db=db,
        product_url=product_url,
        product_name=product_name,
        current_score=scoring.final_score,
        limit=5,
    )
    return [AlternativeProduct(**a) for a in alts]


# ──────────────────────────────────────────
# POST /feedback
# ──────────────────────────────────────────
@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    response: Response,
    db: Session = Depends(get_db),
    rate_limit: dict = Depends(check_general_rate_limit),
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
    _add_rate_headers(response, rate_limit)

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


# ──────────────────────────────────────────
# GET /brands  (Phase 6)
# ──────────────────────────────────────────
@router.get("/brands", response_model=BrandListResponse)
async def list_brands(
    response: Response,
    limit: int = Query(50, ge=1, le=200, description="Max brands to return"),
    db: Session = Depends(get_db),
    rate_limit: dict = Depends(check_general_rate_limit),
):
    """List all tracked brand profiles, sorted by number of products scanned."""
    _add_rate_headers(response, rate_limit)
    brands = get_all_brands(db, limit=limit)
    brand_responses = [
        BrandProfileResponse(
            brand_name=b.brand_name_display,
            avg_final_score=round(b.avg_final_score, 1),
            avg_materials_score=round(b.avg_materials_score, 1),
            avg_certifications_score=round(b.avg_certifications_score, 1),
            avg_transparency_score=round(b.avg_transparency_score, 1),
            avg_ethics_score=round(b.avg_ethics_score, 1),
            avg_gwr_index=round(b.avg_gwr_index, 2),
            total_products_scanned=b.total_products_scanned,
            best_score=round(b.best_score, 1),
            worst_score=round(b.worst_score, 1),
            overall_grade=b.overall_grade,
            most_common_grade=b.most_common_grade,
            risk_level=b.risk_level,
        )
        for b in brands
    ]
    return BrandListResponse(
        success=True,
        total_brands=len(brand_responses),
        brands=brand_responses,
    )


# ──────────────────────────────────────────
# GET /brands/{brand_name}  (Phase 6)
# ──────────────────────────────────────────
@router.get("/brands/{brand_name}", response_model=BrandProfileResponse)
async def get_brand(
    brand_name: str,
    response: Response,
    db: Session = Depends(get_db),
    rate_limit: dict = Depends(check_general_rate_limit),
):
    """Get a specific brand's ethical profile."""
    _add_rate_headers(response, rate_limit)
    profile = get_brand_profile(db, brand_name)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Brand '{brand_name}' not found.")

    return BrandProfileResponse(
        brand_name=profile.brand_name_display,
        avg_final_score=round(profile.avg_final_score, 1),
        avg_materials_score=round(profile.avg_materials_score, 1),
        avg_certifications_score=round(profile.avg_certifications_score, 1),
        avg_transparency_score=round(profile.avg_transparency_score, 1),
        avg_ethics_score=round(profile.avg_ethics_score, 1),
        avg_gwr_index=round(profile.avg_gwr_index, 2),
        total_products_scanned=profile.total_products_scanned,
        best_score=round(profile.best_score, 1),
        worst_score=round(profile.worst_score, 1),
        overall_grade=profile.overall_grade,
        most_common_grade=profile.most_common_grade,
        risk_level=profile.risk_level,
    )
