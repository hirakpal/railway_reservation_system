#agents.py

# Import the centralized DB helper functions
from database_manager import search_available_seats, book_seat_atomic, cancel_booking, get_seat_status


def search_agent(state):
    """Retrieves available seats."""
    available = search_available_seats()
    return {"history": [f"Available seats: {available}"]}


def booking_agent(state):
    """Attempts an atomic booking."""
    seat_id = state.get("seat_id")
    user_id = state.get("user_id", "default_user")
    result = book_seat_atomic(seat_id, user_id)
    msg = "Success! Seat booked." if result is True else f"Failed: {result}"
    return {"history": [f"Booking status for seat {seat_id}: {msg}"]}


def cancellation_agent(state):
    """Cancels a booking."""
    seat_id = state.get("seat_id")
    user_id = state.get("user_id")
    success = cancel_booking(seat_id, user_id)
    msg = "Cancellation successful." if success else "Cancellation failed: Not your ticket or seat not booked."
    return {"history": [msg]}


def status_agent(state):
    """Retrieves specific seat status."""
    seat_id = state.get("seat_id")
    info = get_seat_status(seat_id)
    if info == "not_found":
        msg = f"Seat {seat_id} does not exist."
    else:
        msg = f"Seat {seat_id} is {info['status']} (User: {info['user_id'] or 'None'})."
    return {"history": [msg]}
