# --- 1. Database Layer ---
def init_db():
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS seats (seat_id INTEGER PRIMARY KEY, status TEXT DEFAULT 'available', user_id TEXT)")
    if cursor.execute("SELECT count(*) FROM seats").fetchone()[0] == 0:
        cursor.executemany("INSERT INTO seats (seat_id, status) VALUES (?, ?)", [(i, 'available') for i in range(1, 6)])
    conn.commit(); conn.close()

def update_seat(seat_id, action, user="user1"):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    if action == "book":
        cursor.execute("UPDATE seats SET status='booked', user_id=? WHERE seat_id=? AND status='available'", (user, seat_id))
    else: # cancel
        cursor.execute("UPDATE seats SET status='available', user_id=NULL WHERE seat_id=? AND user_id=?", (seat_id, user))
    
    success = cursor.rowcount > 0
    conn.commit(); conn.close()
    return success

# --- 2. Logic Layer ---
def agent_logic(state):
    action, sid = state['action'], state['seat_id']
    if action == "book":
        msg = "Success! Seat booked." if update_seat(sid, "book") else "Failed: Seat already booked."
    elif action == "cancel":
        msg = "Cancellation successful." if update_seat(sid, "cancel") else "Failed: Not your ticket or seat is available."
    else: # status
        row = sqlite3.connect("railway.db").execute("SELECT status, user_id FROM seats WHERE seat_id=?", (sid,)).fetchone()
        msg = f"Seat {sid} is {row[0]} (User: {row[1] or 'None'})"
    return {"history": [msg]}

# --- 3. Graph Orchestrator ---
class State(TypedDict): action: str; seat_id: int; history: List[str]
builder = StateGraph(State)
builder.add_node("agent", agent_logic)
builder.set_entry_point("agent"); builder.add_edge("agent", END)
graph = builder.compile(checkpointer=MemorySaver())

# --- 4. Streamlit UI ---
st.set_page_config(layout="wide")
st.title("🚆 Railway Reservation")
init_db()

col1, col2 = st.columns([1, 2])
with col1:
    action = st.radio("Action:", ["Book Seat", "Cancel Seat", "Check Seat Status"])
    sid = st.number_input("Seat ID (1-5):", 1, 5)
    if st.button("Process"):
        act_map = {"Book Seat": "book", "Cancel Seat": "cancel", "Check Seat Status": "status"}
        res = graph.invoke({"action": act_map[action], "seat_id": sid}, {"configurable": {"thread_id": "u1"}})
        st.success(res['history'][0])
        st.rerun()

with col2:
    st.subheader("Live Status")
    st.table(pd.read_sql("SELECT * FROM seats ORDER BY seat_id", sqlite3.connect("railway.db")))
