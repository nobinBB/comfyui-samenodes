"""
Cyclic Increment Node for ComfyUI
Increments a value and cycles back to start after specified iterations
"""

import time

# Global dictionary to store counters and parameters for each node instance
# Structure: {unique_id: {"counter": int, "start_value": int, "cycle_length": int, "last_time": float}}
_node_states = {}

# Timeout in seconds to detect new queue execution (default: 10 seconds)
QUEUE_TIMEOUT = 10.0

class CyclicIncrement:
    """
    A node that increments a value and cycles back to start_value after cycle_length iterations
    Example: start_value=1, cycle_length=4 -> 1, 2, 3, 4, 1, 2, 3, 4...

    IMPORTANT:
    - When cycle_length or start_value changes, the counter resets to 0
    - When more than 10 seconds elapse between executions, the counter automatically resets to 0
      (this typically indicates a new queue/batch execution)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "start_value": ("INT", {
                    "default": 1,
                    "min": -1000000,
                    "max": 1000000,
                    "step": 1,
                    "display": "number"
                }),
                "cycle_length": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "display": "number"
                }),
                "increment": ("BOOLEAN", {
                    "default": True
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"
    CATEGORY = "utils/increment"
    OUTPUT_NODE = False

    def get_value(self, start_value, cycle_length, increment, unique_id=None):
        """
        Get the current value in the cycle

        Args:
            start_value: Starting value of the cycle
            cycle_length: Number of iterations before cycling back to start
            increment: Whether to increment the counter for next execution
            unique_id: Unique identifier for this node instance (provided by ComfyUI)

        Returns:
            Current value in the cycle
        """
        current_time = time.time()

        # Use a global key if unique_id is not provided
        node_key = unique_id if unique_id is not None else "global"

        # Initialize state for this node if it doesn't exist
        if node_key not in _node_states:
            _node_states[node_key] = {
                "counter": 0,
                "start_value": start_value,
                "cycle_length": cycle_length,
                "last_time": current_time
            }
            print(f"[CyclicIncrement] Initialized node {node_key} with counter=0")

        # Get current state
        state = _node_states[node_key]

        # Check if too much time elapsed (indicates new queue execution)
        time_elapsed = current_time - state.get("last_time", current_time)

        if time_elapsed > QUEUE_TIMEOUT:
            # New queue execution detected - reset counter
            state["counter"] = 0
            print(f"[CyclicIncrement] Timeout detected ({time_elapsed:.1f}s), reset counter to 0")

        # Update last execution time
        state["last_time"] = current_time

        # Check if parameters changed - if so, reset counter
        if state["start_value"] != start_value or state["cycle_length"] != cycle_length:
            state["counter"] = 0
            state["start_value"] = start_value
            state["cycle_length"] = cycle_length
            print(f"[CyclicIncrement] Parameters changed, reset counter to 0")

        # Get current counter value
        counter = state["counter"]

        # Calculate current position in the cycle (0 to cycle_length-1)
        position = counter % cycle_length

        # Calculate current value
        current_value = start_value + position

        print(f"[CyclicIncrement] Node {node_key}: counter={counter}, position={position}, value={current_value}, increment={increment}")

        # Increment counter if enabled
        if increment:
            state["counter"] = counter + 1

        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, start_value, cycle_length, increment, **kwargs):
        """
        Force ComfyUI to re-execute this node when increment is enabled
        """
        if increment:
            # Return a unique value every time to force execution
            return float("nan")
        return start_value


# Node display name mapping
NODE_CLASS_MAPPINGS = {
    "CyclicIncrement": CyclicIncrement
}

# Human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CyclicIncrement": "Cyclic Increment"
}
