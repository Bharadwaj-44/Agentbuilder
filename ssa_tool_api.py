"""
Tool endpoints
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database.crud import ssa_agent as agent_crud
from app.database.crud import ssa_tool as tool_crud
from app.api.schemas.ssa_api_schemas import ToolConfig, ToolResponse, ToolConfigRequest
from app.utils.yaml_generator import update_tool_yaml
from app.config import SSA_AGENTS_DIR

router = APIRouter()


@router.post("/{agent_uuid}/tools", response_model=ToolResponse)
def add_tool(
    agent_uuid: str,
    tool: ToolConfig,
    db: Session = Depends(get_db)
):
    """
    Add tools and tool resources to an agent
    - Processes tool_choice, tools, and tool_resources from frontend
    - Saves to new configuration tables
    - Updates tool.yaml
    """
    try:
        # Verify agent exists
        # agent = agent_crud.get_agent(db, agent_uuid)
        # if not agent:
        #     raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent folder exists, create if it doesn't
        agent_folder = os.path.join(SSA_AGENTS_DIR, agent_uuid)
        if not os.path.exists(agent_folder):
            os.makedirs(agent_folder, exist_ok=True)
            # Create the source directory structure as well
            source_dir = os.path.join(agent_folder, "source")
            os.makedirs(source_dir, exist_ok=True)
        
        # Process and save each tool configuration
        created_tools = []
        for tool_d in tool.tools:
            # Create tool configuration
            tool_obj = tool_crud.create_tool_config(
                db=db,
                agnt_id=agent_uuid,
                sesn_id=tool.sesn_id,
                db_nm=tool_d.db_name,
                schma_nm=tool_d.input_schema,
                tool_nm=tool_d.name,
                tool_desc=tool_d.description,
                tool_config={
                    "type": tool_d.type,
                    "tool_choice": tool.tool_choice.model_dump() if tool.tool_choice else None
                }
            )
            created_tools.append(tool_obj)
        for tool_d, v in tool.tool_resources.items():    
            # Process tool resources if they exist for this tool
            if tool.tool_resources and tool_d in tool.tool_resources:
                tool_resource = tool.tool_resources[tool_d]
                
                # Create tool resource configuration
                tool_crud.create_tool_resource_config(
                    db=db,
                    agnt_id=agent_uuid,
                    tool_nm=tool_d,
                    tool_desc="",
                    tool_config=tool.tool_resources[tool_d],
                    sesn_id=tool.sesn_id,
                    db_nm=tool_resource.db_name or "default_db",
                    schma_nm="default_schema",
                    rsrc_config=tool_resource.model_dump()
                )

        # Save original tool config to legacy table for backward compatibility
        # tool_crud.create_tool(db, agent_uuid, request.tool_config)

        # Get agent name from DB
        agent_details = agent_crud.get_agent_details(db, agent_uuid)
        if agent_details:
            agent_name = agent_details.get("agent_name", "default_agent").lower().replace(" ", "_")
        else:
            # If no agent details found, use default agent name
            agent_name = "default_agent"

        # Path to agent_name subfolder
        agent_name_folder = os.path.join(agent_folder, "source", agent_name)
        # Create agent_name subfolder if it doesn't exist
        os.makedirs(agent_name_folder, exist_ok=True)
        
        # Update tool.yaml
        update_tool_yaml(agent_name_folder, tool, agent_name)
        
        return ToolResponse(
            message=f"Successfully added {len(created_tools)} tools with resources",
            agent_uuid=agent_uuid
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
