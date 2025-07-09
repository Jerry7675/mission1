# mission1/backend/app/db/schemas.py

from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class DebateSession(Base):
    __tablename__ = "debate_sessions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    verdict = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    rounds = relationship("DebateRound", back_populates="session")


class DebateRound(Base):
    __tablename__ = "debate_rounds"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("debate_sessions.id"))
    round_number = Column(Integer)
    agent = Column(String)  # 'Mistral' or 'Gemma'
    response = Column(Text)

    session = relationship("DebateSession", back_populates="rounds")
