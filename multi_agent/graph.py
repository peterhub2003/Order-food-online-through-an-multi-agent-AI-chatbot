import json
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from .model_provider import create_chat_model
from .prompts import AGENT_PROMPTS
from .tools_utils import invoke_tool
from .logger import AgentLogger
import re

from .state import (
    AgentState, OrchestratorDecision, UserInfo, CartItem,
    SearchMenuOutput, CreateOrderOutput, AddItemOutput, 
    CalculateTotalOutput, CheckOrderOutput, FaqOutput, 
    RemoveItemOutput, GenericOutput, CheckUserOutput
)

from typing import Optional, List


def update_cart(current_cart: List[dict], new_items: Optional[List[CartItem]]) -> List[dict]:
    if not current_cart:
        current_cart = []
    
    if not new_items:
        return current_cart
    
    updated_cart = [item for item in current_cart]
    
    for new_item in new_items:
        new_item_dict = new_item.dict()
        

        found = False
        for existing_item in updated_cart:
            if existing_item['item_name'].lower() in new_item_dict['item_name'].lower() or \
               new_item_dict['item_name'].lower() in existing_item['item_name'].lower():
                
                if new_item_dict.get('item_id'):
                    existing_item['item_id'] = new_item_dict['item_id']
                
                if new_item_dict['quantity'] != 1: 
                     existing_item['quantity'] = new_item_dict['quantity']
                     
                found = True
                break
        
        if not found:
            updated_cart.append(new_item_dict)
            
    return updated_cart

def extract_json_from_text(text: str) -> dict:
    try:
        if match:
            json_str = match.group(1).strip()
            return json.loads(json_str)
        return json.loads(text)
    except Exception:
        return {} 
    

def update_user_info(current_info: dict, new_info: UserInfo) -> dict:
    if not current_info:
        current_info = {"name": None, "phone": None, "address": None}
    
    if not new_info:
        return current_info
        
    return {
        "name": new_info.name if new_info.name else current_info.get("name"),
        "phone": new_info.phone if new_info.phone else current_info.get("phone"),
        "address": new_info.address if new_info.address else current_info.get("address"),
    }


async def orchestrator_node(state: AgentState):

    AgentLogger.log_agent_start("Orchestrator", state)

    llm = create_chat_model()
    prompt_config = AGENT_PROMPTS["planner"]
    
    
    current_user_info = state.get("user_info", {}) or {}
    current_queue = state.get("task_queue", [])
    task_outputs = state.get("task_outputs", {})
    if current_queue is None: 
        current_queue = []

    current_cart = state.get("cart", []) or []

    user_msg_content = prompt_config.user_template.format(
        user_input=state.get("user_input", ""),
        task_queue=str(current_queue),
        task_outputs=json.dumps(task_outputs, ensure_ascii=False),
        planner_plan="",
        warning=state.get("warning", ""),
        current_user_info=str(current_user_info),
        current_cart=json.dumps(current_cart, ensure_ascii=False),
    )
    
    messages = [
        ("system", prompt_config.system),
        ("human", user_msg_content)
    ]
    
    try:
        structured_llm = llm.with_structured_output(OrchestratorDecision)
        decision: OrchestratorDecision = await structured_llm.ainvoke(messages)
    except Exception as e:
        #logger.error(f"Orchestrator Error: {e}")
        return {
            "next_step": "synthesis_agent",
            "next_action": "finish",
            "task_queue": [],
            "warning": f"System Error: {str(e)}",
            "user_info": current_user_info,
            "task_outputs": task_outputs
        }

    AgentLogger.log_planner_decision(decision)

    new_info = decision.extracted_info
    updated_info = current_user_info.copy()
    if new_info:
        if new_info.name: updated_info["name"] = new_info.name
        if new_info.phone: updated_info["phone"] = new_info.phone
        if new_info.address: updated_info["address"] = new_info.address 

    updated_cart = update_cart(current_cart, decision.extracted_cart)

    actual_next_step = decision.next_step
    if decision.refusal_reason:
        actual_next_step = "synthesis_agent"
    elif decision.current_action in ["ask_user", "finish"]:
        actual_next_step = "synthesis_agent"
    else:
        actual_next_step = "tool_agent"


    return {
        "next_step": actual_next_step,
        "next_action": decision.current_action,
        "task_queue": decision.updated_queue,
        "planner_plan": decision.plan,
        "warning": "",
        "user_info": updated_info,
        "task_outputs": task_outputs,
        "should_clear_memory": getattr(decision, "clear_memory", False),
        "refusal_reason": getattr(decision, "refusal_reason", None),
        "cart": updated_cart 
    }



async def tool_agent_node(state: AgentState, config: RunnableConfig):
    AgentLogger.log_agent_start("Tool Agent", state)

    llm = create_chat_model()
    prompt_config = AGENT_PROMPTS["tool_agent"]
    
    
    mcp_tools = config["configurable"].get("mcp_tools", [])
    mcp_tool_map = config["configurable"].get("mcp_tool_map", {})
    backend_token = config["configurable"].get("backend_access_token")

    llm_with_tools = llm.bind_tools(mcp_tools)
    
    schema_map = {
        "search_menu": SearchMenuOutput,
        "create_order": CreateOrderOutput,
        "add_item": AddItemOutput,
        "remove_item": RemoveItemOutput,
        "calculate_total": CalculateTotalOutput,
        "check_order": CheckOrderOutput,
        "check_user_info": CheckOrderOutput, 
        "cancel_order": GenericOutput,
        "confirm_order": GenericOutput,
        "ask_faq": FaqOutput
    }

    current_action = state.get("next_action", "unknown")
    current_user_info = state.get("user_info", {})
    target_schema = schema_map.get(current_action, GenericOutput)

    user_msg_content = prompt_config.user_template.format(
        next_action=current_action,
        plan=state.get("planner_plan", ""),
        user_info_str=json.dumps(current_user_info, ensure_ascii=False)
    )
    
    messages = [
        ("system", prompt_config.system),
        ("human", user_msg_content)
    ]
    

    try:
        ai_msg = await llm_with_tools.ainvoke(messages)
    except Exception as e:
        return {
            "task_outputs": {
                **state.get("task_outputs", {}),
                current_action: {"error": f"LLM Error: {str(e)}", "status": "failed"}
            }
        }
    

    tool_results_str = ""
    

    if ai_msg.tool_calls:
        
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            AgentLogger.log_tool_call(tool_name, tool_args)

            tool_instance = mcp_tool_map.get(tool_name)
            output = "Tool not found"
            if tool_instance:
                output = await invoke_tool(
                    tool=tool_instance, 
                    args=tool_args, 
                    tool_context={"backend_access_token": backend_token}
                )
            
            AgentLogger.log_tool_result(tool_name, output)
            tool_results_str += f"- Action: {tool_name}\n- Result: {output}\n"
        

        summary_messages = messages + [
            ai_msg,
            ToolMessage(content=tool_results_str, tool_call_id=ai_msg.tool_calls[0]["id"])
        ]

        schema_map = {
            "search_menu": SearchMenuOutput,
            "create_order": CreateOrderOutput,
            "add_item": AddItemOutput,
            "calculate_total": CalculateTotalOutput,
            "check_user_info": CheckUserOutput
        }


        try:
            structured_summary_llm = llm.with_structured_output(target_schema)
            final_output_obj = await structured_summary_llm.ainvoke(summary_messages)
            extracted_data = final_output_obj.dict()
            
        except Exception as e:
            extracted_data = {"error": "Failed to structure output", "raw": tool_results_str}

    else:
        extracted_data = {"status": "no_tool_called", "reason": ai_msg.content}
    

    current_outputs = state.get("task_outputs", {}).copy()
    current_outputs[current_action] = extracted_data
    
    AgentLogger.log_tool_result(f"💾 Memory Saved ({current_action})", extracted_data)
    
    return {
        "task_outputs": current_outputs,
        "tool_answer": str(extracted_data)
    }




async def synthesis_agent_node(state: AgentState):
    AgentLogger.log_agent_start("Synthesis Agent", state)
    llm = create_chat_model()
    prompt_config = AGENT_PROMPTS["synthesis"]
    
    task_outputs = state.get("task_outputs", {})
    should_clear = state.get("should_clear_memory", False)
    current_user_info = state.get("user_info", {}) or {}
    refusal_reason = state.get("refusal_reason", None)


    user_msg_content = prompt_config.user_template.format(
        user_input=state.get("user_input", ""),
        next_action=state.get("next_action", ""),
        task_outputs=json.dumps(task_outputs, ensure_ascii=False),
        warning=state.get("warning", ""),   
        current_user_info=str(current_user_info),
        refusal_reason=str(refusal_reason) if refusal_reason else "None"
    )
    
    messages = [
        ("system", prompt_config.system),
        ("human", user_msg_content)
    ]
    response = await llm.ainvoke(messages)
    AgentLogger.log_synthesis(response.content)

    final_state_update = {
        "messages": [response],
        "refusal_reason": None 
    }
    
    if should_clear:
        AgentLogger.log_tool_result("SYSTEM", "Clearing Task Memory & Queue (Order Finished)")
        final_state_update["task_outputs"] = {} 
        final_state_update["task_queue"] = []   
        final_state_update["tool_answer"] = ""
        final_state_update["should_clear_memory"] = False
        final_state_update["cart"] = [] 
    
    return final_state_update 


def router(state: AgentState):
    return state["next_step"]



workflow = StateGraph(AgentState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("tool_agent", tool_agent_node)
workflow.add_node("synthesis_agent", synthesis_agent_node)

workflow.set_entry_point("orchestrator")

workflow.add_conditional_edges(
    "orchestrator",
    router,
    {
        "tool_agent": "tool_agent",
        "synthesis_agent": "synthesis_agent"
    }
)


workflow.add_edge("tool_agent", "orchestrator")
workflow.add_edge("synthesis_agent", END)

