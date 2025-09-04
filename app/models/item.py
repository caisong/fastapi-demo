"""
Example Item model
"""
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Item(Base):
    """Item model - example entity"""
    
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    owner = relationship("User", back_populates="items")

    def __repr__(self):
        return f"<Item(id={self.id}, title='{self.title}')>"


# Add the reverse relationship to User model
from app.models.user import User
User.items = relationship("Item", back_populates="owner")