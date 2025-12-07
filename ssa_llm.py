"""
CRUD operations for LLMs
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.data_classes.ssa_models import SnowflakeCortexLLM


def init_default_llms(db: Session):
    """
    Initialize default Snowflake Cortex LLMs if not present
    """
    # Check if LLMs already exist
    count = db.query(SnowflakeCortexLLM).count()
    
    if count == 0:
        default_llms = [
            ("llama3.1-8b", "Llama 3.1 8B"),
            ("llama3.1-70b", "Llama 3.1 70B"),
            ("llama3.1-405b", "Llama 3.1 405B"),
            ("mistral-large2", "Mistral Large 2"),
            ("mixtral-8x7b", "Mixtral 8x7B"),
            ("snowflake-arctic", "Snowflake Arctic")
        ]
        
        for model_id, model_name in default_llms:
            create_llm(db, model_id, model_name)


def get_all_llms(db: Session) -> List[SnowflakeCortexLLM]:
    """
    Get all available Snowflake Cortex LLMs
    """
    return db.query(SnowflakeCortexLLM).all()


# For future use
def get_llm_by_id(db: Session, model_id: str) -> Optional[SnowflakeCortexLLM]:
    """
    Get a specific LLM by model_id
    """
    return db.query(SnowflakeCortexLLM).filter(SnowflakeCortexLLM.model_id == model_id).first()


# For future use
def create_llm(db: Session, model_id: str, model_name: str) -> SnowflakeCortexLLM:
    """
    Add a new LLM to the database
    """
    db_llm = SnowflakeCortexLLM(
        model_id=model_id,
        model_name=model_name
    )
    db.add(db_llm)
    db.commit()
    db.refresh(db_llm)
    return db_llm