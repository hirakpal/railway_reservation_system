# main.py multiple seat booking/cancellations

import streamlit as st
import pandas as pd
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Use centralized database manager
from database_manager import init_db, book_seat_atomic, cancel_booking, get_all_seat_data
from version import __version__

# --- 1. Agent Logic & Graph ---
# Fixed State: using seat_ids as a List[int]
class State(TypedDict):
    action: str
    seat_ids: List[int]
    history: List[str]


def agent_logic(state):
    action, sids = state['action'], state['seat_ids']
    results = []
    for sid in sids:
        if action == "book":
            res = book_seat_atomic(sid, state.get("user", "user1"))
            if res is True:
                results.append(f"Seat {sid}: ✅ Booked")
            elif res == "not_found":
                results.append(f"Seat {sid}: ❌ Not found")
            else:
                results.append(f"Seat {sid}: ❌ Failed - {res}")
        else:  # cancel
            success = cancel_booking(sid, state.get("user", "user1"))
            results.append(f"Seat {sid}: {'✅ Cancelled' if success else '❌ Failed'}")
    return {"history": [" | ".join(results)]}


builder = StateGraph(State)
builder.add_node("agent", agent_logic)
builder.set_entry_point("agent"); builder.add_edge("agent", END)
graph = builder.compile(checkpointer=MemorySaver())

# --- 2. Streamlit UI ---
st.set_page_config(layout="wide", page_title="Seat Reservation")
st.title("🚆 Seat Reservation System")
st.caption(f"Version: {__version__}")

# Initialize DB
init_db()

if 'msg' not in st.session_state:
    st.session_state.msg = None

col1, col2 = st.columns([1, 2])

with col1:
    action = st.radio("Action:", ["Book Seat", "Cancel Seat"])
    # multiselect to handle multiple seats
    sids = st.multiselect("Select Seat ID(s):", [1, 2, 3, 4, 5])

    if st.button("Process"):
        if not sids:
            st.warning("Please select at least one seat.")
        else:
            act_map = {"Book Seat": "book", "Cancel Seat": "cancel"}
            res = graph.invoke(
                {"action": act_map[action], "seat_ids": sids, "user": "user1"},
                {"configurable": {"thread_id": "u1"}}
            )
            st.session_state.msg = res['history'][0]
            st.rerun()

    if st.session_state.msg:
        st.info(st.session_state.msg)

with col2:
    st.subheader("Live Status")
    data = get_all_seat_data()
    df = pd.DataFrame(data, columns=["seat_id", "status", "user_id"]) if data else pd.DataFrame(columns=["seat_id", "status", "user_id"])
    st.table(df)
