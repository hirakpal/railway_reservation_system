#harness.py
from langgraph.checkpoint.memory import MemorySaver
import uuid
# 1. Initialize Memory
memory = MemorySaver()

# 2. Re-compile the graph by passing the checkpointer to the builder,
# OR use the existing graph if it already has the checkpointer.
# Since our graph is already compiled, we should re-compile the builder instead:

# No import needed here, assuming graph_builder is globally available from a previous cell's execution
persistent_graph = graph_builder.compile(checkpointer=memory)

def run_harness(task_input, seat_id=None, user_id="user_123"):
    run_janitor()
    
    # Config defines the thread for persistence
    config = {"configurable": {"thread_id": user_id}}
    
    print(f"--- Harness: Running task '{task_input}' ---")
    
    # 3. Use the persistent_graph
    final_state = persistent_graph.invoke(
        {"task": task_input, "seat_id": seat_id, "user_id": user_id, "history": []}, 
        config=config
    )
        
    return final_state
