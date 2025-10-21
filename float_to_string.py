"""
Float to String Conversion Node for ComfyUI
Converts float values to string format
"""

class FloatToString:
    """
    A node that converts float values to string
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {
                    "default": 0.0,
                    "min": -1e9,
                    "max": 1e9,
                    "step": 0.01,
                    "display": "number"
                }),
                "decimal_places": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "display": "number"
                }),
                "use_decimal_places": ("BOOLEAN", {
                    "default": True
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "convert"
    CATEGORY = "utils/conversion"

    def convert(self, value, decimal_places, use_decimal_places):
        """
        Convert float to string

        Args:
            value: Float value to convert
            decimal_places: Number of decimal places to use (if use_decimal_places is True)
            use_decimal_places: Whether to format with specific decimal places

        Returns:
            Tuple containing the string representation
        """
        if use_decimal_places:
            # Format with specific decimal places
            result = f"{value:.{decimal_places}f}"
        else:
            # Convert directly to string (uses Python's default representation)
            result = str(value)

        return (result,)


# Node display name mapping
NODE_CLASS_MAPPINGS = {
    "FloatToString": FloatToString
}

# Human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "FloatToString": "Float to String"
}
