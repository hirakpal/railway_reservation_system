# main.py multiple seat booking/cancellations with GenAI hooks and user name input

import streamlit as st
import sqlite3
import pandas as pd
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List

# GenAI modules
from nlp_query_processor import parse_nl_query
from genai_recommender import recommend_seats
from pricing_optimizer import optimize_pricing

# --- 1. Database & Persistence Setup ---
def init_db():
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS seats (seat_id INTEGER PRIMARY KEY, status TEXT DEFAULT 'available', user_id TEXT, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    if cursor.execute("SELECT count(*) FROM seats").fetchone()[0] == 0:
        cursor.executemany("INSERT INTO seats (seat_id, status) VALUES (?, ?)", [(i, 'available') for i in range(1, 6)])
    conn.commit(); conn.close()

def update_seat(seat_id, action, user="user1"):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    if action == "book":
        cursor.execute("UPDATE seats SET status='booked', user_id=?, last_updated=CURRENT_TIMESTAMP WHERE seat_id=? AND status='available'", (user, seat_id))
    else: # cancel
        cursor.execute("UPDATE seats SET status='available', user_id=NULL, last_updated=CURRENT_TIMESTAMP WHERE seat_id=? AND user_id=?", (seat_id, user))
    success = cursor.rowcount > 0
    conn.commit(); conn.close()
    return success

# --- 2. Agent Logic & Graph ---
def agent_logic(state):
    action, sids = state['action'], state['seat_ids']
    user = state.get('user', 'user1')
    results = []
    for sid in sids:
        if action == "book":
            success = update_seat(sid, 'book', user)
            results.append(f"Seat {sid}: {'✅ Booked' if success else '❌ Failed'}")
        else: # cancel
            success = update_seat(sid, 'cancel', user)
            results.append(f"Seat {sid}: {'✅ Cancelled' if success else '❌ Failed'}")
    return {"history": [" | ".join(results)]}

# Fixed State: using seat_ids as a List[int]
class State(TypedDict): 
    action: str
    seat_ids: List[int]
    user: str
    history: List[str]

builder = StateGraph(State)
builder.add_node("agent", agent_logic)
builder.set_entry_point("agent"); builder.add_edge("agent", END)
graph = builder.compile(checkpointer=MemorySaver())

# --- 3. Streamlit UI ---
st.set_page_config(layout="wide", page_title="Seat Reservation")
st.title("🚆 Seat Reservation System")
init_db()

if 'msg' not in st.session_state: st.session_state.msg = None

col1, col2 = st.columns([1, 2])

with col1:
    action = st.radio("Action:", ["Book Seat", "Cancel Seat"])
    # Changed to multiselect to handle multiple seats
    sids = st.multiselect("Select Seat ID(s):", [1, 2, 3, 4, 5])
    user = st.text_input("User name:", value="user1")

    st.markdown("---")
    st.subheader("GenAI: Natural Language Query")
    nl = st.text_input("Ask in natural language (e.g. 'I want an aisle seat near the entrance')")
    if st.button("Process NL Query"):
        prefs = parse_nl_query(nl)
        available = [r[0] for r in pd.read_sql("SELECT seat_id FROM seats WHERE status='available'", sqlite3.connect("railway.db")).values]
        recs = recommend_seats(available, prefs)
        st.session_state.msg = f"Recommendations: {recs} based on {prefs}"
        st.rerun()

    st.markdown("---")
    if st.button("Process"):
        if not sids:
            st.warning("Please select at least one seat.")
        elif not user:
            st.warning("Please enter a user name.")
        else:
            act_map = {"Book Seat": "book", "Cancel Seat": "cancel"}
            # pass user into the graph state
            res = graph.invoke(
                {"action": act_map[action], "seat_ids": sids, "user": user}, 
                {"configurable": {"thread_id": user}}
            )
            st.session_state.msg = res['history'][0]
            st.rerun()

    if st.session_state.msg:
        st.info(st.session_state.msg)

with col2:
    st.subheader("Live Status")
    conn = sqlite3.connect("railway.db")
    seat_df = pd.read_sql("SELECT * FROM seats ORDER BY seat_id", conn)
    st.table(seat_df)

    st.subheader("GenAI: Pricing Suggestions")
    seat_data = list(seat_df.itertuples(index=False, name=None))
    prices = optimize_pricing(seat_data)
    st.write(prices)

