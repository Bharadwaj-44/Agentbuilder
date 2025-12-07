"""
CRUD operations for agents
"""
import json
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session

from app.database.data_classes.ssa_models import UserAgent, AgentDetails
from app.api.schemas.ssa_api_schemas import AgentCreate, AgentConfig


def create_agent(db: Session, agent: AgentCreate) -> UserAgent:
    """
    Create a new agent with UUID
    """
    agent_uuid = str(uuid.uuid4())
    db_agent = UserAgent(
        agent_uuid=agent_uuid,
        user_id=agent.user_id
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_uuid: str) -> Optional[UserAgent]:
    """
    Get agent by UUID
    """
    return db.query(UserAgent).filter(UserAgent.agent_uuid == agent_uuid).first()


def create_agent_details(db: Session, agent_uuid: str, details: AgentConfig) -> AgentDetails:
    """
    Create or update agent details
    """
    agent_json = json.dumps(details.model_dump(by_alias=True)).encode()
    
    # Check if details already exist
    existing = db.query(AgentDetails).filter(AgentDetails.agent_id == agent_uuid).first()
    
    if existing:
        # Update existing
        existing.agent_json = agent_json
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        db_details = AgentDetails(
            agent_id=agent_uuid,
            agent_json=agent_json
        )
        db.add(db_details)
        db.commit()
        db.refresh(db_details)
        return db_details
    

# For future use
def get_agents_by_user(db: Session, user_id: str) -> List[UserAgent]:
    """
    Get all agents for a specific user
    """
    return db.query(UserAgent).filter(UserAgent.user_id == user_id).all()


# For future use
def get_all_agents(db: Session, skip: int = 0, limit: int = 100) -> List[UserAgent]:
    """
    Get all agents with pagination
    """
    return db.query(UserAgent).offset(skip).limit(limit).all()


def get_agent_details(db: Session, agent_uuid: str) -> Optional[dict]:
    """
    Get agent details as dictionary
    """
    details = db.query(AgentDetails).filter(AgentDetails.agent_id == agent_uuid).first()
    if details:
        return json.loads(details.agent_json.decode())
    return None


# For future use
def delete_agent(db: Session, agent_uuid: str) -> bool:
    """
    Delete an agent and all related data
    """
    agent = get_agent(db, agent_uuid)
    if agent:
        db.delete(agent)
        db.commit()
        return True
    return False