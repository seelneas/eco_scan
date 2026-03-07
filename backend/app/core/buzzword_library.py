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
CATEGORY_LABELS = {
    "vague_eco": "Vague Eco-Language",
    "unregulated_claim": "Unregulated Sustainability Claim",
    "brand_internal": "Brand-Internal Label",
    "misleading_natural": "Misleading 'Natural' Claim",
    "carbon_vague": "Vague Carbon/Climate Claim",
    "circular_vague": "Vague Circularity Claim",
    "ethical_vague": "Vague Ethical Claim",
    "packaging_claim": "Unverified Packaging Claim",
}


# ──────────────────────────────────────────
# The Buzzword Database
# ──────────────────────────────────────────
BUZZWORD_DATABASE = [
    # ═══════════════════════════════════════
    # VAGUE ECO-LANGUAGE
    # ═══════════════════════════════════════
    {
        "term": "eco-friendly",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\beco[\s-]?friendly\b",
        "requires_evidence": "Specific certification (e.g., EU Ecolabel, GOTS, Bluesign)",
        "explanation": "No legal or scientific definition exists for 'eco-friendly'. Any product can use this term without substantiation.",
    },
    {
        "term": "earth-friendly",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bearth[\s-]?friendly\b",
        "requires_evidence": "Life cycle assessment or recognized environmental certification",
        "explanation": "Identical in vagueness to 'eco-friendly'. No regulatory standard defines this term.",
    },
    {
        "term": "planet-positive",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bplanet[\s-]?positive\b",
        "requires_evidence": "Verified carbon-negative status or net-positive environmental impact assessment",
        "explanation": "Implies the product benefits the planet, which requires extraordinary evidence to prove.",
    },
    {
        "term": "sustainable",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bsustainab(?:le|ly|ility)\b",
        "requires_evidence": "Specific sustainability metrics, certifications, or third-party audited standards",
        "explanation": "'Sustainable' is the most overused term in green marketing. Without specifying WHAT is sustainable and HOW, it is meaningless.",
    },
    {
        "term": "green",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bgreen(?:er)?\b(?!\s*(?:color|colour|dye|tea|bean|house|field))",
        "requires_evidence": "Specific environmental benefit with data",
        "explanation": "When used to describe environmental qualities (not the color), 'green' has no defined meaning.",
    },
    {
        "term": "environmentally friendly",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\benvironment(?:ally)?\s*friendly\b",
        "requires_evidence": "Environmental impact assessment or recognized certification",
        "explanation": "No standard defines what qualifies as 'environmentally friendly'.",
    },
    {
        "term": "clean",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bclean\b(?!\s*(?:up|ing|ed|er|room|water))",
        "requires_evidence": "Chemical safety certification like OEKO-TEX or Bluesign",
        "explanation": "In a sustainability context, 'clean' has no standardized definition.",
    },
    {
        "term": "better for the planet",
        "risk_level": "high",
        "category": "vague_eco",
        "regex_pattern": r"\bbetter\s+for\s+(?:the\s+)?(?:planet|earth|environment)\b",
        "requires_evidence": "Comparative life cycle assessment showing measurable improvement",
        "explanation": "Comparative claim ('better') without specifying what it's compared to or by how much.",
    },
    {
        "term": "responsibly made",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bresponsib(?:le|ly)\s*(?:made|sourced|crafted|produced)\b",
        "requires_evidence": "SA8000, Fair Trade, or similar labor/environmental certification",
        "explanation": "'Responsibly' is subjective without defining the standard of responsibility.",
    },
    {
        "term": "mindful",
        "risk_level": "medium",
        "category": "vague_eco",
        "regex_pattern": r"\bmindful(?:ly)?\b",
        "requires_evidence": "Specific environmental or social practices with evidence",
        "explanation": "'Mindful' implies care but provides no measurable commitment.",
    },

    # ═══════════════════════════════════════
    # MISLEADING 'NATURAL' CLAIMS
    # ═══════════════════════════════════════
    {
        "term": "natural",
        "risk_level": "medium",
        "category": "misleading_natural",
        "regex_pattern": r"\bnatural(?:ly)?\b(?!\s*(?:gas|disaster|language|law|rubber))",
        "requires_evidence": "Material composition disclosure showing natural fiber content",
        "explanation": "'Natural' is not regulated in textiles. PVC can technically be 'inspired by nature'.",
    },
    {
        "term": "pure",
        "risk_level": "medium",
        "category": "misleading_natural",
        "regex_pattern": r"\bpure(?:ly)?\b(?!\s*(?:math|logic|water))",
        "requires_evidence": "Material composition showing 100% of a specific natural fiber",
        "explanation": "'Pure' could mean anything. A 'pure polyester' garment is 'pure' petroleum.",
    },
    {
        "term": "organic",
        "risk_level": "medium",
        "category": "misleading_natural",
        "regex_pattern": r"\borganic\b(?!\s*(?:cotton|linen|hemp|wool|silk|bamboo|certified))",
        "requires_evidence": "GOTS or OCS certification specifying which component is organic",
        "explanation": "'Organic' without specifying the material or certification is vague. Only certified organic fibers count.",
    },
    {
        "term": "non-toxic",
        "risk_level": "medium",
        "category": "misleading_natural",
        "regex_pattern": r"\bnon[\s-]?toxic\b",
        "requires_evidence": "OEKO-TEX Standard 100 or equivalent chemical safety testing",
        "explanation": "All textiles contain some chemicals from dyeing/finishing. 'Non-toxic' needs testing certification.",
    },
    {
        "term": "chemical-free",
        "risk_level": "high",
        "category": "misleading_natural",
        "regex_pattern": r"\bchemical[\s-]?free\b",
        "requires_evidence": "Impossible to substantiate — everything is made of chemicals",
        "explanation": "Scientifically inaccurate. All matter is chemical. This term is inherently misleading.",
    },

    # ═══════════════════════════════════════
    # VAGUE CARBON/CLIMATE CLAIMS
    # ═══════════════════════════════════════
    {
        "term": "carbon neutral",
        "risk_level": "medium",
        "category": "carbon_vague",
        "regex_pattern": r"\bcarbon[\s-]?neutral\b",
        "requires_evidence": "Verified by Gold Standard, VCS, or ClimatePartner with public offset details",
        "explanation": "Without specifying the offset methodology and verification body, this claim is unverifiable.",
    },
    {
        "term": "climate positive",
        "risk_level": "high",
        "category": "carbon_vague",
        "regex_pattern": r"\bclimate[\s-]?positive\b",
        "requires_evidence": "Verified carbon-negative operations with third-party audit",
        "explanation": "A stronger claim than carbon neutral, requiring even more evidence.",
    },
    {
        "term": "low carbon",
        "risk_level": "medium",
        "category": "carbon_vague",
        "regex_pattern": r"\blow[\s-]?carbon\b",
        "requires_evidence": "Comparative carbon footprint data with industry benchmarks",
        "explanation": "'Low' relative to what? Without a baseline comparison, this is meaningless.",
    },
    {
        "term": "zero waste",
        "risk_level": "medium",
        "category": "carbon_vague",
        "regex_pattern": r"\bzero[\s-]?waste\b",
        "requires_evidence": "Waste audit showing 90%+ diversion rate from landfill",
        "explanation": "True zero-waste manufacturing is extremely rare. Often refers only to one stage of production.",
    },

    # ═══════════════════════════════════════
    # VAGUE CIRCULARITY CLAIMS
    # ═══════════════════════════════════════
    {
        "term": "recyclable",
        "risk_level": "medium",
        "category": "circular_vague",
        "regex_pattern": r"\brecyclab(?:le|ility)\b",
        "requires_evidence": "Information about existing recycling infrastructure for this specific material",
        "explanation": "'Recyclable' is misleading if no recycling facility actually processes this material type.",
    },
    {
        "term": "biodegradable",
        "risk_level": "medium",
        "category": "circular_vague",
        "regex_pattern": r"\bbio[\s-]?degradab(?:le|ility)\b",
        "requires_evidence": "Composting certification (e.g., OK compost) specifying conditions and timeframe",
        "explanation": "Everything is technically biodegradable given enough time. Needs conditions and timeframe.",
    },
    {
        "term": "compostable",
        "risk_level": "medium",
        "category": "circular_vague",
        "regex_pattern": r"\bcompostab(?:le|ility)\b",
        "requires_evidence": "Industrial vs. home compostability certification with specific standards",
        "explanation": "Industrial compostable items often can't be composted at home or in municipal facilities.",
    },
    {
        "term": "upcycled",
        "risk_level": "low",
        "category": "circular_vague",
        "regex_pattern": r"\bupcycl(?:ed|ing)\b",
        "requires_evidence": "Description of what original material was repurposed",
        "explanation": "Generally a legitimate practice, but needs detail about the source material.",
    },

    # ═══════════════════════════════════════
    # VAGUE ETHICAL CLAIMS
    # ═══════════════════════════════════════
    {
        "term": "ethically made",
        "risk_level": "medium",
        "category": "ethical_vague",
        "regex_pattern": r"\bethical(?:ly)?\s*(?:made|sourced|crafted|produced)\b",
        "requires_evidence": "Fair Trade, SA8000, or equivalent labor certification",
        "explanation": "'Ethical' is subjective. What does it mean — living wages? Safe conditions? Both?",
    },
    {
        "term": "fair wages",
        "risk_level": "medium",
        "category": "ethical_vague",
        "regex_pattern": r"\bfair\s*wages?\b",
        "requires_evidence": "Fair Trade certification or published wage data vs. living wage benchmarks",
        "explanation": "'Fair' is relative. Without comparing to living wage benchmarks, this is vague.",
    },
    {
        "term": "handmade",
        "risk_level": "low",
        "category": "ethical_vague",
        "regex_pattern": r"\bhand[\s-]?made\b",
        "requires_evidence": "Information about artisan conditions and fair compensation",
        "explanation": "While handmade is generally verifiable, it doesn't inherently mean ethical labor conditions.",
    },
    {
        "term": "cruelty-free",
        "risk_level": "medium",
        "category": "ethical_vague",
        "regex_pattern": r"\bcruelty[\s-]?free\b",
        "requires_evidence": "Leaping Bunny or PETA certification for cosmetics; vegan certification for fashion",
        "explanation": "In fashion, 'cruelty-free' has no standard definition beyond not using animal products.",
    },

    # ═══════════════════════════════════════
    # BRAND-INTERNAL LABELS
    # ═══════════════════════════════════════
    {
        "term": "conscious",
        "risk_level": "high",
        "category": "brand_internal",
        "regex_pattern": r"\bconscious(?:\s*(?:choice|collection|edit))?\b",
        "requires_evidence": "Third-party certification — brand-internal labels are not verified",
        "explanation": "Commonly used as internal brand marketing (e.g., H&M 'Conscious'). Not backed by independent standards.",
    },
    {
        "term": "join life",
        "risk_level": "high",
        "category": "brand_internal",
        "regex_pattern": r"\bjoin\s*life\b",
        "requires_evidence": "Third-party certification — Zara's internal label",
        "explanation": "Zara's brand-internal sustainability label. Does not meet third-party verification standards.",
    },
    {
        "term": "move to zero",
        "risk_level": "medium",
        "category": "brand_internal",
        "regex_pattern": r"\bmove\s*to\s*zero\b",
        "requires_evidence": "Third-party certification — Nike's internal sustainability program",
        "explanation": "Nike's internal program. Aspirational language, not a certification.",
    },
    {
        "term": "primegreen",
        "risk_level": "medium",
        "category": "brand_internal",
        "regex_pattern": r"\bprime(?:green|blue)\b",
        "requires_evidence": "GRS certification for recycled content verification",
        "explanation": "Adidas internal labels. Primegreen/Primeblue indicate recycled content but are not independently verified.",
    },
    {
        "term": "responsible edit",
        "risk_level": "high",
        "category": "brand_internal",
        "regex_pattern": r"\bresponsible\s*edit\b",
        "requires_evidence": "Third-party certification — ASOS's internal label",
        "explanation": "ASOS's brand-internal curation label. Selection criteria are not independently audited.",
    },
    {
        "term": "evoluSHEIN",
        "risk_level": "high",
        "category": "brand_internal",
        "regex_pattern": r"\bevolu\s*shein\b",
        "requires_evidence": "Third-party certification",
        "explanation": "SHEIN's sustainability label on a fast-fashion platform with major transparency concerns.",
    },

    # ═══════════════════════════════════════
    # UNVERIFIED PACKAGING CLAIMS
    # ═══════════════════════════════════════
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
