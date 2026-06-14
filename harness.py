from langgraph.checkpoint.memory import MemorySaver
# from graph_orchestrator import graph # The 'graph' object is already available in the notebook scope
# from database_manager import run_janitor # The 'run_janitor' function is already available in the notebook scope
import uuid

# Memory for persistence
memory = MemorySaver()

# The graph is already compiled from graph_orchestrator.py
persistent_graph = graph

def run_harness(task_input, seat_id=None, user_id="user_123"):
    # 1. Operational Maintenance: Run Janitor before any user action
    run_janitor()

    # 2. Setup Persistence: Unique thread for this session
    config = {
        "configurable": {"thread_id": user_id},
        "checkpointer": memory # Pass the checkpointer here
    }

    # 3. Execution & Streaming
    print(f"--- Harness: Running task '{task_input}' ---")
    final_state = None

    # We stream events from the graph
    for event in persistent_graph.stream(
        {"task": task_input, "seat_id": seat_id, "user_id": user_id},
        config=config
    ):
        print(f"Update: {event}")
        final_state = event

    return final_state

# Integration with Streamlit
# You will call this function inside your app.py file
