from sqlalchemy import Column, Integer, String, BigInteger
from .session import Base

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    item_id = Column(Integer, index=True)
    timestamp = Column(BigInteger)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    category = Column(String(100))