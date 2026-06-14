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


# 1. Initialize Database
if 'db_init' not in st.session_state:
    init_db()
    st.session_state.db_init = True

st.title("🚆 AI Seat Reservation")

# 2. UI Options
option = st.radio(
    "Choose an action:",
    ("See Availability", "Book Seat", "Cancel Seat", "Search Seat Status")
)

# 3. Dynamic Input based on selection
seat_id = None
if option != "See Availability":
    seat_id = st.number_input("Enter Seat ID (1-5):", min_value=1, max_value=5, step=1)

# 4. Process Request
if st.button("Process Request"):
    with st.spinner("Agent is processing..."):
        # Map UI label to task keyword for the agent
        task_map = {
            "See Availability": "Check available seats",
            "Book Seat": f"Book seat {seat_id}",
            "Cancel Seat": f"Cancel seat {seat_id}",
            "Search Seat Status": f"Status of seat {seat_id}"
        }
        
        # Execute via harness
        result = run_harness(task_input=task_map[option], seat_id=seat_id, user_id="user_1")
        
        # Display Result
        st.write("### Result:")
        if result and 'history' in result and result['history']:
            st.success(result['history'][-1])
        else:
            st.error("No response from the agent.")
