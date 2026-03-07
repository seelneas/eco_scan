"""
EcoScan Material Impact Library
A comprehensive database of textile and product materials with sustainability metadata.
Used by the scoring engine for deterministic tier assignment and impact scoring.
"""

# ──────────────────────────────────────────
# Material Impact Database
# Each entry: canonical_name -> {tier, score, category, notes}
#   tier: "high" (sustainable), "medium" (moderate), "low" (harmful)
#   score: 0-100 fine-grained impact score within the tier
#   water: relative water usage (low/medium/high)
#   carbon: relative carbon footprint (low/medium/high)
# ──────────────────────────────────────────

MATERIAL_DATABASE = {
    # ═══════════════════════════════════════
    # TIER: HIGH (Sustainable Materials)
    # ═══════════════════════════════════════
    "organic cotton": {
        "tier": "high",
        "score": 90,
        "water": "medium",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "46% less CO2 than conventional cotton; no pesticides; requires GOTS/OCS for verification.",
    },
    "recycled polyester": {
        "tier": "high",
        "score": 85,
        "water": "low",
        "carbon": "medium",
        "category": "synthetic_recycled",
        "notes": "Diverts plastic from landfill; 59% less energy than virgin polyester; requires GRS/RCS for verification.",
    },
    "recycled nylon": {
        "tier": "high",
        "score": 88,
        "water": "low",
        "carbon": "medium",
        "category": "synthetic_recycled",
        "notes": "Often sourced from ocean waste (Econyl); 80% less carbon than virgin nylon.",
    },
    "econyl": {
        "tier": "high",
        "score": 90,
        "water": "low",
        "carbon": "low",
        "category": "synthetic_recycled",
        "notes": "Regenerated nylon from fishing nets and industrial waste; infinitely recyclable.",
    },
    "hemp": {
        "tier": "high",
        "score": 95,
        "water": "low",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "Requires no pesticides; improves soil health; extremely low water usage.",
    },
    "linen": {
        "tier": "high",
        "score": 88,
        "water": "low",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "Made from flax; biodegradable; low water and pesticide requirements.",
    },
    "organic linen": {
        "tier": "high",
        "score": 92,
        "water": "low",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "Same benefits as linen with certified organic farming.",
    },
    "organic hemp": {
        "tier": "high",
        "score": 97,
        "water": "low",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "The highest-scoring natural fiber; certified organic hemp.",
    },
    "lyocell": {
        "tier": "high",
        "score": 87,
        "water": "low",
        "carbon": "low",
        "category": "semi_synthetic",
        "notes": "Closed-loop production recovers 99%+ of solvent; TENCEL is the most recognized brand.",
    },
    "tencel": {
        "tier": "high",
        "score": 87,
        "water": "low",
        "carbon": "low",
        "category": "semi_synthetic",
        "notes": "Branded lyocell by Lenzing; FSC or PEFC certified wood pulp.",
    },
    "recycled wool": {
        "tier": "high",
        "score": 82,
        "water": "low",
        "carbon": "low",
        "category": "natural_recycled",
        "notes": "Mechanically recycled from post-consumer woolen garments.",
    },
    "recycled cotton": {
        "tier": "high",
        "score": 80,
        "water": "low",
        "carbon": "low",
        "category": "natural_recycled",
        "notes": "Mechanically or chemically recycled; shorter fibers may reduce durability.",
    },
    "piñatex": {
        "tier": "high",
        "score": 85,
        "water": "low",
        "carbon": "low",
        "category": "innovative",
        "notes": "Made from pineapple leaf fiber; vegan leather alternative.",
    },
    "cork fabric": {
        "tier": "high",
        "score": 90,
        "water": "low",
        "carbon": "low",
        "category": "innovative",
        "notes": "Harvested without harming trees; carbon-negative material.",
    },
    "bamboo linen": {
        "tier": "high",
        "score": 80,
        "water": "low",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "Mechanically processed bamboo; different from chemically processed bamboo viscose.",
    },

    # ═══════════════════════════════════════
    # TIER: MEDIUM (Moderate Impact)
    # ═══════════════════════════════════════
    "conventional cotton": {
        "tier": "medium",
        "score": 45,
        "water": "high",
        "carbon": "medium",
        "category": "natural_fiber",
        "notes": "World's most pesticide-intensive crop; 10,000L water per kg.",
    },
    "cotton": {
        "tier": "medium",
        "score": 45,
        "water": "high",
        "carbon": "medium",
        "category": "natural_fiber",
        "notes": "Assumed conventional when not specified as organic or BCI.",
    },
    "bci cotton": {
        "tier": "medium",
        "score": 55,
        "water": "medium",
        "carbon": "medium",
        "category": "natural_fiber",
        "notes": "Better Cotton Initiative promotes better practices but is not organic.",
    },
    "modal": {
        "tier": "medium",
        "score": 60,
        "water": "medium",
        "carbon": "low",
        "category": "semi_synthetic",
        "notes": "From beechwood; TENCEL Modal uses sustainable forestry; generic modal may not.",
    },
    "ecovero viscose": {
        "tier": "medium",
        "score": 65,
        "water": "medium",
        "carbon": "low",
        "category": "semi_synthetic",
        "notes": "Lenzing's sustainable viscose; 50% lower emissions than generic viscose.",
    },
    "deadstock fabric": {
        "tier": "medium",
        "score": 55,
        "water": "low",
        "carbon": "low",
        "category": "reclaimed",
        "notes": "Leftover factory fabric reused; sustainability depends on the original material.",
    },
    "responsible wool": {
        "tier": "medium",
        "score": 60,
        "water": "medium",
        "carbon": "medium",
        "category": "natural_fiber",
        "notes": "RWS-certified farms; animal welfare and land management standards.",
    },
    "wool": {
        "tier": "medium",
        "score": 50,
        "water": "medium",
        "carbon": "medium",
        "category": "natural_fiber",
        "notes": "Biodegradable and durable; impact depends on farming practices.",
    },
    "conventional linen": {
        "tier": "medium",
        "score": 55,
        "water": "low",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "Non-organic flax; still low-impact relative to cotton.",
    },
    "cupro": {
        "tier": "medium",
        "score": 55,
        "water": "medium",
        "carbon": "medium",
        "category": "semi_synthetic",
        "notes": "Made from cotton linter waste; silky feel; closed-loop process.",
    },
    "bamboo viscose": {
        "tier": "medium",
        "score": 40,
        "water": "medium",
        "carbon": "medium",
        "category": "semi_synthetic",
        "notes": "Bamboo grows fast but conversion to viscose uses harsh chemicals.",
    },
    "silk": {
        "tier": "medium",
        "score": 50,
        "water": "medium",
        "carbon": "low",
        "category": "natural_fiber",
        "notes": "Natural protein fiber; ethical concerns with silkworm farming.",
    },

    # ═══════════════════════════════════════
    # TIER: LOW (Harmful / High-Impact)
    # ═══════════════════════════════════════
    "polyester": {
        "tier": "low",
        "score": 15,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Petroleum-based; sheds microplastics; not biodegradable; 5.5kg CO2 per kg.",
    },
    "virgin polyester": {
        "tier": "low",
        "score": 10,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Explicitly virgin petroleum-based polyester.",
    },
    "nylon": {
        "tier": "low",
        "score": 15,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Petroleum-based; nitrous oxide emissions in production.",
    },
    "virgin nylon": {
        "tier": "low",
        "score": 10,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Explicitly virgin petroleum-based nylon.",
    },
    "acrylic": {
        "tier": "low",
        "score": 10,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Petroleum-based; difficult to recycle; significant microplastic shedding.",
    },
    "viscose": {
        "tier": "low",
        "score": 25,
        "water": "high",
        "carbon": "medium",
        "category": "semi_synthetic",
        "notes": "Uses toxic chemicals (carbon disulfide) in production; linked to deforestation.",
    },
    "rayon": {
        "tier": "low",
        "score": 25,
        "water": "high",
        "carbon": "medium",
        "category": "semi_synthetic",
        "notes": "Essentially the same as viscose; chemically processed wood pulp.",
    },
    "conventional leather": {
        "tier": "low",
        "score": 15,
        "water": "high",
        "carbon": "high",
        "category": "animal",
        "notes": "Chrome tanning pollutes waterways; linked to deforestation for cattle farming.",
    },
    "leather": {
        "tier": "low",
        "score": 15,
        "water": "high",
        "carbon": "high",
        "category": "animal",
        "notes": "Assumed conventional unless specified as vegetable-tanned or recycled.",
    },
    "polyurethane": {
        "tier": "low",
        "score": 20,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Petroleum-based; often marketed as 'vegan leather' but not sustainable.",
    },
    "polyurethane (pu)": {
        "tier": "low",
        "score": 20,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Same as polyurethane.",
    },
    "pvc": {
        "tier": "low",
        "score": 5,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Releases dioxins during production; non-recyclable; the worst synthetic.",
    },
    "elastane": {
        "tier": "low",
        "score": 20,
        "water": "low",
        "carbon": "medium",
        "category": "synthetic_virgin",
        "notes": "Petroleum-based stretch fiber; makes garments harder to recycle.",
    },
    "spandex": {
        "tier": "low",
        "score": 20,
        "water": "low",
        "carbon": "medium",
        "category": "synthetic_virgin",
        "notes": "Same as elastane.",
    },
    "acetate": {
        "tier": "low",
        "score": 25,
        "water": "medium",
        "carbon": "medium",
        "category": "semi_synthetic",
        "notes": "Wood pulp derived but chemically intensive process.",
    },
    "polypropylene": {
        "tier": "low",
        "score": 15,
        "water": "low",
        "carbon": "high",
        "category": "synthetic_virgin",
        "notes": "Petroleum-based; commonly used in disposable products.",
    },
}


# ──────────────────────────────────────────
# Certification Authority Database
# tier: "gold" (highest credibility), "silver" (well-recognized), "bronze" (emerging)
# ──────────────────────────────────────────

CERTIFICATION_DATABASE = {
    # Gold Standard (10 pts)
    "gots": {
        "full_name": "Global Organic Textile Standard",
        "tier": "gold", "points": 10,
        "covers": ["materials", "labor"],
        "url": "https://global-standard.org",
    },
    "fair trade": {
        "full_name": "Fair Trade Certified",
        "tier": "gold", "points": 10,
        "covers": ["labor", "community"],
        "url": "https://www.fairtrade.net",
    },
    "fairtrade": {
        "full_name": "Fairtrade International",
        "tier": "gold", "points": 10,
        "covers": ["labor", "community"],
        "url": "https://www.fairtrade.net",
    },
    "b-corp": {
        "full_name": "B Corporation",
        "tier": "gold", "points": 10,
        "covers": ["governance", "labor", "environment"],
        "url": "https://www.bcorporation.net",
    },
    "b corp": {
        "full_name": "B Corporation",
        "tier": "gold", "points": 10,
        "covers": ["governance", "labor", "environment"],
        "url": "https://www.bcorporation.net",
    },
    "cradle to cradle": {
        "full_name": "Cradle to Cradle Certified",
        "tier": "gold", "points": 10,
        "covers": ["materials", "circularity"],
        "url": "https://www.c2ccertified.org",
    },
    "sa8000": {
        "full_name": "Social Accountability 8000",
        "tier": "gold", "points": 10,
        "covers": ["labor"],
        "url": "https://sa-intl.org",
    },

    # Silver Standard (5 pts)
    "oeko-tex": {
        "full_name": "OEKO-TEX Standard 100",
        "tier": "silver", "points": 5,
        "covers": ["chemical_safety"],
        "url": "https://www.oeko-tex.com",
    },
    "oeko-tex standard 100": {
        "full_name": "OEKO-TEX Standard 100",
        "tier": "silver", "points": 5,
        "covers": ["chemical_safety"],
        "url": "https://www.oeko-tex.com",
    },
    "bluesign": {
        "full_name": "Bluesign System",
        "tier": "silver", "points": 5,
        "covers": ["chemical_safety", "environment"],
        "url": "https://www.bluesign.com",
    },
    "grs": {
        "full_name": "Global Recycled Standard",
        "tier": "silver", "points": 5,
        "covers": ["materials", "recycled_content"],
        "url": "https://textileexchange.org",
    },
    "global recycled standard": {
        "full_name": "Global Recycled Standard",
        "tier": "silver", "points": 5,
        "covers": ["materials", "recycled_content"],
        "url": "https://textileexchange.org",
    },
    "rcs": {
        "full_name": "Recycled Claim Standard",
        "tier": "silver", "points": 5,
        "covers": ["materials", "recycled_content"],
        "url": "https://textileexchange.org",
    },
    "recycled claim standard": {
        "full_name": "Recycled Claim Standard",
        "tier": "silver", "points": 5,
        "covers": ["materials", "recycled_content"],
        "url": "https://textileexchange.org",
    },
    "rws": {
        "full_name": "Responsible Wool Standard",
        "tier": "silver", "points": 5,
        "covers": ["animal_welfare", "land_management"],
        "url": "https://textileexchange.org",
    },
    "responsible wool standard": {
        "full_name": "Responsible Wool Standard",
        "tier": "silver", "points": 5,
        "covers": ["animal_welfare", "land_management"],
        "url": "https://textileexchange.org",
    },
    "fsc": {
        "full_name": "Forest Stewardship Council",
        "tier": "silver", "points": 5,
        "covers": ["forestry", "materials"],
        "url": "https://fsc.org",
    },
    "eu ecolabel": {
        "full_name": "EU Ecolabel",
        "tier": "silver", "points": 5,
        "covers": ["environment"],
        "url": "https://ec.europa.eu/environment/ecolabel",
    },

    # Bronze Standard (3 pts)
    "wrap": {
        "full_name": "Worldwide Responsible Accredited Production",
        "tier": "bronze", "points": 3,
        "covers": ["labor"],
        "url": "https://wrapcompliance.org",
    },
    "climatepartner": {
        "full_name": "ClimatePartner Certified",
        "tier": "bronze", "points": 3,
        "covers": ["carbon"],
        "url": "https://www.climatepartner.com",
    },
    "climate partner": {
        "full_name": "ClimatePartner Certified",
        "tier": "bronze", "points": 3,
        "covers": ["carbon"],
        "url": "https://www.climatepartner.com",
    },
    "ocs": {
        "full_name": "Organic Content Standard",
        "tier": "bronze", "points": 3,
        "covers": ["materials"],
        "url": "https://textileexchange.org",
    },
    "organic content standard": {
        "full_name": "Organic Content Standard",
        "tier": "bronze", "points": 3,
        "covers": ["materials"],
        "url": "https://textileexchange.org",
    },
}


def lookup_material(name: str) -> dict:
    """
    Look up a material by canonical name.
    Returns the material data or a default 'unknown' entry.
    """
    key = name.strip().lower()
    if key in MATERIAL_DATABASE:
        return MATERIAL_DATABASE[key]

    # Fuzzy matching: check if the material name contains a known key
    for db_key, data in MATERIAL_DATABASE.items():
        if db_key in key or key in db_key:
            return data

    return {
        "tier": "low",
        "score": 20,
        "water": "medium",
        "carbon": "medium",
        "category": "unknown",
        "notes": f"Material '{name}' not found in database; defaulting to low tier.",
    }


def lookup_certification(name: str) -> dict:
    """
    Look up a certification by name.
    Returns the certification data or None if not recognized.
    """
    key = name.strip().lower()
    if key in CERTIFICATION_DATABASE:
        return CERTIFICATION_DATABASE[key]

    # Fuzzy matching
    for db_key, data in CERTIFICATION_DATABASE.items():
        if db_key in key or key in db_key:
            return data

    return None
