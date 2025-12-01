from __future__ import annotations

from typing import Sequence

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from utils.config import MODEL_NAME, OLLAMA_API_KEY, OLLAMA_BASE_URL


def create_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OLLAMA_API_KEY,
        base_url=OLLAMA_BASE_URL,
        reasoning_effort="low"
    )


def create_tool_model(
    tools: Sequence[BaseTool],
    *,
    tool_choice: str | None = "auto",
    parallel_tool_calls: bool = True,
) -> ChatOpenAI:
    """Create a ChatOpenAI model configured for tool calling via LangChain.

    The returned model exposes `.invoke` / `.ainvoke` and will populate
    `AIMessage.tool_calls` with a list of tool call dicts:
    `{"name": str, "args": dict, "id": str}`.
    """

    base = create_chat_model()
    return base.bind_tools(
        list(tools),
        tool_choice=tool_choice,
        parallel_tool_calls=parallel_tool_calls,
    )
