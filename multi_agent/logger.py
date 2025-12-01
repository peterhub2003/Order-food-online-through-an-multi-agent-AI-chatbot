from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.tree import Tree
from rich import print as rprint
import json
from typing import Any, Dict

console = Console()

class AgentLogger:
    @staticmethod
    def print_header(title: str):
        console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))

    @staticmethod
    def log_agent_start(agent_name: str, state: Dict[str, Any]):
        """Log khi một Agent bắt đầu chạy"""
        tree = Tree(f"[bold green]🤖 Agent Active: {agent_name}[/bold green]")
        
        # In state đầu vào (rút gọn messages để đỡ dài)
        input_data = state.copy()
        if "messages" in input_data:
            input_data["messages"] = f"[{len(input_data['messages'])} messages history]"
            
        tree.add(f"[yellow]Input State:[/yellow]").add(JSON.from_data(input_data))
        console.print(tree)
        console.print("")

    @staticmethod
    def log_planner_decision(decision: Any):
        """Log quyết định của Orchestrator"""
        # decision là object Pydantic hoặc dict
        data = decision.dict() if hasattr(decision, "dict") else decision
        
        panel = Panel(
            JSON.from_data(data),
            title="[bold purple]🧠 Orchestrator Decision[/bold purple]",
            subtitle=f"Next Step: [bold red]{data.get('next_step')}[/bold red]",
            border_style="purple"
        )
        console.print(panel)
        console.print("")

    @staticmethod
    def log_tool_call(tool_name: str, tool_args: Dict):
        """Log khi Tool Agent chuẩn bị gọi tool"""
        console.print(f"   [bold yellow]🔨 Calling Tool:[/bold yellow] [cyan]{tool_name}[/cyan]")
        console.print(f"   [dim]Arguments:[/dim] {json.dumps(tool_args, ensure_ascii=False)}")

    @staticmethod
    def log_tool_result(tool_name: str, result: Any):
        """Log kết quả trả về từ tool"""
        # Nếu result là dict/json lớn, in đẹp. Nếu ngắn, in dòng.
        try:
            if isinstance(result, (dict, list)):
                res_str = JSON.from_data(result)
            else:
                res_str = str(result)
        except:
            res_str = str(result)

        tree = Tree(f"   [bold blue]✅ Tool Result: {tool_name}[/bold blue]")
        tree.add(res_str)
        console.print(tree)
        console.print("--------------------------------------------------")

    @staticmethod
    def log_synthesis(response: str):
        """Log phản hồi cuối cùng"""
        console.print(Panel(
            response,
            title="[bold green]🗣️ Synthesis Final Response[/bold green]",
            border_style="green"
        ))