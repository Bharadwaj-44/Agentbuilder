"""
CRUD operations for LangGraph models
Handles LLM Providers, LLM Models, Agents, Profiles, Tools, and Memory Configurations
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.data_classes.lsa_models import (
    LLMProvider,
    LLMModel,
    LangGraphAgent,
    LangGraphAgentProfile,
    MCPTool,
    MemoryConfigModel,
)


# ============================================================
# Initialization Utilities for Default Providers and LLMs
# ============================================================

def init_default_providers(db: Session):
    """
    Initialize a set of default LLM providers if they do not exist.
    Used to prefill provider dropdowns in the UI.
    """
    default_providers = [
        {"provider_id": "cortex", "provider_name": "Snowflake Cortex"},
        {"provider_id": "openai", "provider_name": "OpenAI"},
        {"provider_id": "anthropic", "provider_name": "Anthropic"},
        {"provider_id": "google_gemini", "provider_name": "Google Gemini"},
        {"provider_id": "ehap", "provider_name": "EHAP"},
    ]

    created_count = 0
    for provider in default_providers:
        existing = get_provider_by_id(db, provider["provider_id"])
        if not existing:
            create_provider(db, provider["provider_id"], provider["provider_name"])
            created_count += 1

    return {"message": f"Initialized {created_count} new providers."}


def init_default_llms_by_provider(db: Session):
    """
    Initialize a set of default LLMs for each provider.
    Used to prefill LLM dropdowns in the UI for the selected provider.
    """
    default_llms = {
        "cortex": [
            {"model_id": "openai-gpt-5-chat", "model_name": "OpenAI GPT 5 Chat"},
            {"model_id": "claude-4-sonnet", "model_name": "Claude 4 Sonnet"},
            {"model_id": "mistral-large", "model_name": "Mistral Large"},
            {"model_id": "llama3-70b", "model_name": "Llama 3 70B"},
            {"model_id": "llama3-8b", "model_name": "Llama 3 8B"},
            {"model_id": "mixtral-8x7b", "model_name": "Mixtral 8x7B"},
        ],
        "openai": [
            {"model_id": "gpt-4", "model_name": "GPT-4"},
            {"model_id": "gpt-4-turbo", "model_name": "GPT-4 Turbo"},
            {"model_id": "gpt-3.5-turbo", "model_name": "GPT-3.5 Turbo"},
        ],
        "anthropic": [
            {"model_id": "claude-3-opus", "model_name": "Claude 3 Opus"},
            {"model_id": "claude-3-sonnet", "model_name": "Claude 3 Sonnet"},
            {"model_id": "claude-3-haiku", "model_name": "Claude 3 Haiku"},
        ],
        "google_gemini": [
            {"model_id": "gemini-1.5-pro", "model_name": "Gemini 1.5 Pro"},
            {"model_id": "gemini-1.5-flash", "model_name": "Gemini 1.5 Flash"},
        ],
        "ehap": [
            {"model_id": "ehap-base", "model_name": "EHAP Base Model"},
            {"model_id": "ehap-advanced", "model_name": "EHAP Advanced Model"},
        ],
    }

    created_count = 0
    for provider_id, models in default_llms.items():
        provider = get_provider_by_id(db, provider_id)
        if not provider:
            continue  # Skip if provider not found

        for model in models:
            existing = get_llm_by_id(db, model["model_id"])
            if not existing:
                create_llm_model(
                    db,
                    model_id=model["model_id"],
                    model_name=model["model_name"],
                    provider_id=provider_id,
                )
                created_count += 1

    return {"message": f"Initialized {created_count} new LLMs."}


# ============================================================
# LLM Provider CRUD
# ============================================================

def create_provider(db: Session, provider_id: str, provider_name: str) -> LLMProvider:
    provider = LLMProvider(provider_id=provider_id, provider_name=provider_name)
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def get_all_providers(db: Session) -> List[LLMProvider]:
    return db.query(LLMProvider).all()


def get_provider_by_id(db: Session, provider_id: str) -> Optional[LLMProvider]:
    return db.query(LLMProvider).filter(LLMProvider.provider_id == provider_id).first()


def delete_provider(db: Session, provider_id: str) -> bool:
    provider = db.query(LLMProvider).filter(LLMProvider.provider_id == provider_id).first()
    if not provider:
        return False
    db.delete(provider)
    db.commit()
    return True


# ============================================================
# LLM Model CRUD
# ============================================================

def create_llm_model(db: Session, model_id: str, model_name: str, provider_id: str) -> LLMModel:
    llm = LLMModel(
        model_id=model_id,
        model_name=model_name,
        provider_id=provider_id,
    )
    db.add(llm)
    db.commit()
    db.refresh(llm)
    return llm


def get_llms_by_provider(db: Session, provider_id: str) -> List[LLMModel]:
    return db.query(LLMModel).filter(LLMModel.provider_id == provider_id).all()


def get_llm_by_id(db: Session, model_id: str) -> Optional[LLMModel]:
    return db.query(LLMModel).filter(LLMModel.model_id == model_id).first()


def delete_llm_model(db: Session, model_id: str) -> bool:
    llm = db.query(LLMModel).filter(LLMModel.model_id == model_id).first()
    if not llm:
        return False
    db.delete(llm)
    db.commit()
    return True


# ============================================================
# LangGraph Agent CRUD
# ============================================================

def create_agent(db: Session, agent_uuid: str, user_id: str) -> LangGraphAgent:
    agent = LangGraphAgent(agent_uuid=agent_uuid, user_id=user_id)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def get_agent(db: Session, agent_uuid: str) -> Optional[LangGraphAgent]:
    return db.query(LangGraphAgent).filter(LangGraphAgent.agent_uuid == agent_uuid).first()


def get_agents_by_user(db: Session, user_id: str) -> List[LangGraphAgent]:
    return db.query(LangGraphAgent).filter(LangGraphAgent.user_id == user_id).all()


def delete_agent(db: Session, agent_uuid: str) -> bool:
    agent = db.query(LangGraphAgent).filter(LangGraphAgent.agent_uuid == agent_uuid).first()
    if not agent:
        return False
    db.delete(agent)
    db.commit()
    return True


# ============================================================
# LangGraph Agent Profile CRUD
# ============================================================

def create_agent_profile(db: Session, agent_id: str, llm_model_id: Optional[int], agent_json: bytes) -> LangGraphAgentProfile:
    profile = LangGraphAgentProfile(
        agent_id=agent_id,
        llm_model_id=llm_model_id,
        agent_json=agent_json,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_agent_profile(db: Session, agent_id: str, llm_model_id: Optional[int], agent_json: bytes) -> Optional[LangGraphAgentProfile]:
    profile = db.query(LangGraphAgentProfile).filter(LangGraphAgentProfile.agent_id == agent_id).first()
    if not profile:
        return None

    profile.llm_model_id = llm_model_id
    profile.agent_json = agent_json
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


def get_agent_profile(db: Session, agent_id: str) -> Optional[LangGraphAgentProfile]:
    return db.query(LangGraphAgentProfile).filter(LangGraphAgentProfile.agent_id == agent_id).first()


def delete_agent_profile(db: Session, agent_id: str) -> bool:
    profile = db.query(LangGraphAgentProfile).filter(LangGraphAgentProfile.agent_id == agent_id).first()
    if not profile:
        return False
    db.delete(profile)
    db.commit()
    return True


# ============================================================
# MCP Tool CRUD
# ============================================================

def create_mcp_tool(db: Session, agent_id: str, mcp_tool_json: bytes) -> MCPTool:
    tool = MCPTool(agent_id=agent_id, mcp_tool_json=mcp_tool_json)
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool


def get_mcp_tools_by_agent(db: Session, agent_id: str) -> List[MCPTool]:
    return db.query(MCPTool).filter(MCPTool.agent_id == agent_id).all()


def get_mcp_tool_by_id(db: Session, tool_id: int) -> Optional[MCPTool]:
    return db.query(MCPTool).filter(MCPTool.id == tool_id).first()


def delete_mcp_tool(db: Session, tool_id: int) -> bool:
    tool = db.query(MCPTool).filter(MCPTool.id == tool_id).first()
    if not tool:
        return False
    db.delete(tool)
    db.commit()
    return True


# ============================================================
# Memory Configuration CRUD
# ============================================================

def create_memory_config(db: Session, agent_id: str, memory_config_json: bytes) -> MemoryConfigModel:
    memory = MemoryConfigModel(agent_id=agent_id, memory_config_json=memory_config_json)
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def update_memory_config(db: Session, agent_id: str, memory_config_json: bytes) -> Optional[MemoryConfigModel]:
    memory = db.query(MemoryConfigModel).filter(MemoryConfigModel.agent_id == agent_id).first()
    if not memory:
        return None

    memory.memory_config_json = memory_config_json
    memory.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(memory)
    return memory


def get_memory_config(db: Session, agent_id: str) -> Optional[MemoryConfigModel]:
    return db.query(MemoryConfigModel).filter(MemoryConfigModel.agent_id == agent_id).first()


def delete_memory_config(db: Session, agent_id: str) -> bool:
    memory = db.query(MemoryConfigModel).filter(MemoryConfigModel.agent_id == agent_id).first()
    if not memory:
        return False
    db.delete(memory)
    db.commit()
    return True




# ============================================================
# Initialization Utilities for Default Providers and LLMs
# ============================================================

# def init_default_providers(db: Session):
#     """
#     Initialize a set of default LLM providers if they do not exist.
#     Used to prefill provider dropdowns in the UI.
#     """
#     default_providers = [
#         {"provider_id": "snowflake_cortex", "provider_name": "Snowflake Cortex"},
#         {"provider_id": "openai", "provider_name": "OpenAI"},
#         {"provider_id": "anthropic", "provider_name": "Anthropic"},
#         {"provider_id": "google_gemini", "provider_name": "Google Gemini"},
#         {"provider_id": "ehap", "provider_name": "EHAP"},
#     ]

#     created_count = 0
#     for provider in default_providers:
#         existing = (
#             db.query(LLMProvider)
#             .filter(LLMProvider.provider_id == provider["provider_id"])
#             .first()
#         )
#         if not existing:
#             new_provider = LLMProvider(
#                 provider_id=provider["provider_id"],
#                 provider_name=provider["provider_name"]
#             )
#             db.add(new_provider)
#             created_count += 1

#     if created_count > 0:
#         db.commit()

#     return {"message": f"Initialized {created_count} new providers."}


# def init_default_llms(db: Session):
#     """
#     Initialize a set of default LLMs for each provider.
#     Used to prefill LLM dropdowns in the UI for the selected provider.
#     """
#     # Define provider → list of models mapping
#     default_llms = {
#         "snowflake_cortex": [
#             {"model_id": "claude-4-sonnet", "model_name": "Claude 4 Sonnet"},
#             {"model_id": "mistral-large", "model_name": "Mistral Large"},
#             {"model_id": "llama3-70b", "model_name": "Llama 3 70B"},
#             {"model_id": "llama3-8b", "model_name": "Llama 3 8B"},
#             {"model_id": "mixtral-8x7b", "model_name": "Mixtral 8x7B"},
#         ],
#         "openai": [
#             {"model_id": "gpt-4", "model_name": "GPT-4"},
#             {"model_id": "gpt-4-turbo", "model_name": "GPT-4 Turbo"},
#             {"model_id": "gpt-3.5-turbo", "model_name": "GPT-3.5 Turbo"},
#         ],
#         "anthropic": [
#             {"model_id": "claude-3-opus", "model_name": "Claude 3 Opus"},
#             {"model_id": "claude-3-sonnet", "model_name": "Claude 3 Sonnet"},
#             {"model_id": "claude-3-haiku", "model_name": "Claude 3 Haiku"},
#         ],
#         "google_gemini": [
#             {"model_id": "gemini-1.5-pro", "model_name": "Gemini 1.5 Pro"},
#             {"model_id": "gemini-1.5-flash", "model_name": "Gemini 1.5 Flash"},
#         ],
#         "ehap": [
#             {"model_id": "ehap-base", "model_name": "EHAP Base Model"},
#             {"model_id": "ehap-advanced", "model_name": "EHAP Advanced Model"},
#         ],
#     }

#     created_count = 0
#     for provider_id, models in default_llms.items():
#         provider = (
#             db.query(LLMProvider)
#             .filter(LLMProvider.provider_id == provider_id)
#             .first()
#         )
#         if not provider:
#             # skip creating llms if provider does not exist
#             continue

#         for model in models:
#             existing = (
#                 db.query(LLMModel)
#                 .filter(LLMModel.model_id == model["model_id"])
#                 .first()
#             )
#             if not existing:
#                 new_model = LLMModel(
#                     model_id=model["model_id"],
#                     model_name=model["model_name"],
#                     provider_id=provider.provider_id,
#                 )
#                 db.add(new_model)
#                 created_count += 1

#     if created_count > 0:
#         db.commit()

#     return {"message": f"Initialized {created_count} new LLMs."}