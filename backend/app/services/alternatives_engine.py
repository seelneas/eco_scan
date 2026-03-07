"""
EcoScan Alternative Product Engine (Phase 6)
When a product scores low, suggests "Better Alternatives" from the same category.

Strategy:
1. Infer a product category from the product name (using keyword mapping).
2. Store category tags in the database alongside product scores.
3. When queried, find higher-scoring products in the same category.
"""

import re
import hashlib
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.database import ProductCategory
from app.models.schemas import ScoringResult

logger = logging.getLogger("ecoscan.alternatives")


# ──────────────────────────────────────────
# Category Inference
# ──────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "t-shirts": ["t-shirt", "tee", "tshirt", "t shirt", "crewneck", "v-neck"],
    "dresses": ["dress", "gown", "maxi", "midi dress", "mini dress", "sundress"],
    "jeans": ["jeans", "denim", "skinny jeans", "straight leg", "bootcut"],
    "pants": ["pants", "trousers", "chinos", "slacks", "joggers", "sweatpants"],
    "jackets": ["jacket", "coat", "blazer", "parka", "windbreaker", "bomber", "anorak"],
    "sweaters": ["sweater", "pullover", "cardigan", "knit", "hoodie", "sweatshirt"],
    "shirts": ["shirt", "blouse", "button-down", "oxford", "flannel", "polo"],
    "skirts": ["skirt", "miniskirt", "midi skirt", "maxi skirt"],
    "shorts": ["shorts", "bermuda", "cargo shorts"],
    "activewear": ["leggings", "sports bra", "activewear", "yoga", "athletic", "gym wear", "workout"],
    "underwear": ["underwear", "boxers", "briefs", "bra", "panties", "lingerie", "socks"],
    "shoes": ["shoes", "sneakers", "boots", "sandals", "loafers", "heels", "flats", "trainers"],
    "bags": ["bag", "backpack", "tote", "purse", "handbag", "wallet", "clutch"],
    "accessories": ["hat", "scarf", "belt", "gloves", "sunglasses", "jewelry", "watch", "tie"],
    "swimwear": ["swimsuit", "bikini", "swim trunks", "one-piece", "swimwear", "bathing suit"],
    "outerwear": ["raincoat", "trench coat", "vest", "fleece", "down jacket", "puffer"],
}


def infer_category(product_name: str) -> str:
    """
    Infer a product category from its name using keyword matching.
    Returns a normalized category string.
    """
    if not product_name:
        return "uncategorized"

    name_lower = product_name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category

    return "uncategorized"


# ──────────────────────────────────────────
# Store Product Category
# ──────────────────────────────────────────
def store_product_category(
    db: Session,
    product_url: str,
    scoring_result: ScoringResult,
):
    """
    Tag and store a product's category in the database.
    Called after every successful analysis.
    """
    product_name = scoring_result.llm_analysis.product.name or "Unknown"
    brand_name = scoring_result.llm_analysis.product.brand
    category = infer_category(product_name)
    url_hash = hashlib.sha256(product_url.strip().lower().encode()).hexdigest()

    if category == "uncategorized":
        logger.debug(f"Could not categorize: {product_name}")
        return

    # Check if entry already exists
    existing = (
        db.query(ProductCategory)
        .filter(ProductCategory.product_url_hash == url_hash)
        .first()
    )

    if existing:
        existing.final_score = scoring_result.final_score
        existing.grade = scoring_result.grade
        existing.category = category
        logger.debug(f"Category updated: {product_name} → {category}")
    else:
        entry = ProductCategory(
            product_url_hash=url_hash,
            product_name=product_name,
            brand_name=brand_name,
            category=category,
            final_score=scoring_result.final_score,
            grade=scoring_result.grade,
            product_url=product_url,
        )
        db.add(entry)
        logger.info(f"Category stored: {product_name} → {category} (score: {scoring_result.final_score})")

    db.commit()


# ──────────────────────────────────────────
# Find Better Alternatives
# ──────────────────────────────────────────
def find_alternatives(
    db: Session,
    product_url: str,
    product_name: str,
    current_score: float,
    limit: int = 5,
) -> list[dict]:
    """
    Find higher-scoring products in the same category.

    Logic:
    1. Infer the current product's category.
    2. Query the database for products in the same category with a HIGHER score.
    3. Exclude the current product itself.
    4. Return top N results sorted by score descending.
    """
    category = infer_category(product_name)

    if category == "uncategorized":
        return []

    url_hash = hashlib.sha256(product_url.strip().lower().encode()).hexdigest()

    alternatives = (
        db.query(ProductCategory)
        .filter(
            ProductCategory.category == category,
            ProductCategory.final_score > current_score,
            ProductCategory.product_url_hash != url_hash,
        )
        .order_by(ProductCategory.final_score.desc())
        .limit(limit)
        .all()
    )

    results = []
    for alt in alternatives:
        results.append({
            "product_name": alt.product_name,
            "brand": alt.brand_name,
            "score": alt.final_score,
            "grade": alt.grade,
            "category": alt.category,
            "product_url": alt.product_url,
            "score_improvement": round(alt.final_score - current_score, 1),
        })

    if results:
        logger.info(
            f"Found {len(results)} better alternatives for '{product_name}' "
            f"(category: {category}, current score: {current_score})"
        )
    else:
        logger.debug(f"No better alternatives found for '{product_name}' in category '{category}'")

    return results
