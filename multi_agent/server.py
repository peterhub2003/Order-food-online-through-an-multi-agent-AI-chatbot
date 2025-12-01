from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException,Request
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from utils.logging_utils import get_logger
from .graph import workflow
from .state import AgentState
from fastapi.middleware.cors import CORSMiddleware

from utils.config import MCP_SERVER_ID, MCP_SERVER_URL
from .tools_utils import load_tools
from .graph import workflow

mcp_client = MultiServerMCPClient(
    {
        MCP_SERVER_ID: {
            "transport": "streamable_http",
            "url": MCP_SERVER_URL,
        }
    }
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hàm này chạy khi Server bắt đầu (trước yield) 
    và khi Server tắt (sau yield).
    """
    print(f"🔌 Connecting to MCP Server via {MCP_SERVER_URL}...")
    
    # Bắt đầu kết nối. Lệnh 'async with' sẽ giữ kết nối mở cho đến khi thoát block.
    # MultiServerMCPClient khi enter sẽ trả về bản thân nó hoặc context
    async with mcp_client.session(MCP_SERVER_ID) as client_context:

        
        print("🛠️ Loading tools...")
        tools_list, tool_map_dict, elapsed = await load_tools(client_context)
        
        print(f"✅ Loaded {len(tools_list)} tools in {elapsed:.3f}s")


        app.state.mcp_tools = tools_list
        app.state.mcp_tool_map = tool_map_dict
        

        memory = MemorySaver()
        app.state.graph = workflow.compile(checkpointer=memory)
        
        yield
        
    print("🛑 MCP Connection closed.")


app = FastAPI(title="Multi-Agent Orchestrator",lifespan=lifespan)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:80",  
    "*",                     
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,      
    allow_methods=["*"],         
    allow_headers=["*"],         
)


logger = get_logger("multi_agent.server")



class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.get("/health")
async def health() -> Dict[str, str]:
    logger.debug("health check")
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
async def run_multi_agent(request: Request, body: ChatRequest) -> ChatResponse:
    session_id = body.session_id or str(uuid.uuid4())
    logger.info(
        "run_multi_agent: received request",
        extra={"session_id": session_id},
    )

    mcp_tools = request.app.state.mcp_tools
    mcp_tool_map = request.app.state.mcp_tool_map

    auth_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not auth_token:
        logger.warning("⚠️ No Bearer token found in request headers!")
    else:
        logger.info("🔑 Backend access token found in request headers.")

        
    config = {
        "configurable": {
            "thread_id": session_id,      # Cho checkpointer
            "mcp_tools": mcp_tools,           
            "mcp_tool_map": mcp_tool_map,      
            "backend_access_token": auth_token 
        }
    }

    input_data = {
        "user_input": body.message,
        "messages": [HumanMessage(content=body.message)]
    }

    try:
        
        graph = request.app.state.graph
        
        result = await graph.ainvoke(input_data, config=config)
        
        last_msg = result["messages"][-1]
        
        logger.info(
            "run_multi_agent: completed",
            extra={
                "session_id": session_id,
                "has_warning": bool(result.get("warning")),
            },
        )

        return ChatResponse(
            response=last_msg.content,
            session_id=session_id
        )
        

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



