"""
LLM endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.database.crud import ssa_llm as llm_crud
from app.api.schemas.ssa_api_schemas import LLMModel

router = APIRouter()


@router.get("/llms", response_model=List[LLMModel])
def get_available_llms(db: Session = Depends(get_db)):
    """
    Step 3: Get list of available Snowflake Cortex LLMs
    """
    try:
        llms = llm_crud.get_all_llms(db)
        return llms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
