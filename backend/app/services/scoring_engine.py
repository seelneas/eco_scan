"""
EcoScan Scoring Engine (Phase 3 — Hybrid Reasoning)
Implements the weighted sustainability scoring framework and Greenwashing Risk Index.

The Hybrid Approach:
1. The LLM extracts raw data points (materials, certifications, claims) from product text.
2. This engine applies DETERMINISTIC Python logic to calculate weighted scores.
3. This separation ensures consistent, reproducible scoring regardless of LLM variability.
"""

import logging

from app.models.schemas import (
    LLMAnalysisResult,
    ScoringResult,
    CategoryScore,
    GreenwashingReport,
    GWRLevel,
)
from app.core.material_library import (
    MATERIAL_DATABASE,
    CERTIFICATION_DATABASE,
    lookup_material,
    lookup_certification,
)
from app.services.greenwashing_detector import run_greenwashing_detection

logger = logging.getLogger("ecoscan.scoring")


# ──────────────────────────────────────────
# Scoring Weights
# ──────────────────────────────────────────
WEIGHTS = {
    "materials": 0.35,
    "certifications": 0.25,
    "transparency": 0.20,
    "ethics": 0.20,
}


# ──────────────────────────────────────────
# (M) Materials Impact — 35%
# ──────────────────────────────────────────
def calculate_materials_score(analysis: LLMAnalysisResult) -> CategoryScore:
    """
    Score materials using the Material Library for fine-grained impact data.
    Uses the library's 0-100 score (not just high/medium/low tiers) weighted by
    the percentage of each material in the composition.
    """
    if not analysis.materials:
        return CategoryScore(
            category="Materials Impact",
            score=0,
            max_score=100,
            details="No material information found on the product page.",
        )

    total_percentage = 0
    weighted_score = 0
    detail_parts = []

    for material in analysis.materials:
        pct = material.percentage if material.percentage is not None else 0

        # Look up the material in our deterministic library
        mat_data = lookup_material(material.name)
        mat_score = mat_data["score"]

        # Weighted contribution: (percentage / 100) * material_score
        if pct > 0:
            weighted_score += (pct / 100) * mat_score
            total_percentage += pct
        else:
            # If no percentage given, treat as full composition (single material)
            weighted_score += mat_score
            total_percentage = 100

        tier_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(mat_data["tier"], "⚪")
        detail_parts.append(
            f"{tier_emoji} {material.name} ({pct or '?'}%) → "
            f"{mat_data['tier']} tier (score: {mat_score}/100)"
        )

    # Normalize if percentages don't sum to 100
    if total_percentage > 0 and total_percentage != 100:
        weighted_score = (weighted_score / total_percentage) * 100
    elif total_percentage == 0:
        weighted_score = 0

    score = max(0, min(100, weighted_score))

    logger.debug(f"Materials score: {score} (from {len(analysis.materials)} materials)")

    return CategoryScore(
        category="Materials Impact",
        score=round(score, 1),
        max_score=100,
        details="; ".join(detail_parts),
    )


# ──────────────────────────────────────────
# (C) Certifications — 25%
# ──────────────────────────────────────────
def calculate_certifications_score(analysis: LLMAnalysisResult) -> CategoryScore:
    """
    Score based on recognized third-party certifications using the Certification Database.
    Uses tiered points: Gold (10), Silver (5), Bronze (3).
    Caps at 100 to prevent over-scoring from many certifications.
    """
    if not analysis.certifications:
        return CategoryScore(
            category="Certifications",
            score=0,
            max_score=100,
            details="No certifications detected.",
        )

    total_points = 0
    recognized = []
    brand_internal = []

    for cert in analysis.certifications:
        if not cert.is_third_party:
            brand_internal.append(cert.name)
            continue

        # Look up in our certification database
        cert_data = lookup_certification(cert.standard)

        if cert_data:
            points = cert_data["points"]
            total_points += points
            tier_label = cert_data["tier"].upper()
            recognized.append(f"✅ {cert.name} [{tier_label}] (+{points}pts)")
        else:
            # Unknown third-party cert still gets partial credit
            total_points += 2
            recognized.append(f"⚪ {cert.name} [UNRANKED] (+2pts)")

    # Scale: 20 pts = 100 score (2 Gold certs = perfect)
    score = min(100, (total_points / 20) * 100)

    detail_parts = recognized.copy()
    if brand_internal:
        detail_parts.append(f"⚠️ Brand-internal labels (0pts): {', '.join(brand_internal)}")

    details = "; ".join(detail_parts) if detail_parts else "No recognized third-party certifications."

    logger.debug(f"Certifications score: {score} ({total_points} pts from {len(recognized)} certs)")

    return CategoryScore(
        category="Certifications",
        score=round(score, 1),
        max_score=100,
        details=details,
    )


# ──────────────────────────────────────────
# (T) Transparency — 20%
# ──────────────────────────────────────────
def calculate_transparency_score(analysis: LLMAnalysisResult) -> CategoryScore:
    """
    Score based on supply chain disclosure depth.
    Points awarded incrementally:
      - Factory name disclosed: +40
      - Country of manufacture: +20
      - Supply chain depth (tier1: +10, tier2: +20, tier3: +30)
      - Material percentages provided: +10 bonus
    """
    t = analysis.transparency
    score = 0
    detail_parts = []

    # Factory disclosure (the most impactful signal)
    if t.factory_disclosed:
        score += 40
        factory_name = t.factory_name or "Name provided"
        detail_parts.append(f"🏭 Factory disclosed: {factory_name}")

    # Country of manufacture
    if t.country_of_manufacture:
        score += 20
        detail_parts.append(f"🌍 Country: {t.country_of_manufacture}")

    # Supply chain depth bonus
    depth_scores = {"tier1": 10, "tier2": 20, "tier3": 30}
    depth_bonus = depth_scores.get(t.supply_chain_depth.value, 0)
    score += depth_bonus
    if depth_bonus > 0:
        depth_labels = {
            "tier1": "Assembly factory",
            "tier2": "Fabric mill/processor",
            "tier3": "Raw material source",
        }
        label = depth_labels.get(t.supply_chain_depth.value, t.supply_chain_depth.value)
        detail_parts.append(f"🔗 Supply chain depth: {label}")

    # Bonus: material composition transparency
    has_full_composition = (
        len(analysis.materials) > 0
        and all(m.percentage is not None for m in analysis.materials)
    )
    if has_full_composition:
        score += 10
        detail_parts.append("📊 Full material composition disclosed")

    score = min(100, score)
    details = "; ".join(detail_parts) if detail_parts else "No supply chain information disclosed."

    return CategoryScore(
        category="Transparency",
        score=round(score, 1),
        max_score=100,
        details=details,
    )


# ──────────────────────────────────────────
# (E) Ethics & Circularity — 20%
# ──────────────────────────────────────────
def calculate_ethics_score(analysis: LLMAnalysisResult) -> CategoryScore:
    """
    Score based on ethical commitments and circularity signals.
    Points:
      - Living wage: +40
      - Take-back/circularity: +30
      - Carbon neutral (verified): +30
      - Carbon neutral (unverified): +10
    """
    e = analysis.ethical_signals
    score = 0
    detail_parts = []

    if e.living_wage_commitment:
        score += 40
        detail_parts.append("✅ Living wage commitment found")

    if e.take_back_program:
        score += 30
        detail_parts.append("♻️ Take-back/recycling program available")

    if e.carbon_neutral_claim:
        if e.carbon_neutral_verified:
            score += 30
            detail_parts.append("🌱 Carbon neutrality verified by recognized standard")
        else:
            score += 10
            detail_parts.append("⚠️ Carbon neutrality claimed but NOT independently verified")

    score = min(100, score)
    details = "; ".join(detail_parts) if detail_parts else "No ethical commitments detected."

    return CategoryScore(
        category="Ethics & Circularity",
        score=round(score, 1),
        max_score=100,
        details=details,
    )


# ──────────────────────────────────────────
# Letter Grade
# ──────────────────────────────────────────
def determine_grade(score: float) -> str:
    """Convert a 0-100 score to a letter grade with +/- qualifiers."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 73:
        return "B+"
    elif score >= 65:
        return "B"
    elif score >= 58:
        return "C+"
    elif score >= 50:
        return "C"
    elif score >= 42:
        return "D+"
    elif score >= 35:
        return "D"
    else:
        return "F"


# ──────────────────────────────────────────
# Master Scoring Function
# ──────────────────────────────────────────
def compute_ecoscan_score(
    analysis: LLMAnalysisResult,
    raw_product_text: str = "",
) -> ScoringResult:
    """
    The master scoring function. Implements the HYBRID REASONING approach:
    1. LLM has already extracted structured data points.
    2. This function applies DETERMINISTIC logic to compute consistent scores.
    3. The GWRD system runs the full regex + LLM hybrid to detect greenwashing.
    4. The GWR penalty ensures that marketing language is actively penalized.

    Pipeline: Category Scores → Weighted Sum → GWRD Pipeline → GWR Penalty → Final Score → Grade
    """
    logger.info(
        f"Computing score for '{analysis.product.name}' "
        f"(brand: {analysis.product.brand or 'N/A'})"
    )

    # 1. Calculate individual category scores (each on 0-100 scale)
    materials = calculate_materials_score(analysis)
    certifications = calculate_certifications_score(analysis)
    transparency = calculate_transparency_score(analysis)
    ethics = calculate_ethics_score(analysis)

    category_scores = [materials, certifications, transparency, ethics]

    # 2. Calculate weighted base score
    base_score = (
        materials.score * WEIGHTS["materials"]
        + certifications.score * WEIGHTS["certifications"]
        + transparency.score * WEIGHTS["transparency"]
        + ethics.score * WEIGHTS["ethics"]
    )

    # 3. Run the full GWRD pipeline (regex + LLM hybrid)
    gwrd_result = run_greenwashing_detection(
        raw_product_text=raw_product_text,
        llm_analysis=analysis,
    )
    gwr_report = gwrd_result["greenwashing_report"]

    # 4. Apply GWR penalty
    penalty_factor = gwr_report.penalty_percent / 100
    final_score = base_score * (1 - penalty_factor)
    final_score = round(max(0, min(100, final_score)), 1)

    # 5. Determine grade
    grade = determine_grade(final_score)

    logger.info(
        f"Score computed: base={base_score:.1f}, "
        f"GWR={gwr_report.risk_level.value} (-{gwr_report.penalty_percent}%), "
        f"final={final_score} ({grade})"
    )

    return ScoringResult(
        base_score=round(base_score, 1),
        final_score=final_score,
        grade=grade,
        category_scores=category_scores,
        greenwashing_report=gwr_report,
        llm_analysis=analysis,
    )
