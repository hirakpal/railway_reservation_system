#harness.py
from database_manager import run_janitor
from graph_orchestrator import graph


def run_harness(task_input, seat_id=None, user_id="user_123"):
    """Executes a task through the persistent graph and returns the state."""

    # Clean stale locks from previous sessions before running the task
    run_janitor()

    # Define the thread_id for stateful persistence
    config = {"configurable": {"thread_id": user_id}}

    print(f"--- Harness: Running task '{task_input}' ---")

    # Invoke the compiled graph
    final_state = graph.invoke(
        {
            "task": task_input,
            "seat_id": seat_id,
            "user_id": user_id,
            "history": []
        },
        config=config
    )

    return final_state
