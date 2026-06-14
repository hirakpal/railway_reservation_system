from langgraph.graph import StateGraph, END
# from agents import search_agent, booking_agent # This import is not needed as functions are in notebook scope
from typing import TypedDict, List

# Define the shared State for our agents
class State(TypedDict):
    task: str
    seat_id: int
    user_id: str
    history: List[str]

# 1. Initialize the Graph
builder = StateGraph(State)

# 2. Add Nodes
builder.add_node("search", search_agent)
builder.add_node("booking", booking_agent)
builder.add_node("cancellation", cancellation_agent)

# 3. Define Logic: The Supervisor/Router
def supervisor(state):
    # This acts as our "Reasoning" layer
    task = state.get("task", "").lower()
    if "book" in task: return "booking"
    if "cancel" in task: return "cancellation"
    return "search"

# 4. Set Edges
builder.set_entry_point("search") # Everything starts with a search
builder.add_conditional_edges("search", supervisor, {"booking": "booking", "search": END})
builder.add_edge("booking", END)
builder.add_edge("cancellation", END)

# 5. Compile
graph = builder.compile()
