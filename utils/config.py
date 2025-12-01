from __future__ import annotations

import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-oss:20b")
MCP_SERVER_ID = os.getenv("MCP_SERVER_ID", "sandbox")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-backend:8000/mcp")

# Orchestrator limits
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "20"))
MAX_TOTAL_TOOL_CALLS = int(os.getenv("MAX_TOTAL_TOOL_CALLS", "32"))
TOOL_TIMEOUT_SECONDS = float(os.getenv("TOOL_TIMEOUT_SECONDS", "15.0"))
TOOL_MAX_RETRIES = int(os.getenv("TOOL_MAX_RETRIES", "2"))

# Redis configuration for multi-turn conversation caching
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "mcp_ollama:")



SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    (
        "You are a helpful assistant that can use tools exposed via an MCP "
        "server. When useful, you SHOULD call tools rather than guessing. "
        "Think through the problem, call tools to gather facts, then provide "
        "a concise final answer to the user."
    ),
)
