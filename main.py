#main.py
import streamlit as st
import sqlite3
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
import uuid # Needed for MemorySaver and thread_id in harness

# --- Start of database_manager.py content ---
def init_db():
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'available',
            user_id TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT count(*) FROM seats")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO seats (seat_id, status, user_id) VALUES (?, ?, ?)",
                           [(i, 'available', None) for i in range(1, 6)])
    conn.commit()
    conn.close()

def search_available_seats():
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM seats WHERE status = 'available'")
    available = [row[0] for row in cursor.fetchall()]
    conn.close()
    return available

def get_seat_status(seat_id):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, user_id FROM seats WHERE seat_id = ?", (seat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": row[0], "user_id": row[1]}
    return "not_found"

def book_seat_atomic(seat_id, user_id):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM seats WHERE seat_id = ?", (seat_id,))
    if cursor.fetchone() is None:
        conn.close()
        return "not_found"
    cursor.execute("""
        UPDATE seats SET status = 'booked', user_id = ?, last_updated = CURRENT_TIMESTAMP
        WHERE seat_id = ? AND status = 'available'
    """, (user_id, seat_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return True if success else "not_available"

def cancel_booking(seat_id, user_id):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE seats SET status = 'available', user_id = NULL
        WHERE seat_id = ? AND user_id = ?
    """, (seat_id, user_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def run_janitor():
    conn = sqlite3.connect("railway.db")
    threshold = (datetime.now() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("UPDATE seats SET status = 'available', user_id = NULL WHERE status = 'locked' AND last_updated < ?", (threshold,))
    conn.commit()
    conn.close()

def get_all_seat_statuses():
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id, status, user_id FROM seats ORDER BY seat_id")
    all_seats = cursor.fetchall()
    conn.close()
    return all_seats
# --- End of database_manager.py content ---

# --- Start of agents.py content ---
def search_agent(state):
    """Retrieves available seats."""
    available = search_available_seats()
    return {"history": [f"Available seats: {available}"]}

def booking_agent(state):
    """Attempts an atomic booking."""
    seat_id = state.get("seat_id")
    user_id = state.get("user_id", "default_user")
    result = book_seat_atomic(seat_id, user_id)
    msg = "Success! Seat booked." if result is True else f"Failed: {result}"
    return {"history": [f"Booking status for seat {seat_id}: {msg}"]}

def cancellation_agent(state):
    """Cancels a booking."""
    seat_id = state.get("seat_id")
    user_id = state.get("user_id")
    success = cancel_booking(seat_id, user_id)
    msg = "Cancellation successful." if success else "Cancellation failed: Not your ticket or seat not booked."
    return {"history": [msg]}

def status_agent(state):
    """Retrieves specific seat status."""
    seat_id = state.get("seat_id")
    info = get_seat_status(seat_id)
    if info == "not_found":
        msg = f"Seat {seat_id} does not exist."
    else:
        msg = f"Seat {seat_id} is {info['status']} (User: {info['user_id'] or 'None'})."
    return {"history": [msg]}
# --- End of agents.py content ---

# --- Start of graph_orchestrator.py content ---
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

graph_builder = StateGraph(State)
graph_builder.add_node("reasoning", reasoning_node)
graph_builder.add_node("search", search_agent)
graph_builder.add_node("booking", booking_agent)
graph_builder.add_node("cancellation", cancellation_agent)
graph_builder.add_node("status", status_agent) # New node
graph_builder.add_node("invalid_seat_id_handler", invalid_seat_id_handler)

graph_builder.set_entry_point("reasoning")

graph_builder.add_conditional_edges(
    "reasoning",
    lambda state: [state["action"]], # Ensure it returns a list
    {
        "search": "search",
        "book": "booking",
        "cancel": "cancellation",
        "status": "status",
        "invalid": "invalid_seat_id_handler",
    },
)

graph_builder.add_edge("search", END)
graph_builder.add_edge("booking", END)
graph_builder.add_edge("cancellation", END)
graph_builder.add_edge("status", END)
graph_builder.add_edge("invalid_seat_id_handler", END)
# --- End of graph_orchestrator.py content ---

# --- Start of harness.py content ---
# 1. Initialize Memory for state persistence
memory = MemorySaver()

# 2. Compile the graph with the checkpointer
# This binds the memory to your graph definition
# Note: graph_builder is defined in graph_orchestrator.py content
persistent_graph = graph_builder.compile(checkpointer=memory)

def run_harness(task_input, seat_id=None, user_id="user_123"):
    """Executes a task through the persistent graph and returns the state."""

    # Clean stale locks from previous sessions before running the task
    run_janitor() # Note: run_janitor is defined in database_manager.py content

    # 3. Define the thread_id for stateful persistence
    # Using user_id as thread_id isolates each user's history
    config = {"configurable": {"thread_id": user_id}}

    print(f"--- Harness: Running task '{task_input}' ---")

    # 4. Invoke the persistent graph
    final_state = persistent_graph.invoke(
        {
            "task": task_input,
            "seat_id": seat_id,
            "user_id": user_id,
            "history": []
        },
        config=config
    )

    return final_state
# --- End of harness.py content ---


# Streamlit app layout
st.set_page_config(page_title="🚆 AI Seat Reservation", page_icon="🚆")
st.title("🚆 AI Seat Reservation")

# 1. Initialize Database
if 'db_init' not in st.session_state:
    init_db()
    st.session_state.db_init = True

# 2. UI Options
option = st.radio(
    "Choose an action:",
    ("See Availability", "Book Seat", "Cancel Seat", "Search Seat Status")
)

# 3. Dynamic Input based on selection
seat_id_input = None # Renamed to avoid conflict with `seat_id` in harness.run_harness parameters
if option != "See Availability":
    seat_id_input = st.number_input("Enter Seat ID (1-5):", min_value=1, max_value=5, step=1)

# 4. Process Request
if st.button("Process Request"):
    if option == "See Availability":
        task_input_for_harness = "Check available seats"
        seat_id_for_harness = None
    elif option == "Book Seat":
        task_input_for_harness = f"Book seat {seat_id_input}"
        seat_id_for_harness = seat_id_input
    elif option == "Cancel Seat":
        task_input_for_harness = f"Cancel seat {seat_id_input}"
        seat_id_for_harness = seat_id_input
    elif option == "Search Seat Status":
        task_input_for_harness = f"Status of seat {seat_id_input}"
        seat_id_for_harness = seat_id_input
    else:
        task_input_for_harness = "invalid"
        seat_id_for_harness = None

    with st.spinner("Agent is processing..."):
        # Execute via harness
        # Using a fixed user_id for now as the UI doesn't have an input for it.
        result = run_harness(
            task_input=task_input_for_harness,
            seat_id=seat_id_for_harness,
            user_id="streamlit_user"
        )

        # Display Result
        st.write("### Result:")
        if result and 'history' in result and result['history']:
            st.success(result['history'][-1])
            # Additional display for specific actions if needed
            if result.get('action') == 'book' and 'Success' in result['history'][-1]:
                st.balloons()
        else:
            st.error("No response from the agent or an error occurred.")
