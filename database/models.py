from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DealModel(Base):
    """SQLAlchemy ORM model for scraped Deal records."""
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    product_description = Column(String(1024), nullable=False)
    price = Column(Float, nullable=False, index=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    opportunities = relationship("OpportunityModel", back_populates="deal", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "product_description": self.product_description,
            "price": self.price,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OpportunityModel(Base):
    """SQLAlchemy ORM model for detected high-margin discount opportunities."""
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    estimate = Column(Float, nullable=False, index=True)
    discount = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    deal = relationship("DealModel", back_populates="opportunities")

    __table_args__ = (
        Index('idx_discount_desc', discount.desc()),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "deal": self.deal.to_dict() if self.deal else None,
            "estimate": self.estimate,
            "discount": self.discount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
