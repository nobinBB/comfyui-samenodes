"""
Text Split 3 Node for ComfyUI
Splits text into 3 outputs using <#text#> delimiter
Based on NegativeWildcardsProcessor concept
"""

import re


class TextSplit3:
    """
    A node that splits text into 3 separate outputs.
    Text wrapped in <#...#> markers is extracted and distributed to text_2 and text_3.

    Usage:
    - First <#...#> block goes to text_2
    - Second <#...#> block goes to text_3
    - Remaining text (with markers removed) goes to text_1

    Example:
    Input: "positive prompt <#negative prompt#> <#extra info#> more text"
    Output:
    - text_1: "positive prompt  more text"
    - text_2: "negative prompt"
    - text_3: "extra info"
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("text_1", "text_2", "text_3")
    FUNCTION = "split_text"
    CATEGORY = "utils/text"

    def split_text(self, text):
        """
        Split text into 3 outputs using <#...#> delimiter

        Args:
            text: Input text with optional <#...#> markers

        Returns:
            Tuple of (text_1, text_2, text_3)
        """
        # Pattern to match <#...#>
        pattern = r"<#(.*?)#>"

        # Find all matches
        matches = re.findall(pattern, text, re.DOTALL)

        # Extract text_2 and text_3 from matches
        text_2 = matches[0].strip() if len(matches) >= 1 else ""
        text_3 = matches[1].strip() if len(matches) >= 2 else ""

        # Remove all <#...#> blocks from original text for text_1
        text_1 = re.sub(pattern, "", text, flags=re.DOTALL).strip()

        # Clean up multiple spaces
        text_1 = re.sub(r'\s+', ' ', text_1).strip()

        return (text_1, text_2, text_3)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "TextSplit3": TextSplit3,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "TextSplit3": "Text Split 3",
}
