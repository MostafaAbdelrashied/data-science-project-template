from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base_model import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "chat"}

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)

    chats = relationship("Chat", back_populates="user")
