"""
EcoScan Database Models (SQLAlchemy)
Persistent storage for analysis results, feedback, and analytics.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    JSON,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────
# Product Analysis Cache
# ──────────────────────────────────────────
class ProductAnalysis(Base):
    """Stores cached analysis results to avoid redundant LLM calls."""
    __tablename__ = "product_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_url_hash = Column(String(64), unique=True, index=True, nullable=False)
    product_url = Column(Text, nullable=False)
    brand_name = Column(String(255), nullable=True)
    product_name = Column(String(500), nullable=True)

    # Scores
    base_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=True)
    grade = Column(String(2), nullable=True)
    gwr_index = Column(Float, nullable=True)
    gwr_level = Column(String(10), nullable=True)

    # Full LLM response stored as JSON
    llm_result_json = Column(JSON, nullable=True)
    scoring_result_json = Column(JSON, nullable=True)

    # Metadata
    llm_model = Column(String(50), nullable=True)
    analysis_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ProductAnalysis(url_hash={self.product_url_hash}, score={self.final_score})>"


# ──────────────────────────────────────────
# User Feedback
# ──────────────────────────────────────────
class Feedback(Base):
    """Stores user feedback on analysis results for continuous improvement."""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(36), unique=True, index=True, nullable=False)
    product_url = Column(Text, nullable=False)
    feedback_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    expected_score = Column(Float, nullable=True)
    user_id_hash = Column(String(64), nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Feedback(id={self.feedback_id}, type={self.feedback_type})>"


# ──────────────────────────────────────────
# Analysis History (Analytics / Audit Log)
# ──────────────────────────────────────────
class AnalysisLog(Base):
    """Tracks every scan event for analytics and rate limiting."""
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_url_hash = Column(String(64), index=True, nullable=False)
    user_id_hash = Column(String(64), nullable=True)
    was_cached = Column(Boolean, default=False)
    duration_ms = Column(Integer, nullable=True)
    final_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AnalysisLog(url_hash={self.product_url_hash}, cached={self.was_cached})>"


# ──────────────────────────────────────────
# Brand Profile (Phase 6)
# ──────────────────────────────────────────
class BrandProfile(Base):
    """
    Persistent brand-level ethical ratings.
    Tracks rolling averages across all scanned products for a brand.
    """
    __tablename__ = "brand_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_name_normalized = Column(String(255), unique=True, index=True, nullable=False)
    brand_name_display = Column(String(255), nullable=False)

    # Rolling averages (updated on every scan)
    avg_final_score = Column(Float, default=0.0)
    avg_materials_score = Column(Float, default=0.0)
    avg_certifications_score = Column(Float, default=0.0)
    avg_transparency_score = Column(Float, default=0.0)
    avg_ethics_score = Column(Float, default=0.0)
    avg_gwr_index = Column(Float, default=0.0)

    # Stats
    total_products_scanned = Column(Integer, default=0)
    best_score = Column(Float, default=0.0)
    worst_score = Column(Float, default=100.0)
    most_common_grade = Column(String(2), nullable=True)

    # Reputation
    overall_grade = Column(String(2), nullable=True)
    risk_level = Column(String(10), default="unknown")  # low, medium, high, unknown

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BrandProfile(brand={self.brand_name_display}, grade={self.overall_grade}, products={self.total_products_scanned})>"


# ──────────────────────────────────────────
# Product Category Tags (Phase 6)
# ──────────────────────────────────────────
class ProductCategory(Base):
    """
    Stores category tags for analyzed products.
    Powers the Alternative Product Engine by enabling same-category lookups.
    """
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_url_hash = Column(String(64), index=True, nullable=False)
    product_name = Column(String(500), nullable=True)
    brand_name = Column(String(255), nullable=True)
    category = Column(String(100), index=True, nullable=False)  # e.g., "dresses", "t-shirts"
    final_score = Column(Float, nullable=True)
    grade = Column(String(2), nullable=True)
    product_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ProductCategory(name={self.product_name}, category={self.category}, score={self.final_score})>"


# ──────────────────────────────────────────
# Database Engine & Session Factory
# ──────────────────────────────────────────
def get_engine(database_url: str = "sqlite:///./ecoscan.db"):
    """Create a database engine. Uses SQLite by default for development."""
    return create_engine(database_url, echo=False)


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_session_factory(engine) -> sessionmaker:
    """Return a session factory bound to the given engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)
