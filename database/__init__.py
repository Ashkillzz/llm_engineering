"""
Persistence and ORM layer for Online Deal Scouter.
"""

from database.connection import close_db_session, get_db_session, init_db, SessionLocal, engine
from database.models import Base, DealModel, OpportunityModel

__all__ = [
    "Base",
    "DealModel",
    "OpportunityModel",
    "init_db",
    "get_db_session",
    "close_db_session",
    "SessionLocal",
    "engine",
]
