from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple
import asyncio

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools

from utils.config import TOOL_MAX_RETRIES, TOOL_TIMEOUT_SECONDS
from utils.logging_utils import get_logger

logger = get_logger("tools_utils")


async def load_tools(session: Any) -> Tuple[List[BaseTool], Dict[str, BaseTool], float]:
    """Load MCP tools from a session and return LangChain tools.

    Returns (tools, tool_map, elapsed_seconds), where:
    - tools: list of LangChain ``BaseTool`` instances suitable for
      ``ChatOpenAI.bind_tools``.
    - tool_map: mapping from tool name to tool instance for direct invocation.
    - elapsed_seconds: time spent loading tools from the MCP server.
    """

    start = time.perf_counter()
    tools: List[BaseTool] = await load_mcp_tools(session)
    elapsed = time.perf_counter() - start
    # logger.info("load_tools finished in %.3f seconds", elapsed)

    tool_map: Dict[str, BaseTool] = {tool.name: tool for tool in tools}
    return tools, tool_map, elapsed


async def invoke_tool(
    tool: Any,
    args: Dict[str, Any],
    tool_context: Dict[str, Any] | None = None,
) -> Any:
    """Invoke a LangChain tool with timeout and basic retry.

    Any exceptions are logged and, after exhausting retries, a string
    describing the error is returned so the model can handle it.
    """

    last_error: Exception | None = None
    merged_args: Dict[str, Any] = dict(args)
    tool_name = getattr(tool, "name", "unknown")

    if tool_context is not None:
        backend_token = tool_context.get("backend_access_token")
        if backend_token:
            merged_args["access_token"] = backend_token
            logger.info(f"🔑 Injected access_token into tool '{tool_name}'")
        else:

            if "order" in tool_name or "user" in tool_name:
                logger.warning(f"⚠️ Warning: Calling sensitive tool '{tool_name}' without BACKEND_ACCESS_TOKEN!")

    async def _run_once() -> Any:
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(merged_args)
        return await asyncio.to_thread(tool.invoke, merged_args)

    for attempt in range(TOOL_MAX_RETRIES + 1):
        try:
            logger.info(f"🔨 Calling Tool: {tool_name} (Attempt {attempt+1})")
            return await asyncio.wait_for(_run_once(), timeout=TOOL_TIMEOUT_SECONDS)
        except Exception as exc: 
            last_error = exc
            tool_name = getattr(tool, "name", "unknown")
            logger.warning(
                "Tool '%s' failed on attempt %d/%d: %s",
                tool_name,
                attempt + 1,
                TOOL_MAX_RETRIES + 1,
                exc,
            )

    tool_name = getattr(tool, "name", "unknown")
    logger.error(
        "Tool '%s' failed after %d attempts; returning error text to the model.",
        tool_name,
        TOOL_MAX_RETRIES + 1,
    )
    return f"[tool-error:{tool_name}] {last_error}"

