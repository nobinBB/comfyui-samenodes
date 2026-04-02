"""
LoRA Text Dual Input Node for ComfyUI
Provides two text input fields - one for LoRA syntax and one for additional text output
"""


class LoRATextDualInput:
    """
    A node with two text input fields.
    The first text field is for LoRA syntax (to be processed by other nodes).
    The second text field is output as second_text.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # First text input - for LoRA syntax
                "text": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                # Second text input - for additional text
                "second_text": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "second_text")
    FUNCTION = "process_text"
    CATEGORY = "Same Nodes/LoRA"

    def process_text(self, text, second_text):
        """
        Process two text inputs and return them as outputs.

        Args:
            text: First text input (typically contains LoRA syntax)
            second_text: Second text input (additional text)

        Returns:
            Tuple of (text, second_text)
        """
        return (text, second_text)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "LoRATextDualInput": LoRATextDualInput,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoRATextDualInput": "LoRA Text Dual Input",
}
