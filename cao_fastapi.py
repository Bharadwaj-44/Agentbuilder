import decimal
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from snowflake_auth import SnowflakeAuthManager
import json
import os
import yaml
from models import AgentRequest, FilterDataRequest
from validator import validate_agent_request
from models import EnvName
import io

from cao.CAO_AGENT import run_agent

app = FastAPI()

##Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DataRequest(BaseModel):
    application_name: str
    user_identity: str
    paid_start_date: str
    paid_end_date: str
    disalwd_explntn_cd: str = ""

import logging
logger = logging.getLogger(__name__)

@app.post("/run_{{application_name}}_agent")
async def run_{{application_name}}_agent_endpoint(
    request: AgentRequest = Body(..., example=None)
):
    error = validate_agent_request(request)
    if error:
        return error
    messages = [msg.model_dump() for msg in request.messages]
    print("Calling the run agent")
    return await run_agent(
        messages,
        request.application_name,
        request.user_identity,
        "{{agent_name}}"
    )
