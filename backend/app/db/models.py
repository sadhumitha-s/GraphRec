from sqlalchemy import Column, Integer, String, BigInteger, LargeBinary, DateTime
from sqlalchemy.sql import func
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

class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    genre_id = Column(Integer)

class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    # This column stores the actual 'graph.bin' file content
    binary_data = Column(LargeBinary) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())