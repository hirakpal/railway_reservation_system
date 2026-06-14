"""
Update database_manager to include basic seat metadata (position) and helper to fetch full rows.
"""
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "railway.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'available',
            user_id TEXT,
            position TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("SELECT count(*) FROM seats")
    if cursor.fetchone()[0] == 0:
        # seed with positions for 5 seats
        seed = [
            (1, 'available', None, 'window'),
            (2, 'available', None, 'aisle'),
            (3, 'available', None, 'middle'),
            (4, 'available', None, 'aisle'),
            (5, 'available', None, 'window'),
        ]
        cursor.executemany("INSERT INTO seats (seat_id, status, user_id, position) VALUES (?, ?, ?, ?)", seed)
    conn.commit()
    conn.close()


def search_available_seats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id FROM seats WHERE status = 'available'")
    available = [row[0] for row in cursor.fetchall()]
    conn.close()
    return available


def get_seat_status(seat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, user_id FROM seats WHERE seat_id = ?", (seat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": row[0], "user_id": row[1]}
    return "not_found"


def book_seat_atomic(seat_id, user_id):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    threshold = (datetime.now() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute("UPDATE seats SET status = 'available', user_id = NULL WHERE status = 'locked' AND last_updated < ?", (threshold,))
    conn.commit()
    conn.close()


def get_all_seat_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT seat_id, status, user_id, position FROM seats ORDER BY seat_id")
    data = cursor.fetchall()
    conn.close()
    return data
