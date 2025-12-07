"""
SQLAlchemy models for database tables
"""
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime, Integer, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship

from app.database.database import Base


class LLMProvider(Base):
    """LLM Provider table (e.g., Snowflake Cortex, OpenAI, Google Gemini)"""
    __tablename__ = "llm_provider"

    provider_id = Column(String, primary_key=True, index=True)
    provider_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    llms = relationship("LLMModel", back_populates="provider")


class LLMModel(Base):
    """LLM Model table — linked to provider"""
    __tablename__ = "llm_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String, nullable=False, unique=True, index=True)
    model_name = Column(String, nullable=False)
    provider_id = Column(String, ForeignKey("llm_provider.provider_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    provider = relationship("LLMProvider", back_populates="llms")
    agent_profiles = relationship("LangGraphAgentProfile", back_populates="llm_model")


class LangGraphAgent(Base):
    """LangGraph Agent mapping table"""
    __tablename__ = "langgraph_agent"
    
    agent_uuid = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent_profile = relationship(
        "LangGraphAgentProfile", 
        back_populates="langgraph_agent", 
        uselist=False
    )
    mcp_tools = relationship(
        "MCPTool", 
        back_populates="langgraph_agent"
    )
    memory_config = relationship(
        "MemoryConfigModel",
        back_populates="langgraph_agent",
        uselist=False
    )


class LangGraphAgentProfile(Base):
    """LangGraph Agent profile table"""
    __tablename__ = "langgraph_agent_profile"
    
    agent_id = Column(String, ForeignKey("langgraph_agent.agent_uuid"), primary_key=True, index=True)
    llm_model_id = Column(Integer, ForeignKey("llm_model.id"), nullable=True) 
    agent_json = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    langgraph_agent = relationship("LangGraphAgent", back_populates="agent_profile")
    llm_model = relationship("LLMModel", back_populates="agent_profiles")


class MCPTool(Base):
    """MCP Tool table"""
    __tablename__ = "mcp_tool"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("langgraph_agent.agent_uuid"), nullable=False, index=True)
    mcp_tool_json = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    langgraph_agent = relationship("LangGraphAgent", back_populates="mcp_tools")


class MemoryConfigModel(Base):
    """Agent Memory Configuration table"""
    __tablename__ = "memory_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("langgraph_agent.agent_uuid"), nullable=False, index=True)
    memory_config_json = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    langgraph_agent = relationship(
        "LangGraphAgent",
        back_populates="memory_config"
    )