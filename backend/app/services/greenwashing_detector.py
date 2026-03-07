"""
EcoScan Greenwashing Risk Detection (GWRD) Service
The hybrid regex + LLM system that actively identifies and flags greenwashing.

Pipeline:
1. REGEX PRE-SCAN: Scan raw text for known buzzwords (fast, deterministic)
2. LLM EXTRACTION: Get structured claims from the LLM analysis
3. CLAIM VERIFICATION: Cross-reference every claim against available evidence
4. RISK INDEX: Calculate the final GWR score from the combined results
"""

import logging
from typing import Optional

from app.core.buzzword_library import (
    scan_text_for_buzzwords,
    get_buzzword_summary,
)
from app.core.material_library import lookup_certification
from app.models.schemas import (
    LLMAnalysisResult,
    GreenwashingReport,
    GWRLevel,
    VagueBuzzword,
    GreenwashingRisk,
    ClaimVerification,
)

logger = logging.getLogger("ecoscan.gwrd")


# ──────────────────────────────────────────
# Step 1: Regex Pre-Scan
# ──────────────────────────────────────────
def regex_prescan(raw_product_text: str) -> dict:
    """
    Run the buzzword regex scanner on raw product text.
    This runs BEFORE the LLM and catches obvious greenwashing fast.
    Returns: {matches: [...], summary: {...}}
    """
    matches = scan_text_for_buzzwords(raw_product_text)
    summary = get_buzzword_summary(matches)

    logger.info(
        f"Regex pre-scan: {summary['total_flags']} buzzwords flagged "
        f"({summary['high_risk_count']} high, {summary['medium_risk_count']} medium, "
        f"{summary['low_risk_count']} low)"
    )

    return {
        "matches": matches,
        "summary": summary,
    }


# ──────────────────────────────────────────
# Step 2: Merge Regex + LLM Findings
# ──────────────────────────────────────────
def merge_buzzword_findings(
    regex_matches: list[dict],
    llm_buzzwords: list[VagueBuzzword],
) -> list[VagueBuzzword]:
    """
    Merge buzzwords found by regex with those found by the LLM.
    The LLM may find context-dependent buzzwords that regex misses.
    Regex may catch terms the LLM normalized away.
    Returns a deduplicated, combined list.
    """
    # Start with LLM findings (they have richer context)
    merged = {bw.word.lower(): bw for bw in llm_buzzwords}

    # Add regex findings that the LLM missed
    for match in regex_matches:
        term_key = match["term"].lower()
        if term_key not in merged:
            # Convert regex match to VagueBuzzword schema
            risk = GreenwashingRisk.HIGH if match["risk_level"] == "high" else GreenwashingRisk.MEDIUM
            merged[term_key] = VagueBuzzword(
                word=match["term"],
                context=match["context"],
                reason=match["explanation"],
                greenwashing_risk=risk,
            )

    return list(merged.values())


# ──────────────────────────────────────────
# Step 3: Claim Verification Pipeline
# ──────────────────────────────────────────
def verify_claims(analysis: LLMAnalysisResult) -> list[ClaimVerification]:
    """
    Systematically verify every sustainability claim against available evidence.

    Logic Flow:
    1. For each verifiable claim, check if supporting certifications exist.
    2. For each certification, verify it's a recognized third-party standard.
    3. For material claims, check if materials match the claim.
    4. For transparency claims, check if factory/supply chain data exists.
    """
    verifications = []

    # Collect all available evidence
    third_party_certs = {
        c.standard.lower()
        for c in analysis.certifications
        if c.is_third_party
    }
    material_names = {m.name.lower() for m in analysis.materials}
    has_factory = analysis.transparency.factory_disclosed
    has_country = analysis.transparency.country_of_manufacture is not None

    # Verify each claimed sustainability attribute
    for claim in analysis.sustainability_claims.verifiable:
        claim_lower = claim.claim.lower()
        evidence_lower = claim.supporting_evidence.lower()

        # Check 1: Is there a matching certification?
        cert_found = any(
            cert_name in claim_lower or cert_name in evidence_lower
            for cert_name in third_party_certs
        )

        if cert_found:
            verifications.append(ClaimVerification(
                claim=claim.claim,
                is_supported=True,
                evidence=claim.supporting_evidence,
                source="certification",
            ))
            continue

        # Check 2: Is there material data supporting this?
        material_match = any(mat in claim_lower for mat in material_names)
        if material_match:
            verifications.append(ClaimVerification(
                claim=claim.claim,
                is_supported=True,
                evidence=claim.supporting_evidence,
                source="material_data",
            ))
            continue

        # Check 3: Is it a transparency claim backed by disclosure?
        is_transparency = any(
            kw in claim_lower
            for kw in ["factory", "supply chain", "made in", "manufactured"]
        )
        if is_transparency and (has_factory or has_country):
            verifications.append(ClaimVerification(
                claim=claim.claim,
                is_supported=True,
                evidence=claim.supporting_evidence,
                source="transparency",
            ))
            continue

        # No evidence found — this "verifiable" claim lacks backing
        verifications.append(ClaimVerification(
            claim=claim.claim,
            is_supported=False,
            evidence="No matching certification, material data, or transparency disclosure found",
            source="none",
        ))

    return verifications


# ──────────────────────────────────────────
# Step 4: Enhanced GWR Index Calculation
# ──────────────────────────────────────────
def calculate_enhanced_gwr(
    merged_buzzwords: list[VagueBuzzword],
    claim_verifications: list[ClaimVerification],
    analysis: LLMAnalysisResult,
) -> GreenwashingReport:
    """
    Calculate the enhanced Greenwashing Risk Index.
    """
    # ... (counts)
    vague_count = len(merged_buzzwords)
    high_risk_vague = sum(1 for bw in merged_buzzwords if bw.greenwashing_risk == GreenwashingRisk.HIGH)
    
    unsupported_list = [v for v in claim_verifications if not v.is_supported]
    unsupported_count = len(unsupported_list)

    # Count positive signals
    verified_count = sum(1 for v in claim_verifications if v.is_supported)
    third_party_certs = sum(1 for c in analysis.certifications if c.is_third_party)
    
    total_evidence = verified_count + third_party_certs + (1 if analysis.transparency.factory_disclosed else 0)

    # Calculate index
    weighted_negatives = vague_count + (high_risk_vague * 0.5) + unsupported_count
    gwr_index = weighted_negatives / (total_evidence + 1)

    # Logic-based level mapping
    if gwr_index <= 0.5:
        risk_level = GWRLevel.LOW
        penalty = 0
    elif gwr_index <= 1.5:
        risk_level = GWRLevel.MEDIUM
        penalty = 15
    else:
        risk_level = GWRLevel.HIGH
        penalty = 40

    return GreenwashingReport(
        vague_claims_count=vague_count,
        verifiable_evidence_count=total_evidence,
        gwr_index=round(gwr_index, 2),
        risk_level=risk_level,
        penalty_percent=penalty,
        flagged_terms=merged_buzzwords,
        unsupported_claims=unsupported_list,
    )


# ──────────────────────────────────────────
# Master GWRD Function
# ──────────────────────────────────────────
def run_greenwashing_detection(
    raw_product_text: str,
    llm_analysis: LLMAnalysisResult,
) -> dict:
    """
    The full GWRD pipeline.
    Called by the scoring engine after LLM extraction.

    Returns:
        {
            "regex_prescan": {...},         # Raw regex scan results
            "merged_buzzwords": [...],       # Combined regex + LLM buzzwords
            "claim_verifications": [...],    # Each claim's verification result
            "greenwashing_report": ...,      # Final GWR report
        }
    """
    logger.info(f"Running GWRD pipeline for '{llm_analysis.product.name}'...")

    # Step 1: Regex pre-scan the raw text
    prescan = regex_prescan(raw_product_text)

    # Step 2: Merge regex + LLM buzzword findings
    merged_buzzwords = merge_buzzword_findings(
        regex_matches=prescan["matches"],
        llm_buzzwords=llm_analysis.sustainability_claims.vague_buzzwords,
    )

    # Step 3: Verify claims against evidence
    claim_verifications = verify_claims(llm_analysis)

    # Step 4: Calculate enhanced GWR
    gwr_report = calculate_enhanced_gwr(
        merged_buzzwords=merged_buzzwords,
        claim_verifications=claim_verifications,
        analysis=llm_analysis,
    )

    unsupported = [v for v in claim_verifications if not v.is_supported]
    if unsupported:
        logger.warning(
            f"⚠️ {len(unsupported)} claims lack evidence: "
            + ", ".join(f'"{v.claim}"' for v in unsupported[:3])
        )

    return {
        "regex_prescan": prescan,
        "merged_buzzwords": merged_buzzwords,
        "claim_verifications": [
            {
                "claim": v.claim,
                "is_supported": v.is_supported,
                "evidence": v.evidence,
                "source": v.source,
            }
            for v in claim_verifications
        ],
        "greenwashing_report": gwr_report,
    }
