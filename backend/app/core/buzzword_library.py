"""
EcoScan Buzzword Library
A comprehensive dataset of vague sustainability marketing terms.

Each term is categorized by:
  - risk_level: How deceptive this term typically is
  - category: The type of vague claim
  - regex_pattern: Pattern to match variants of this term in raw text
  - requires_evidence: What certification/data would make this term legitimate
  - explanation: Why this term is flagged
"""

import re
from typing import Optional


# ──────────────────────────────────────────
# Buzzword Categories
# ──────────────────────────────────────────
# ──────────────────────────────────────────
# Buzzword Categories (Simple Version)
# ──────────────────────────────────────────
CATEGORY_LABELS = {
    "vague_eco": "Vague Language",
    "unregulated_claim": "Unproven Claim",
    "brand_internal": "Brand-Internal Label",
    "misleading_natural": "Misleading 'Natural' Claim",
    "carbon_vague": "Vague Climate Claim",
    "circular_vague": "Vague Recycling Claim",
    "ethical_vague": "Vague Fair-Work Claim",
    "packaging_claim": "Packaging Only",
}


# ──────────────────────────────────────────
# The Buzzword Database
# ──────────────────────────────────────────
BUZZWORD_DATABASE = [
    {
        "term": "eco-friendly",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\beco[\s-]?friendly\b",
        "requires_evidence": "A real certificate (like GOTS or EU Ecolabel)",
        "explanation": "This is a very broad term. Since it's not a legal term, anyone can use it without proving it.",
    },
    {
        "term": "earth-friendly",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bearth[\s-]?friendly\b",
        "requires_evidence": "Specific facts about environmental impact",
        "explanation": "Just like 'eco-friendly', this sounds nice but doesn't tell us exactly how it helps the Earth.",
    },
    {
        "term": "sustainable",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bsustainab(?:le|ly|ility)\b",
        "requires_evidence": "Specific proof or certificates",
        "explanation": "'Sustainable' is used everywhere. Unless a brand explains exactly what they mean, it's just marketing.",
    },
    {
        "term": "green",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bgreen(?:er)?\b(?!\s*(?:color|colour|dye|tea|bean|house|field))",
        "requires_evidence": "Actual proof of environmental benefit",
        "explanation": "When a brand says a product is 'green', it doesn't mean much unless they show the math behind it.",
    },
    {
        "term": "clean",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bclean\b(?!\s*(?:up|ing|ed|er|room|water))",
        "requires_evidence": "Certification for safe chemicals (like OEKO-TEX)",
        "explanation": "'Clean' sounds safe, but it's not a regulated word. It needs a certificate to be trustworthy.",
    },
    {
        "term": "better for the planet",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bbetter\s+for\s+(?:the\s+)?(?:planet|earth|environment)\b",
        "requires_evidence": "Proof showing how it's actually better than other products",
        "explanation": "Better than what? Without proof, this is just a fancy promise.",
    },
    {
        "term": "responsibly made",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bresponsib(?:le|ly)\s*(?:made|sourced|crafted|produced)\b",
        "requires_evidence": "Fair Trade or other social certificates",
        "explanation": "What does 'responsible' mean here? Without a standard, it's just the brand's opinion.",
    },
    {
        "term": "natural",
        "risk_level": "medium",
        "category": "misleading_natural",
        "regex_pattern": r"\bnatural(?:ly)?\b(?!\s*(?:gas|disaster|language|law|rubber))",
        "requires_evidence": "Actual list of materials used",
        "explanation": "'Natural' doesn't always mean good. Even crude oil is natural, but we wouldn't want it in our shirts.",
    },
    {
        "term": "organic",
        "risk_level": "medium",
        "category": "misleading_natural",
        "regex_pattern": r"\borganic\b(?!\s*(?:cotton|linen|hemp|wool|silk|bamboo|certified))",
        "requires_evidence": "Offical GOTS or OCS certification",
        "explanation": "'Organic' matters most when we know exactly which material is organic and if it's certified.",
    },
    {
        "term": "chemical-free",
        "risk_level": "high",
        "category": "misleading_natural",
        "regex_pattern": r"\bchemical[\s-]?free\b",
        "requires_evidence": "None — this claim is scientificly impossible",
        "explanation": "Everything in the world is made of chemicals. This is a very misleading term!",
    },
    {
        "term": "carbon neutral",
        "risk_level": "medium",
        "category": "carbon_vague",
        "regex_pattern": r"\bcarbon[\s-]?neutral\b",
        "requires_evidence": "Third-party proof of carbon offsets",
        "explanation": "This usually means the brand is paying to offset its pollution, but we need proof that the offsets are real.",
    },
    {
        "term": "recyclable",
        "risk_level": "medium",
        "category": "circular_vague",
        "regex_pattern": r"\brecyclab(?:le|ility)\b",
        "requires_evidence": "Proof that your local recycling center can actually handle this material",
        "explanation": "A product is only truly recyclable if there are machines in your city that can actually process it.",
    },
    {
        "term": "ethically made",
        "risk_level": "medium",
        "category": "ethical_vague",
        "regex_pattern": r"\bethical(?:ly)?\s*(?:made|sourced|crafted|produced)\b",
        "requires_evidence": "Certificates that prove safe working conditions and fair pay",
        "explanation": "'Ethical' is a big word. We need to know if workers were paid fairly and treated well.",
    },
    {
        "term": "conscious",
        "risk_level": "high",
        "category": "brand_internal",
        "regex_pattern": r"\bconscious(?:\s*(?:choice|collection|edit))?\b",
        "requires_evidence": "A real third-party certificate",
        "explanation": "This is usually just a brand's internal name for a line of products. It hasn't been checked by outside experts.",
    },
    {
        "term": "responsible edit",
        "risk_level": "high",
        "category": "brand_internal",
        "regex_pattern": r"\bresponsible\s*edit\b",
        "requires_evidence": "A real third-party certificate",
        "explanation": "This is just a brand's internal label. It doesn't mean an outside auditor has checked the product.",
    },
    {
        "term": "plastic-free packaging",
        "risk_level": "low",
        "category": "packaging_claim",
        "regex_pattern": r"\bplastic[\s-]?free\s*(?:packaging|pack)?\b",
        "requires_evidence": "Evidence of alternative packaging materials used",
        "explanation": "Generally verifiable but only applies to packaging, not the product itself.",
    },
    {
        "term": "eco packaging",
        "risk_level": "medium",
        "category": "packaging_claim",
        "regex_pattern": r"\beco[\s-]?(?:packaging|pack|wrapped)\b",
        "requires_evidence": "FSC certification or specific recycled content percentage for packaging",
        "explanation": "'Eco packaging' is vague. Recycled cardboard? Compostable materials? Needs specifics.",
    },
]


def compile_buzzword_patterns() -> list[dict]:
    """
    Pre-compile all regex patterns for performance.
    Returns the database with compiled patterns attached.
    """
    compiled = []
    for entry in BUZZWORD_DATABASE:
        compiled_entry = entry.copy()
        compiled_entry["_compiled"] = re.compile(
            entry["regex_pattern"],
            re.IGNORECASE,
        )
        compiled.append(compiled_entry)
    return compiled


# Pre-compile on module load
COMPILED_BUZZWORDS = compile_buzzword_patterns()


def scan_text_for_buzzwords(text: str) -> list[dict]:
    """
    Scan raw product text for vague sustainability buzzwords using regex.
    Returns a list of matches with their location, context, and risk data.
    """
    matches = []
    seen_terms = set()

    for entry in COMPILED_BUZZWORDS:
        pattern = entry["_compiled"]
        for match in pattern.finditer(text):
            matched_text = match.group()
            term_key = entry["term"]

            # Avoid duplicate flags for the same term
            if term_key in seen_terms:
                continue
            seen_terms.add(term_key)

            # Extract surrounding context (up to 80 chars)
            start = max(0, match.start() - 40)
            end = min(len(text), match.end() + 40)
            context = text[start:end].strip()
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."

            matches.append({
                "term": term_key,
                "matched_text": matched_text,
                "risk_level": entry["risk_level"],
                "category": entry["category"],
                "category_label": CATEGORY_LABELS.get(entry["category"], "Unknown"),
                "context": context,
                "explanation": entry["explanation"],
                "requires_evidence": entry["requires_evidence"],
                "position": match.start(),
            })

    # Sort by position in text
    matches.sort(key=lambda x: x["position"])

    return matches


def get_buzzword_summary(matches: list[dict]) -> dict:
    """
    Generate a summary of buzzword scan results.
    """
    if not matches:
        return {
            "total_flags": 0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
            "low_risk_count": 0,
            "categories_flagged": [],
            "verdict": "No vague sustainability language detected.",
        }

    high = sum(1 for m in matches if m["risk_level"] == "high")
    medium = sum(1 for m in matches if m["risk_level"] == "medium")
    low = sum(1 for m in matches if m["risk_level"] == "low")
    categories = list(set(m["category_label"] for m in matches))

    if high >= 3:
        verdict = "🔴 CRITICAL: Heavy use of unsubstantiated sustainability language."
    elif high >= 1:
        verdict = "🟠 WARNING: Multiple vague eco-claims detected without evidence."
    elif medium >= 2:
        verdict = "🟡 CAUTION: Some sustainability language lacks specific backing."
    else:
        verdict = "🟢 MINOR: Few vague terms found; mostly legitimate language."

    return {
        "total_flags": len(matches),
        "high_risk_count": high,
        "medium_risk_count": medium,
        "low_risk_count": low,
        "categories_flagged": categories,
        "verdict": verdict,
    }
