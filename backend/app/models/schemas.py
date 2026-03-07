"""
EcoScan Pydantic Schemas
Data models for API request/response validation and LLM output parsing.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


# ──────────────────────────────────────────
# Enums
# ──────────────────────────────────────────
class ImpactTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GreenwashingRisk(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SupplyChainDepth(str, Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"
    NONE = "none"


class GWRLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FeedbackType(str, Enum):
    INCORRECT_MATERIAL = "incorrect_material"
    MISSING_CERTIFICATION = "missing_certification"
    WRONG_SCORE = "wrong_score"
    FALSE_GREENWASHING_FLAG = "false_greenwashing_flag"
    MISSED_GREENWASHING = "missed_greenwashing"
    TECHNICAL_ERROR = "technical_error"
    OTHER = "other"


# ──────────────────────────────────────────
# API Requests
# ──────────────────────────────────────────
class ProductAnalysisRequest(BaseModel):
    """Incoming request from the Chrome Extension."""
    product_url: str = Field(..., description="The URL of the product page")
    product_text: str = Field(
        ...,
        description="Extracted text content from the product page",
        min_length=10,
        max_length=15000,
    )
    brand_name: Optional[str] = Field(None, description="Brand name if extracted separately")
    user_id_hash: Optional[str] = Field(None, description="Anonymized user identifier")


class FeedbackRequest(BaseModel):
    """User feedback on an analysis result."""
    product_url: str = Field(..., description="The URL of the analyzed product")
    feedback_type: FeedbackType = Field(..., description="Category of the feedback")
    message: str = Field(
        ...,
        description="Detailed description of the issue",
        min_length=5,
        max_length=2000,
    )
    expected_score: Optional[float] = Field(
        None,
        description="What score the user believes is correct (0-100)",
        ge=0,
        le=100,
    )
    user_id_hash: Optional[str] = Field(
        None,
        description="Anonymized user identifier from the extension",
    )


# ──────────────────────────────────────────
# LLM Output Sub-Models
# ──────────────────────────────────────────
class ProductInfo(BaseModel):
    name: Optional[str] = Field(default="Unknown Product")
    brand: Optional[str] = None


class MaterialEntry(BaseModel):
    name: str
    percentage: Optional[int] = None
    impact_tier: ImpactTier = ImpactTier.MEDIUM


class CertificationEntry(BaseModel):
    name: str
    standard: str
    is_third_party: bool
    evidence_snippet: str


class VerifiableClaim(BaseModel):
    claim: str
    supporting_evidence: str


class VagueBuzzword(BaseModel):
    word: str
    context: str
    reason: str
    greenwashing_risk: GreenwashingRisk = GreenwashingRisk.MEDIUM


class SustainabilityClaims(BaseModel):
    verifiable: list[VerifiableClaim] = []
    vague_buzzwords: list[VagueBuzzword] = []


class TransparencySignals(BaseModel):
    factory_disclosed: bool = False
    factory_name: Optional[str] = None
    country_of_manufacture: Optional[str] = None
    supply_chain_depth: SupplyChainDepth = SupplyChainDepth.NONE


class EthicalSignals(BaseModel):
    living_wage_commitment: bool = False
    take_back_program: bool = False
    carbon_neutral_claim: bool = False
    carbon_neutral_verified: bool = False


class LLMAnalysisResult(BaseModel):
    """The full structured output expected from the LLM."""
    product: ProductInfo
    materials: list[MaterialEntry] = []
    certifications: list[CertificationEntry] = []
    sustainability_claims: SustainabilityClaims = SustainabilityClaims()
    transparency: TransparencySignals = TransparencySignals()
    ethical_signals: EthicalSignals = EthicalSignals()
    analysis_notes: Optional[str] = None


# ──────────────────────────────────────────
# Scoring Output
# ──────────────────────────────────────────
class CategoryScore(BaseModel):
    category: str
    score: float
    max_score: float
    details: str


class ClaimVerification(BaseModel):
    claim: str
    is_supported: bool
    evidence: str
    source: str  # "certification", "material_data", "transparency", "none"


class GreenwashingReport(BaseModel):
    vague_claims_count: int
    verifiable_evidence_count: int
    gwr_index: float
    risk_level: GWRLevel
    penalty_percent: int
    flagged_terms: list[VagueBuzzword] = []
    unsupported_claims: list[ClaimVerification] = []


class ScoringResult(BaseModel):
    """The final computed sustainability analysis returned to the extension."""
    base_score: float
    final_score: float
    grade: str  # A, B, C, D, F
    category_scores: list[CategoryScore]
    greenwashing_report: GreenwashingReport
    llm_analysis: LLMAnalysisResult


# ──────────────────────────────────────────
# API Responses
# ──────────────────────────────────────────
class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process itself."""
    analysis_duration_ms: int = Field(..., description="How long the analysis took in milliseconds")
    llm_model: str = Field(..., description="Which LLM model was used")
    cached: bool = Field(False, description="Whether this result was served from cache")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ProductAnalysisResponse(BaseModel):
    """The full API response sent back to the Chrome Extension."""
    success: bool
    product_url: str
    scoring: Optional[ScoringResult] = None
    metadata: Optional[AnalysisMetadata] = None
    brand_profile: Optional["BrandProfileResponse"] = None
    alternatives: list["AlternativeProduct"] = []
    error: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    success: bool
    feedback_id: str
    message: str


class HealthResponse(BaseModel):
    """Structured health check response."""
    status: str
    service: str
    version: str
    environment: str
    llm_model: str
    uptime_seconds: float
    total_analyses: int
    total_feedbacks: int


# ──────────────────────────────────────────
# Phase 6: Brand & Alternatives Schemas
# ──────────────────────────────────────────
class BrandProfileResponse(BaseModel):
    """Brand-level ethical profile returned in API responses."""
    brand_name: str
    avg_final_score: float
    avg_materials_score: float
    avg_certifications_score: float
    avg_transparency_score: float
    avg_ethics_score: float
    avg_gwr_index: float
    total_products_scanned: int
    best_score: float
    worst_score: float
    overall_grade: Optional[str] = None
    most_common_grade: Optional[str] = None
    risk_level: str = "unknown"


class AlternativeProduct(BaseModel):
    """A higher-scoring product suggested as an alternative."""
    product_name: str
    brand: Optional[str] = None
    score: float
    grade: str
    category: str
    product_url: str
    score_improvement: float


class BrandListResponse(BaseModel):
    """Response for listing all tracked brands."""
    success: bool
    total_brands: int
    brands: list[BrandProfileResponse]

