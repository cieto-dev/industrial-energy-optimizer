"""
Database models.

Currently contains only the User table, used for authentication.
Other domain tables live in decision_engine/ or elsewhere and are
not SQLAlchemy models (yet).
"""

from sqlalchemy import Column, Integer, String, Boolean

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)