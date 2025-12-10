from agent import AgentRun
from models import EnvName
import yaml
import os

async def run_agent(messages, 
                    application_name="{{application_name}}", 
                    user_identity="{{user_identity}}", 
                    agent_name="{{agent_name}}"
                    ):

    # Load config from app.yaml
    config_path = os.path.join(os.environ.get("GENAI_PATH", "dev").lower(), "app.yaml")
    print(config_path)
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)


    # Get environment from GENAI_ENV host variable
    # env = os.environ.get("GENAI_ENV", "dev").lower()
    env = os.getenv('env_name')

    # Validate env against EnvName enum from models
    valid_envs = {e.value for e in EnvName}
    if env not in valid_envs:
        raise ValueError(f"Invalid environment '{env}'. Must be one of: {', '.join(valid_envs)}")

    # Get agent config for the given agent_name and environment
    config = config.get("Agents", {})
    agent_config = config.get(agent_name, {}).get(env, {})
    db = agent_config.get("db", "POC_SPC_SNOWPARK_DB")
    schema = agent_config.get("schema", "DATA_SCHEMA")
    aplctn_cd = agent_config.get("aplctn_cd", "aedl")
    env = agent_config.get("env", "preprod")
    region_name = agent_config.get("region_name", "us-east-1")
    warehouse_size_suffix = agent_config.get("warehouse_size_suffix", "")
    prefix = agent_config.get("prefix", "")

    agent_builder = AgentRun.Builder() \
        .aplctn_cd(aplctn_cd) \
        .env(env) \
        .region_name(region_name) \
        .warehouse_size_suffix(warehouse_size_suffix) \
        .prefix(prefix) \
        .agent_name(agent_name) \
        .agent_db(db) \
        .agent_schema(schema) \
        .application_name(application_name) \
        .user_identity(user_identity) \
        .messages(messages) \
        .tool_choice()

    # Build agent object
    agent = agent_builder.build()
    print("Running agent...")
    return await agent.run()
