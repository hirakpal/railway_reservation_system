#harness.py
from langgraph.checkpoint.memory import MemorySaver
import uuid

# 1. Initialize Memory for state persistence
memory = MemorySaver()

# 2. Compile the graph with the checkpointer
# This binds the memory to your graph definition
persistent_graph = graph_builder.compile(checkpointer=memory)

def run_harness(task_input, seat_id=None, user_id="user_123"):
    """Executes a task through the persistent graph and returns the state."""
    
    # Clean stale locks from previous sessions before running the task
    run_janitor()
    
    # 3. Define the thread_id for stateful persistence
    # Using user_id as thread_id isolates each user's history
    config = {"configurable": {"thread_id": user_id}}
    
    print(f"--- Harness: Running task '{task_input}' ---")
    
    # 4. Invoke the persistent graph
    final_state = persistent_graph.invoke(
        {
            "task": task_input, 
            "seat_id": seat_id, 
            "user_id": user_id, 
            "history": []
        }, 
        config=config
    )
        
    return final_state
