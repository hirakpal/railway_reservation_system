# --- 1. Database & Persistence Setup ---
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

# --- 2. Agent Logic & Graph ---
def agent_logic(state):
    action, sid = state['action'], state['seat_id']
    if action == "book":
        msg = "✅ Success! Seat booked." if update_seat(sid, "book") else "❌ Failed: Seat already booked."
    else: # cancel
        msg = "✅ Cancellation successful." if update_seat(sid, "cancel") else "❌ Failed: Not your ticket or seat is available."
    return {"history": [msg]}

class State(TypedDict): action: str; seat_id: int; history: List[str]
builder = StateGraph(State)
builder.add_node("agent", agent_logic)
builder.set_entry_point("agent"); builder.add_edge("agent", END)
graph = builder.compile(checkpointer=MemorySaver())

# --- 3. Streamlit UI ---
st.set_page_config(layout="wide", page_title="Seat Reservation")
st.title("Seat Reservation System")
init_db()

if 'msg' not in st.session_state: st.session_state.msg = None

col1, col2 = st.columns([1, 2])

with col1:
    # Removed "Check Seat Status" from the list
    action = st.radio("Action:", ["Book Seat", "Cancel Seat"])
    sid = st.number_input("Seat ID (1-5):", 1, 5)
    
    if st.button("Process"):
        act_map = {"Book Seat": "book", "Cancel Seat": "cancel"}
        res = graph.invoke({"action": act_map[action], "seat_id": sid}, {"configurable": {"thread_id": "u1"}})
        st.session_state.msg = res['history'][0]
        st.rerun()

    if st.session_state.msg:
        st.write(st.session_state.msg)

with col2:
    st.subheader("Live Status")
    st.table(pd.read_sql("SELECT * FROM seats ORDER BY seat_id", sqlite3.connect("railway.db")))
