from typing import TypedDict, Annotated, List, Literal, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CartItem(BaseModel):
    item_name: str
    quantity: int = 1
    item_id: Optional[int] = None
    note: Optional[str] = None



class MenuItem(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None

class SearchMenuOutput(BaseModel):

    items: List[MenuItem] = Field(default=[], description="Danh sách món ăn tìm thấy.")
    note: Optional[str] = Field(None, description="Ghi chú.")

class OrderDetails(BaseModel):
    id: int
    status: str
    total_amount: Optional[float] = 0.0

class CreateOrderOutput(BaseModel):

    order_id: Optional[int] = Field(None, description="ID đơn hàng vừa tạo.")
    status: str = Field(..., description="Trạng thái (DRAFT/PENDING).")
    error: Optional[str] = None

class AddItemOutput(BaseModel):

    success: bool
    order_id: int
    message: str = "Item added successfully"

class RemoveItemOutput(BaseModel):

    success: bool
    order_id: int
    message: str = "Item removed"

class CalculateTotalOutput(BaseModel):

    total_amount: float
    delivery_fee: float = 0.0
    final_total: float
    breakdown: str

class CheckUserOutput(BaseModel):

    has_info: bool = Field(..., description="Có tìm thấy info trong DB không.")
    user_data: Optional[UserInfo] = None

class CheckOrderOutput(BaseModel):

    orders: List[OrderDetails] = Field(default=[], description="Danh sách đơn hàng gần đây.")
    current_order_status: Optional[str] = None

class FaqOutput(BaseModel):

    answers: List[str] = Field(default=[], description="Danh sách câu trả lời tìm thấy.")

class GenericOutput(BaseModel):

    result: str
    success: bool


class OrchestratorDecision(BaseModel):
    next_step: Literal["tool_agent", "synthesis_agent"]
    current_action: str
    updated_queue: List[str]
    plan: str
    extracted_info: Optional[UserInfo] = None
    extracted_cart: Optional[List[CartItem]] = None
    clear_memory: bool = False
    refusal_reason: Optional[str] = None

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str

    task_queue: List[str]
    next_action: str
    task_outputs: Dict[str, Any]
    tool_answer: str 

    warning: str
    user_info: Dict[str, Optional[str]]
    cart: List[Dict[str, Any]]
    should_clear_memory: bool
    refusal_reason: Optional[str]

    next_step: Literal["tool_agent", "synthesis_agent"]



