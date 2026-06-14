import streamlit as st
from harness import run_harness # run_harness is defined in a previous cell
from database_manager import init_db # init_db is defined in a previous cell

# 1. Setup UI
st.set_page_config(page_title="Railway Reservation System", layout="centered")
st.title("🚆 AI Railway Reservation System")

# Initialize DB on first load
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# 2. User Authentication (Mock)
user_id = st.sidebar.text_input("Enter your User ID:", "User_A")

# 3. Features
menu = st.sidebar.radio("Select Action", ["Search", "Book", "Cancel"])

if menu == "Search":
    st.subheader("Available Trains")
    if st.button("Refresh Availability"):
        result = run_harness("search")
        st.success(result)

elif menu == "Book":
    st.subheader("Book a Ticket")
    seat_id = st.number_input("Seat ID", min_value=1, max_value=5)
    if st.button("Confirm Booking"):
        with st.spinner("Agent is processing..."):
            result = run_harness("book", seat_id=seat_id, user_id=user_id)
            st.write(result)

elif menu == "Cancel":
    st.subheader("Cancel Booking")
    seat_id = st.number_input("Seat ID to Cancel", min_value=1, max_value=5)
    if st.button("Confirm Cancellation"):
        with st.spinner("Agent is cancelling..."):
            result = run_harness("cancel", seat_id=seat_id, user_id=user_id)
            st.write(result)

# 4. Footer
st.sidebar.markdown("---")
st.sidebar.info("Capstone Project: Multi-Agent Railway System")
