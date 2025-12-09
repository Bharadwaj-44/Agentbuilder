"""
Agent endpoints
"""
import os

if not os.getenv('REQUESTS_CA_BUNDLE'):
    os.environ['REQUESTS_CA_BUNDLE'] = "agentbuilderbe/source/certs/cacert.pem"

os.environ['REQUESTS_CA_BUNDLE'] = "agentbuilderbe/source/certs/cacert.pem"

import shutil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db
from app.database.crud import ssa_agent as agent_crud
from app.database.crud import ssa_tool as tool_crud
from app.api.schemas.ssa_api_schemas import (
    AgentCreate,
    AgentResponse,
    AgentConfig,
    AgentRuntimeConfig,
    AgentDetailsResponse,
    AgentListResponse,
    MessageResponse,
    GenerateSnowflakeAgentResponse,
    DeployAgentResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    AgentConfigCreateRequest,
    AgentConfigCreateResponse
)
from app.utils.file_manager import (
    copy_template_to_agent_folder,
    create_agent_zip,
    cleanup_zip
)
from app.utils.yaml_generator import create_agent_yaml
from app.utils.template_renderer import write_rendered_template
from app.config import SSA_AGENTS_DIR, SSA_TEMPLATE_DIR, USERNAME, PASSWORD
# from agent_builder_deploy.my_service_deploy import deploy
from templates.ssa_template.source.agent_builder import create_agent
import os
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=AgentResponse)
def create_snowflake_agent(
    agent: AgentCreate
):
    """
    Create a new agent and return UUID
    """
    try:
        agent_uuid = str(uuid.uuid4())
        return AgentResponse(
            agent_uuid=agent_uuid,
            message="Agent created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_uuid}/configure", response_model=MessageResponse)
def configure_agent(
    agent_uuid: str,
    details: AgentConfigCreateRequest,
    db: Session = Depends(get_db)
):
    """
    a. Configure an agent
    b. Copy template folder
    c. Save to database
    d. Create agent.yaml
    """
    try:

        # Verify agent exists
        # agent = agent_crud.get_agent(db, agent_uuid)
        # if not agent:
        #     raise HTTPException(status_code=404, detail="Agent not found")
        
        # Extract agent name
        agent_name = details.agent_name.lower().replace(" ", "_") if details.agent_name else "default_agent"
        
        # Copy template folder and rename to agent_name
        agent_folder = copy_template_to_agent_folder(agent_uuid, agent_name)
        
        # Save to database
        # agent_crud.create_agent_details(db, agent_uuid, details)
        agent_crud.create_agent_config(
            db=db,
            agnt_id=agent_uuid,
            sesn_id=details.sesn_id,
            db_nm=details.db,
            schma_nm=details.schema,
            agnt_nm=details.agent_name,
            agnt_desc=details.description,
            orch_llm_prvdr=details.llm_config.orchestration,
            llm_nm=details.llm_config.orchestration,
            orch_config=details.orchestration_config.model_dump() if details.orchestration_config else None
        )

        # Path where YAMLs should be created (inside the renamed agent_name folder)
        agent_name_folder = os.path.join(agent_folder, "source", agent_name)
        
        # Create agent.yaml
        create_agent_yaml(agent_name_folder, details)

        logger.debug(f"agent.yaml created at {agent_name_folder}")
        
        return MessageResponse(
            message="Agent configured successfully",
            agent_uuid=agent_uuid
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_uuid}/download")
def download_agent(
    agent_uuid: str,
    db: Session = Depends(get_db)
):
    """
    a. Download agent code as ZIP
    b. Create zip
    c. Return zip file
    d. Cleanup handled by background task
    """
    try:
        # Verify agent exists
        agent = agent_crud.get_agent(db, agent_uuid)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent folder exists
        agent_folder = os.path.join(SSA_AGENTS_DIR, agent_uuid)
        if not os.path.exists(agent_folder):
            raise HTTPException(
                status_code=400,
                detail="Agent not configured yet. Please configure the agent first."
            )
        
        # Create zip file
        zip_path = create_agent_zip(agent_uuid)
        
        # Return zip file with cleanup
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"agent_{agent_uuid}.zip",
            background=lambda: cleanup_zip(zip_path)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_uuid}/runtime-configure", response_model=MessageResponse)
def configure_agent_runtime(
    agent_uuid: str,
    config: AgentRuntimeConfig,
    db: Session = Depends(get_db)
):
    """
    Configure the runtime file using the CAO_AGENT.py template
    by injecting db, schema, application_name, and user_identity values.
    """
    try:
        # Verify agent exists
        agent = agent_crud.get_agent(db, agent_uuid)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Prepare path and name
        agent_folder = os.path.join(SSA_AGENTS_DIR, agent_uuid)
        agent_name = config.agent_name.lower().replace(" ", "_") if config.agent_name else "default_agent"
        db_dev = config.db
        db_sit = config.db.replace("D01","T01")
        db_uat = config.db.replace("D01","U01")
        db_preprod = config.db.replace("D01","U01")
        db_prod = config.db.replace("D01","P01")
        yaml_replacements = {
            "agent_name": agent_name.upper(),
            "db_dev": db_dev,
            "db_sit": db_sit,
            "db_uat": db_uat,
            "db_preprod": db_preprod,
            "db_prod": db_prod,
            "schema": config.schema
        }

        output_yaml_path = write_rendered_template(
            template_dir=os.path.join(SSA_TEMPLATE_DIR, "source", "cao"),
            agent_folder=agent_folder,
            agent_name=agent_name,
            replacements=yaml_replacements,
            template_file="app.yaml",
            output_file="app.yaml",
        )

        # Replacements dictionary
        replacements = {
            "agent_name": agent_name.upper(),
            "application_name": str(config.application_name),
            "user_identity": str(config.user_identity),
            # "db": str(config.db),
            # "schema": str(config.schema)
        }

        # Use utility to render and write the agent file
        target_path = write_rendered_template(
            template_dir=os.path.join(SSA_TEMPLATE_DIR, "source", "cao"),
            agent_folder=agent_folder,
            agent_name=agent_name,
            replacements=replacements,
            template_file="CAO_AGENT.py",
            output_file=f"{agent_name.upper()}_AGENT.py",
        )

        # replacements = {
        #     "agent_name": agent_name.upper(),
        #     "application_name": str(config.application_name)
        #     # "db": str(config.db),
        #     # "schema": str(config.schema)
        # }

        # # Use utility to render and write the agent file
        # target_path = write_rendered_template(
        #     template_dir=os.path.join(SSA_TEMPLATE_DIR, "source"),
        #     agent_folder=agent_folder,
        #     agent_name=agent_name,
        #     replacements=replacements,
        #     template_file="cao_fastapi.py",
        #     output_file=f"{config.application_name.lower()}_fastapi.py",
        # )

        return MessageResponse(
            message=f"Runtime file '{os.path.basename(output_yaml_path)}' and '{os.path.basename(target_path)}' successfully generated.",
            agent_uuid=agent_uuid
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @router.post("/{agent_uuid}/generate_agent_in_snowflake", response_model=GenerateSnowflakeAgentResponse)
# def generate_agent_in_snowflake():
#     agent_url = "https://deniedyetpaidagent.edagenaipreprod.awsdns.internal.das/run_cao_agent"
#     return GenerateSnowflakeAgentResponse(agent_url=agent_url)


@router.post("/{agent_uuid}/generate_agent_in_snowflake", response_model=GenerateSnowflakeAgentResponse)
def generate_agent_in_snowflake(
    agent_uuid: str,
    db: Session = Depends(get_db)
):
    """
    Generate Snowflake Agent
    """
    logger.info(f"[START] generate_agent_in_snowflake called for agent_uuid={agent_uuid}")

    try:
        # Get agent details
        logger.debug("Fetching agent details from DB...")
        agent_details = agent_crud.get_agent_details(db, agent_uuid)

        if not agent_details:   
            logger.error(f"Agent not found for UUID={agent_uuid}")
            raise HTTPException(status_code=404, detail="Agent not found")
        
        logger.info(f"Agent details loaded: {agent_details}")

        # Step 1: Compute name
        try:
            agent_name = agent_details.get("agent_name", "").upper().replace(" ", "_")
            logger.debug(f"Parsed agent_name={agent_name}")
        except Exception as e:
            logger.error(f"ERROR computing agent_name: {e}")
            raise

        # Step 2: Compute folder
        try:
            agent_folder = os.path.join(SSA_AGENTS_DIR, agent_uuid, "source", agent_name.lower())
            logger.debug(f"Computed agent_folder path={agent_folder}")
            logger.debug(f"Folder exists? {os.path.exists(agent_folder)}")
        except Exception as e:
            logger.error(f"ERROR computing agent_folder: {e}")
            raise
        
        # agent_name = agent_details[agent_name].upper().replace(" ", "_")
        # agent_folder = os.path.join(SSA_AGENTS_DIR, agent_uuid, "source", agent_name.lower())

        logger.info(f"Computed agent_name: {agent_name}")
        logger.info(f"Agent folder path: {agent_folder}")

        # Check if folder exists
        if not os.path.exists(agent_folder):
            logger.warning(f"Agent folder does NOT exist: {agent_folder}")
        else:
            logger.debug(f"Agent folder exists: {agent_folder}")
        
        # Set environment variables for agent creation
        os.environ["GENAI_PATH"] = agent_folder
        os.environ["env_name"] = "dev"

        logger.info("Environment variables set:")
        logger.info(f"GENAI_PATH = {os.environ.get('GENAI_PATH')}")
        logger.info(f"env_name = {os.environ.get('env_name')}")

        # Create agent using the template function
        try:
            logger.info("Calling create_agent()...")
            success, agent_url = create_agent(agent_name)
            logger.debug(f"create_agent returned success={success}, agent_url={agent_url}")
        except Exception as e:
            logger.error(f"ERROR creating agent: {e}")
            raise

        if not success:
            logger.error("create_agent reported failure")
            raise HTTPException(status_code=500, detail="Failed to create agent in Snowflake")
        
        return GenerateSnowflakeAgentResponse(agent_url=agent_url)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# @router.post("/{agent_uuid}/deploy_agent", response_model=DeployAgentResponse)
# def deploy_agent(
#     agent_uuid: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Deploy agent to cloud service
#     """
#     try:
#         # Verify agent exists
#         agent = agent_crud.get_agent(db, agent_uuid)
#         if not agent:
#             raise HTTPException(status_code=404, detail="Agent not found")
        
#         # Path of zip file
#         zip_path = create_agent_zip(agent_uuid)

#         username = USERNAME.lower()
#         service_config = {
#             'service_name': agent_uuid,          
#             'environment': 'dev',                          
#             'container_port': 8080,                        
#             'cpu_limit': '500m',                           
#             'memory_limit': '1Gi',                         
#             'replicas': 2,                                 
#             'image_tag': 'latest',                         
#             'app_source_path': zip_path,    
#         }
#         git_credentials = {
#             'username': username,             
#             'password': PASSWORD     
#         }

#         # Deploy service
#         deployment_status = deploy(username, service_config, git_credentials)
        
#         return DeployAgentResponse(
#             agent_uuid=agent_uuid,
#             deployment_status=deployment_status
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# For future use
@router.get("/{agent_uuid}", response_model=AgentDetailsResponse)
def get_agent_details(
    agent_uuid: str,
    db: Session = Depends(get_db)
):
    """
    Get agent details including tools
    """
    try:
        # Get agent
        agent = agent_crud.get_agent(db, agent_uuid)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get agent details
        agent_data = agent_crud.get_agent_details(db, agent_uuid)
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent details not found")
        
        # Get tools
        tools = tool_crud.get_tools_by_agent(db, agent_uuid)
        
        return AgentDetailsResponse(
            agent_uuid=agent_uuid,
            agent_details=agent_data,
            tools=tools
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# For future use
@router.get("", response_model=AgentListResponse)
def list_agents(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all agents, optionally filtered by user_id
    """
    try:
        if user_id:
            agents = agent_crud.get_agents_by_user(db, user_id)
        else:
            agents = agent_crud.get_all_agents(db)
        
        return AgentListResponse(agents=agents)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# For future use
@router.delete("/{agent_uuid}", response_model=MessageResponse)
def delete_agent(
    agent_uuid: str,
    db: Session = Depends(get_db)
):
    """
    Delete an agent and its folder
    """
    try:
        # Delete from database
        success = agent_crud.delete_agent(db, agent_uuid)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Delete folder if exists
        agent_folder = os.path.join(SSA_AGENTS_DIR, agent_uuid)
        if os.path.exists(agent_folder):
            shutil.rmtree(agent_folder)
        
        return MessageResponse(
            message="Agent deleted successfully",
            agent_uuid=agent_uuid
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New endpoints for session and agent configuration
@router.post("/session/create", response_model=SessionCreateResponse)
def create_session_endpoint(
    data: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new session entry when user logs in
    """
    try:
        session = agent_crud.create_session(
            db=db,
            sesn_id=data.sesn_id,
            user_id=data.user_id,
            aplctn_cd=data.aplctn_cd
        )
        
        if not session:
            raise HTTPException(status_code=400, detail="Session already exists")
        
        return SessionCreateResponse(
            message="Session created successfully",
            sesn_id=session.sesn_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
