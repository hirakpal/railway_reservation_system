#graph_orchestrator.py
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from pydantic import BaseModel


class State(TypedDict):
    task: str
    seat_id: int | None
    user_id: str
    history: List[str]
    action: str

class RouterOutput(BaseModel):
    action: str
    seat_id: int | None = None

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(RouterOutput)

def reasoning_node(state):
    decision = structured_llm.invoke(f"Analyze: '{state.get('task')}'. Intent?")
    action = decision.action if decision.action in ["search", "book", "cancel"] else "invalid"
    return {"action": action, "seat_id": decision.seat_id, "history": [f"Routing to {action}"]}

graph_builder = StateGraph(State)
graph_builder.add_node("reasoning", reasoning_node)
graph_builder.add_node("search", search_agent)
graph_builder.add_node("booking", booking_agent)
graph_builder.add_node("cancellation", cancellation_agent)

graph_builder.set_entry_point("reasoning")
graph_builder.add_conditional_edges("reasoning", lambda state: state["action"], {
    "search": "search", "book": "booking", "cancel": "cancellation"
})
graph_builder.add_edge("search", END); graph_builder.add_edge("booking", END); graph_builder.add_edge("cancellation", END)

graph = graph_builder.compile()
