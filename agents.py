#agents.py
import sqlite3

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
