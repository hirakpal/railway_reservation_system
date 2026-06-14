#graph_orchestrator.py
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List
from pydantic import BaseModel

# Import agent functions
from agents import search_agent, booking_agent, cancellation_agent, status_agent

# 1. Define State and Router Output
class State(TypedDict):
    task: str
    seat_id: int | None
    user_id: str
    history: List[str]
    action: str

class RouterOutput(BaseModel):
    action: str
    seat_id: int | None = None

# 2. Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(RouterOutput)

# 3. Reasoning Node: Updated to include 'status'
def reasoning_node(state):
    instruction = (
        "You are a router. Classify user intent as 'search', 'book', 'cancel', or 'status'. "
        "If the intent is unclear, return 'invalid'."
    )
    decision = structured_llm.invoke(f"{instruction} Request: '{state.get('task')}'")
    
    action = decision.action.strip().lower() if decision.action else "invalid"
    valid_actions = ["search", "book", "cancel", "status"]
    final_action = action if action in valid_actions else "invalid"
    
    return {
        "action": final_action, 
        "seat_id": decision.seat_id, 
        "history": [f"Routing to {final_action}"]
    }


def invalid_seat_id_handler(state):
    return {"history": ["Invalid intent or input. Please try again."], "action": "invalid"}

# 4. Define the Graph
graph_builder = StateGraph(State)
graph_builder.add_node("reasoning", reasoning_node)
graph_builder.add_node("search", search_agent)
graph_builder.add_node("booking", booking_agent)
graph_builder.add_node("cancellation", cancellation_agent)
graph_builder.add_node("status", status_agent) # New node
graph_builder.add_node("invalid_seat_id_handler", invalid_seat_id_handler)

graph_builder.set_entry_point("reasoning")

# 5. Routing Logic: Updated with 'status'
graph_builder.add_conditional_edges(
    "reasoning",
    lambda state: state["action"],
    {
        "search": "search",
        "book": "booking",
        "cancel": "cancellation",
        "status": "status",
        "invalid": "invalid_seat_id_handler",
    },
)

# 6. Edges to END
graph_builder.add_edge("search", END)
graph_builder.add_edge("booking", END)
graph_builder.add_edge("cancellation", END)
graph_builder.add_edge("status", END)
graph_builder.add_edge("invalid_seat_id_handler", END)

# 7. Compile with Memory
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)
