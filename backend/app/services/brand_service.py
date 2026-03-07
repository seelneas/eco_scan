"""
EcoScan Brand Intelligence Service (Phase 6)
Tracks brand-level ethical ratings independently of individual products.

Every time a product is analyzed, the brand's rolling profile is updated.
This creates a persistent "Brand Memory" that grows smarter with every scan.
"""

import logging
from typing import Optional
from collections import Counter

from sqlalchemy.orm import Session

from app.models.database import BrandProfile, ProductAnalysis
from app.models.schemas import ScoringResult

logger = logging.getLogger("ecoscan.brand")


# ──────────────────────────────────────────
# Normalization
# ──────────────────────────────────────────
def normalize_brand_name(name: str) -> str:
    """Normalize brand name for consistent lookups."""
    if not name:
        return "unknown"
    return name.strip().lower().replace("'", "").replace('"', "").replace(",", "")


def determine_brand_grade(avg_score: float) -> str:
    """Map average score to letter grade."""
    if avg_score >= 90:
        return "A+"
    elif avg_score >= 80:
        return "A"
    elif avg_score >= 73:
        return "B+"
    elif avg_score >= 65:
        return "B"
    elif avg_score >= 58:
        return "C+"
    elif avg_score >= 50:
        return "C"
    elif avg_score >= 42:
        return "D+"
    elif avg_score >= 35:
        return "D"
    else:
        return "F"


def determine_brand_risk(avg_gwr: float) -> str:
    """Map average GWR index to risk level."""
    if avg_gwr <= 0.5:
        return "low"
    elif avg_gwr <= 1.5:
        return "medium"
    else:
        return "high"


# ──────────────────────────────────────────
# Core: Update Brand Profile
# ──────────────────────────────────────────
def update_brand_profile(
    db: Session,
    brand_name: str,
    scoring_result: ScoringResult,
) -> BrandProfile:
    """
    Update (or create) a brand's rolling profile after a product is scored.
    Uses incremental averaging: new_avg = old_avg + (new_value − old_avg) / n
    """
    if not brand_name:
        return None

    normalized = normalize_brand_name(brand_name)
    profile = (
        db.query(BrandProfile)
        .filter(BrandProfile.brand_name_normalized == normalized)
        .first()
    )

    # Extract category scores by name
    cat_scores = {cs.category: cs.score for cs in scoring_result.category_scores}
    mat_score = cat_scores.get("Materials Impact", 0)
    cert_score = cat_scores.get("Certifications", 0)
    trans_score = cat_scores.get("Transparency", 0)
    eth_score = cat_scores.get("Ethics & Circularity", 0)
    gwr_index = scoring_result.greenwashing_report.gwr_index

    if profile is None:
        # First product for this brand
        profile = BrandProfile(
            brand_name_normalized=normalized,
            brand_name_display=brand_name.strip(),
            avg_final_score=scoring_result.final_score,
            avg_materials_score=mat_score,
            avg_certifications_score=cert_score,
            avg_transparency_score=trans_score,
            avg_ethics_score=eth_score,
            avg_gwr_index=gwr_index,
            total_products_scanned=1,
            best_score=scoring_result.final_score,
            worst_score=scoring_result.final_score,
            most_common_grade=scoring_result.grade,
            overall_grade=scoring_result.grade,
            risk_level=determine_brand_risk(gwr_index),
        )
        db.add(profile)
        logger.info(f"Brand profile CREATED: {brand_name} (score: {scoring_result.final_score})")
    else:
        # Incremental averaging
        n = profile.total_products_scanned + 1

        profile.avg_final_score += (scoring_result.final_score - profile.avg_final_score) / n
        profile.avg_materials_score += (mat_score - profile.avg_materials_score) / n
        profile.avg_certifications_score += (cert_score - profile.avg_certifications_score) / n
        profile.avg_transparency_score += (trans_score - profile.avg_transparency_score) / n
        profile.avg_ethics_score += (eth_score - profile.avg_ethics_score) / n
        profile.avg_gwr_index += (gwr_index - profile.avg_gwr_index) / n

        profile.total_products_scanned = n
        profile.best_score = max(profile.best_score, scoring_result.final_score)
        profile.worst_score = min(profile.worst_score, scoring_result.final_score)
        profile.overall_grade = determine_brand_grade(profile.avg_final_score)
        profile.risk_level = determine_brand_risk(profile.avg_gwr_index)

        # Compute most common grade from all products
        brand_products = (
            db.query(ProductAnalysis.grade)
            .filter(ProductAnalysis.brand_name == brand_name)
            .all()
        )
        grades = [p.grade for p in brand_products if p.grade]
        grades.append(scoring_result.grade)
        if grades:
            profile.most_common_grade = Counter(grades).most_common(1)[0][0]

        logger.info(
            f"Brand profile UPDATED: {brand_name} "
            f"(avg: {profile.avg_final_score:.1f}, products: {n})"
        )

    db.commit()
    db.refresh(profile)
    return profile


# ──────────────────────────────────────────
# Query: Get Brand Profile
# ──────────────────────────────────────────
def get_brand_profile(db: Session, brand_name: str) -> Optional[BrandProfile]:
    """Retrieve a brand's profile by name."""
    if not brand_name:
        return None
    normalized = normalize_brand_name(brand_name)
    return (
        db.query(BrandProfile)
        .filter(BrandProfile.brand_name_normalized == normalized)
        .first()
    )


def get_all_brands(db: Session, limit: int = 50) -> list[BrandProfile]:
    """Retrieve all brand profiles sorted by number of products scanned."""
    return (
        db.query(BrandProfile)
        .order_by(BrandProfile.total_products_scanned.desc())
        .limit(limit)
        .all()
    )
