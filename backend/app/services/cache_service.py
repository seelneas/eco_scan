"""
EcoScan Cache Service
Provides database-level caching for product analyses to avoid redundant LLM calls.
"""

import hashlib
import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.database import ProductAnalysis, AnalysisLog
from app.models.schemas import ScoringResult

logger = logging.getLogger("ecoscan.cache")

# Cache TTL: 30 days
CACHE_TTL_DAYS = 30


def _hash_url(url: str) -> str:
    """Create a consistent hash for a product URL."""
    return hashlib.sha256(url.strip().lower().encode()).hexdigest()


def get_cached_analysis(
    db: Session,
    product_url: str,
) -> Optional[ScoringResult]:
    """
    Check if we have a cached analysis for this product URL.
    Returns the ScoringResult if found and not expired, else None.
    """
    url_hash = _hash_url(product_url)
    cutoff = datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS)

    cached = (
        db.query(ProductAnalysis)
        .filter(
            ProductAnalysis.product_url_hash == url_hash,
            ProductAnalysis.created_at >= cutoff,
        )
        .first()
    )

    if cached and cached.scoring_result_json:
        try:
            result = ScoringResult.model_validate(cached.scoring_result_json)
            logger.info(f"Cache HIT for {product_url[:60]}...")
            return result
        except Exception as e:
            logger.warning(f"Cache entry invalid, will re-analyze: {e}")
            return None

    return None


def save_analysis_to_cache(
    db: Session,
    product_url: str,
    scoring_result: ScoringResult,
    llm_model: str,
    duration_ms: int,
):
    """
    Save an analysis result to the database for future cache hits.
    Uses upsert logic — updates if the URL hash already exists.
    """
    url_hash = _hash_url(product_url)

    existing = (
        db.query(ProductAnalysis)
        .filter(ProductAnalysis.product_url_hash == url_hash)
        .first()
    )

    scoring_json = json.loads(scoring_result.model_dump_json())
    llm_json = json.loads(scoring_result.llm_analysis.model_dump_json())

    if existing:
        existing.base_score = scoring_result.base_score
        existing.final_score = scoring_result.final_score
        existing.grade = scoring_result.grade
        existing.gwr_index = scoring_result.greenwashing_report.gwr_index
        existing.gwr_level = scoring_result.greenwashing_report.risk_level.value
        existing.llm_result_json = llm_json
        existing.scoring_result_json = scoring_json
        existing.llm_model = llm_model
        existing.analysis_duration_ms = duration_ms
        existing.updated_at = datetime.utcnow()
        logger.info(f"Cache UPDATED for {product_url[:60]}...")
    else:
        product_name = scoring_result.llm_analysis.product.name
        brand_name = scoring_result.llm_analysis.product.brand

        entry = ProductAnalysis(
            product_url_hash=url_hash,
            product_url=product_url,
            brand_name=brand_name,
            product_name=product_name,
            base_score=scoring_result.base_score,
            final_score=scoring_result.final_score,
            grade=scoring_result.grade,
            gwr_index=scoring_result.greenwashing_report.gwr_index,
            gwr_level=scoring_result.greenwashing_report.risk_level.value,
            llm_result_json=llm_json,
            scoring_result_json=scoring_json,
            llm_model=llm_model,
            analysis_duration_ms=duration_ms,
        )
        db.add(entry)
        logger.info(f"Cache SAVED for {product_url[:60]}...")

    db.commit()


def log_analysis_event(
    db: Session,
    product_url: str,
    was_cached: bool,
    duration_ms: int,
    final_score: float,
    user_id_hash: Optional[str] = None,
):
    """Record every scan event for analytics."""
    log = AnalysisLog(
        product_url_hash=_hash_url(product_url),
        user_id_hash=user_id_hash,
        was_cached=was_cached,
        duration_ms=duration_ms,
        final_score=final_score,
    )
    db.add(log)
    db.commit()
