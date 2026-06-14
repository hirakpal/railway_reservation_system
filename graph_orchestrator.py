from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from pydantic import BaseModel

# Define the shared State for our agents
class State(TypedDict):
    task: str
    seat_id: int
    user_id: str
    history: List[str]

# Define RouterOutput for structured LLM output
class RouterOutput(BaseModel):
    action: str
    seat_id: int

# 1. Initialize LLM for Structured Output
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(RouterOutput)

# 2. Add the Reasoning Node
def reasoning_node(state):
    task = state.get("task", "")
    decision = structured_llm.invoke(f"Analyze this request: '{task}'. What is the intent?")

    # Update the state with the LLM's decision
    return (
        {
            "task": decision.action,  # Updates the task to the clean action
            "seat_id": decision.seat_id,
            "history": [f"LLM decided to {decision.action} for seat {decision.seat_id}"],
        }
    )

# 3. Update the builder
builder = StateGraph(State)

builder.add_node("reasoning", reasoning_node)  # New entry point
builder.add_node("search", search_agent)
builder.add_node("booking", booking_agent)
builder.add_node("cancellation", cancellation_agent)

builder.set_entry_point("reasoning")

# 4. Update the Supervisor to use LLM results
def supervisor(state):
    # Now simply routes based on the state set by the reasoning_node
    return state["task"]

builder.add_conditional_edges("reasoning", supervisor, {
    "search": "search",
    "book": "booking",
    "cancel": "cancellation"
})

builder.add_edge("search", END)
builder.add_edge("booking", END)
builder.add_edge("cancellation", END)

graph = builder.compile()
