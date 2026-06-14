# database_manager.py
import sqlite3
from datetime import datetime, timedelta

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

# NEW FUNCTION ADDED
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
