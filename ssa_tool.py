"""
CRUD operations for tools
"""
import json
from typing import List
from sqlalchemy.orm import Session

from app.database.data_classes.ssa_models import ToolDetails
from app.api.schemas.ssa_api_schemas import ToolConfig


def create_tool(db: Session, agent_uuid: str, tool: ToolConfig) -> ToolDetails:
    """
    Add a tool to an agent
    """
    tool_json = json.dumps(tool.model_dump()).encode()
    
    db_tool = ToolDetails(
        agent_id=agent_uuid,
        tool_json=tool_json
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool


# For future use
def get_tools_by_agent(db: Session, agent_uuid: str) -> List[dict]:
    """
    Get all tools for a specific agent
    """
    tools = db.query(ToolDetails).filter(ToolDetails.agent_id == agent_uuid).all()
    return [json.loads(tool.tool_json.decode()) for tool in tools]


# For future use
def delete_tool(db: Session, tool_id: int) -> bool:
    """
    Delete a specific tool
    """
    tool = db.query(ToolDetails).filter(ToolDetails.id == tool_id).first()
    if tool:
        db.delete(tool)
        db.commit()
        return True
    return False


def delete_all_tools_by_agent(db: Session, agent_uuid: str) -> int:
    """
    Delete all tools for a specific agent
    Returns number of deleted tools
    """
    count = db.query(ToolDetails).filter(ToolDetails.agent_id == agent_uuid).delete()
    db.commit()
    return count