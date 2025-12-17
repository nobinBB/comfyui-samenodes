"""
Cyclic Increment Node for ComfyUI
Increments a value and cycles back to start after specified iterations
"""

class CyclicIncrement:
    """
    A node that increments a value and cycles back to start_value after cycle_length iterations
    Example: start_value=1, cycle_length=4 -> 1, 2, 3, 4, 1, 2, 3, 4...
    """

    # Class-level counter to track iterations
    counter = 0

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
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"
    CATEGORY = "utils/increment"

    def get_value(self, start_value, cycle_length, increment):
        """
        Get the current value in the cycle

        Args:
            start_value: Starting value of the cycle
            cycle_length: Number of iterations before cycling back to start
            increment: Whether to increment the counter for next execution

        Returns:
            Current value in the cycle
        """
        # Calculate current position in the cycle (0 to cycle_length-1)
        position = self.counter % cycle_length

        # Calculate current value
        current_value = start_value + position

        # Increment counter if enabled
        if increment:
            CyclicIncrement.counter += 1

        return (current_value,)

    @classmethod
    def IS_CHANGED(cls, start_value, cycle_length, increment):
        """
        Force ComfyUI to re-execute this node when increment is enabled
        """
        if increment:
            # Return NaN to force execution every time
            return float("nan")
        return cls.counter


# Node display name mapping
NODE_CLASS_MAPPINGS = {
    "CyclicIncrement": CyclicIncrement
}

# Human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CyclicIncrement": "Cyclic Increment"
}
