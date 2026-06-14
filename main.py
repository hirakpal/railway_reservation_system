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
    cursor.execute("DROP TABLE IF EXISTS seats")
    cursor.execute("""
        CREATE TABLE seats (
            seat_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'available',
            user_id TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.executemany("INSERT INTO seats (seat_id, status, user_id) VALUES (?, ?, ?)",
                       [(i, 'available', None) for i in range(1, 6)])
    conn.commit()
    conn.close()

def search_available_seats():
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM seats WHERE status = 'available'")
    available_seats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return available_seats

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

def get_all_seat_statuses(): # Added in C1c1nft_R3TE
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id, status, user_id FROM seats ORDER BY seat_id")
    all_seats = cursor.fetchall()
    conn.close()
    return all_seats
# --- End of database_manager.py content ---

# --- Start of agents.py content ---
def search_agent(state):
    available = search_available_seats()
    return {"history": [f"Available seats: {available}"]}

def booking_agent(state):
    seat_id = state.get("seat_id")
    user_id = state.get("user_id", "default_user")
    result = book_seat_atomic(seat_id, user_id)
    msg = "Success! Seat booked." if result is True else f"Failed: {result}"
    return {"history": [f"Booking status for seat {seat_id}: {msg}"]}

def cancellation_agent(state):
    seat_id = state.get("seat_id")
    user_id = state.get("user_id")
    success = cancel_booking(seat_id, user_id)
    return {"history": ["Cancellation successful." if success else "Cancellation failed."]}
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
# --- End of graph_orchestrator.py content ---

# --- Start of harness.py content ---
# 1. Initialize Memory
memory = MemorySaver()

# 2. Re-compile the graph by passing the checkpointer to the builder,
# OR use the existing graph if it already has the checkpointer.
# Since our graph is already compiled, we should re-compile the builder instead:

# No import needed here, assuming graph_builder is globally available from a previous cell's execution
persistent_graph = graph_builder.compile(checkpointer=memory)

def run_harness(task_input, seat_id=None, user_id="user_123"):
    run_janitor()

    # Config defines the thread for persistence
    config = {"configurable": {"thread_id": user_id}}

    print(f"--- Harness: Running task '{task_input}' ---")

    # 3. Use the persistent_graph
    final_state = persistent_graph.invoke(
        {"task": task_input, "seat_id": seat_id, "user_id": user_id, "history": []},
        config=config
    )

    return final_state
# --- End of harness.py content ---


# Page Config
st.set_page_config(page_title="Railway Agent", page_icon="🚆")

# Initialize DB
if 'db_init' not in st.session_state:
    init_db()
    st.session_state.db_init = True

st.title("🚆 AI Railway Reservation")

# Sidebar for User Context
st.sidebar.header("User Context")
user_id = st.sidebar.text_input("User ID", "User_123")

# Main Interface
st.subheader("How can I help you today?")
user_input = st.text_input("Enter your request:", placeholder="e.g., Book seat 3, or cancel my booking")

if st.button("Submit Request"):
    if user_input:
        with st.spinner("Agent is reasoning..."):
            # Run the harness
            result = run_harness(task_input=user_input, user_id=user_id)

            # Display results
            st.success("Task Processed!")
            st.write("### Execution History")
            st.info(result.get("history", ["No history available"]))

            # Display Final State
            st.write("### Current Action Status")
            st.write(f"**Action Performed:** {result.get('action')}")
            st.write(f"**Seat ID:** {result.get('seat_id')}")

            # Display Booking Confirmation if successful
            if result.get('action') == 'book' and result.get('history') and "Success! Seat booked." in result.get('history')[0]:
                st.write("### Booking Confirmation")
                st.success(f"Seat {result.get('seat_id')} has been successfully booked by {user_id}!")

    else:
        st.warning("Please enter a task.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Powered by LangGraph & GPT-4o-mini")
