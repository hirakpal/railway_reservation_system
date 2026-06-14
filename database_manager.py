import sqlite3
from datetime import datetime, timedelta

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

def book_seat_atomic(seat_id, user_id):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE seats SET status = 'booked', user_id = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE seat_id = ? AND status = 'available'
    """, (user_id, seat_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def cancel_booking(seat_id, user_id):
    conn = sqlite3.connect("railway.db")
    cursor = conn.cursor()
    # Ensure the user can only cancel their own booking
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
