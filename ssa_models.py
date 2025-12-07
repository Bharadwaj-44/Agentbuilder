"""
SQLAlchemy models for database tables
"""
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime, Integer, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship

from app.database.database import Base

class User(Base):
    """Users table"""
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    date_created = Column(DateTime, default=datetime.utcnow)
    date_updated = Column(DateTime, nullable=True)
    date_expired = Column(DateTime, nullable=True)
    group_id = Column(Text, nullable=True)
    current_login_date = Column(TIMESTAMP, nullable=True)
    last_login_date = Column(TIMESTAMP, nullable=True)


class UserAgent(Base):
    """User Agent mapping table"""
    __tablename__ = "user_agent"
    
    agent_uuid = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent_details = relationship("AgentDetails", back_populates="user_agent", uselist=False)
    tools = relationship("ToolDetails", back_populates="user_agent")


class AgentDetails(Base):
    """Agent details table"""
    __tablename__ = "agent_details"
    
    agent_id = Column(String, ForeignKey("user_agent.agent_uuid"), primary_key=True, index=True)
    agent_json = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_agent = relationship("UserAgent", back_populates="agent_details")


class ToolDetails(Base):
    """Tool details table"""
    __tablename__ = "tool_details"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("user_agent.agent_uuid"), nullable=False, index=True)
    tool_json = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_agent = relationship("UserAgent", back_populates="tools")


class SnowflakeCortexLLM(Base):
    """Snowflake Cortex LLMs table"""
    __tablename__ = "snowflake_cortex_llms"
    
    model_id = Column(String, primary_key=True, index=True)
    model_name = Column(String, nullable=False)