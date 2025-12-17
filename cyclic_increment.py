"""
Cyclic Increment Node for ComfyUI
Increments a value and cycles back to start after specified iterations
"""

# Global dictionary to store counters and parameters for each node instance
# Structure: {unique_id: {"counter": int, "start_value": int, "cycle_length": int}}
_node_states = {}

class CyclicIncrement:
    """
    A node that increments a value and cycles back to start_value after cycle_length iterations
    Example: start_value=1, cycle_length=4 -> 1, 2, 3, 4, 1, 2, 3, 4...

    IMPORTANT: When cycle_length or start_value changes, the counter resets to 0
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
        # Initialize state for this node if it doesn't exist
        if unique_id not in _node_states:
            _node_states[unique_id] = {
                "counter": 0,
                "start_value": start_value,
                "cycle_length": cycle_length
            }

        # Get current state
        state = _node_states[unique_id]

        # Check if parameters changed - if so, reset counter
        if state["start_value"] != start_value or state["cycle_length"] != cycle_length:
            state["counter"] = 0
            state["start_value"] = start_value
            state["cycle_length"] = cycle_length

        # Get current counter value
        counter = state["counter"]

        # Calculate current position in the cycle (0 to cycle_length-1)
        position = counter % cycle_length

        # Calculate current value
        current_value = start_value + position

        # Increment counter if enabled
        if increment:
            state["counter"] = counter + 1

        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        Force ComfyUI to re-execute this node when increment is enabled
        """
        # Always return NaN to force execution every time
        return float("nan")


# Node display name mapping
NODE_CLASS_MAPPINGS = {
    "CyclicIncrement": CyclicIncrement
}

# Human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CyclicIncrement": "Cyclic Increment"
}
