"""
Database models and connection management for The Price is Right application.
Uses SQLAlchemy ORM with PostgreSQL for persistent storage of deals and opportunities.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/price_is_right")

# Create engine with connection pooling for better scalability
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using them
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DealModel(Base):
    """ORM model for Deal data"""
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    product_description = Column(String(1024), nullable=False)
    price = Column(Float, nullable=False, index=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship to opportunities
    opportunities = relationship("OpportunityModel", back_populates="deal", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "product_description": self.product_description,
            "price": self.price,
            "url": self.url,
        }


class OpportunityModel(Base):
    """ORM model for Opportunity data"""
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    estimate = Column(Float, nullable=False, index=True)
    discount = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship to deal
    deal = relationship("DealModel", back_populates="opportunities")
    
    # Index for efficient sorting by discount
    __table_args__ = (
        Index('idx_discount_desc', discount.desc()),
    )

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "deal": self.deal.to_dict(),
            "estimate": self.estimate,
            "discount": self.discount,
        }


def init_db():
    """Initialize the database tables"""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get a database session"""
    return SessionLocal()


def close_db_session(session):
    """Close a database session"""
    session.close()
