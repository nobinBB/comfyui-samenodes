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


class FloatToStringWithPrefix:
    """
    A node that converts float values to string with a prefix
    Example: prefix="Hires倍率", value=1.25 -> "Hires倍率:1.25"
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prefix": ("STRING", {
                    "default": "Hires倍率",
                    "multiline": False
                }),
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

    def convert(self, prefix, value, decimal_places, use_decimal_places):
        """
        Convert float to string with prefix

        Args:
            prefix: Prefix string to prepend (e.g., "Hires倍率")
            value: Float value to convert
            decimal_places: Number of decimal places to use (if use_decimal_places is True)
            use_decimal_places: Whether to format with specific decimal places

        Returns:
            Tuple containing the formatted string (e.g., "Hires倍率:1.25")
        """
        if use_decimal_places:
            # Format with specific decimal places
            value_str = f"{value:.{decimal_places}f}"
        else:
            # Convert directly to string (uses Python's default representation)
            value_str = str(value)

        # Combine prefix and value with colon separator
        result = f"{prefix}:{value_str}"

        return (result,)


# Node display name mapping
NODE_CLASS_MAPPINGS = {
    "FloatToString": FloatToString,
    "FloatToStringWithPrefix": FloatToStringWithPrefix
}

# Human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "FloatToString": "Float to String",
    "FloatToStringWithPrefix": "Float to String with Prefix"
}
