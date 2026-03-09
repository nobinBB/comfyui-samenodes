"""
Text Split 3 Node for ComfyUI
Splits text into 3 outputs using <!text!> and <#text#> delimiters
Based on NegativeWildcardsProcessor concept
"""

import re


class TextSplit3:
    """
    A node that splits text into 3 separate outputs.

    - Text wrapped in <!...!> markers is extracted to text_2
    - Text wrapped in <#...#> markers is extracted to text_3
    - Remaining text (with markers removed) goes to text_1

    Multiple occurrences of each marker type are all extracted.

    Example:
    Input: "positive <!negative1!> text <!negative2!> <#extra1#> more <#extra2#>"
    Output:
    - text_1: "positive text more"
    - text_2: "negative1 negative2"
    - text_3: "extra1 extra2"
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
        Split text into 3 outputs using <!...!> and <#...#> delimiters

        Args:
            text: Input text with optional <!...!> and <#...#> markers

        Returns:
            Tuple of (text_1, text_2, text_3)
        """
        # Pattern to match <!...!>
        pattern_2 = r"<!(.*?)!>"
        # Pattern to match <#...#>
        pattern_3 = r"<#(.*?)#>"

        # Find all matches for text_2 (<!...!>)
        matches_2 = re.findall(pattern_2, text, re.DOTALL)
        # Find all matches for text_3 (<#...#>)
        matches_3 = re.findall(pattern_3, text, re.DOTALL)

        # Join all matches with space
        text_2 = " ".join([m.strip() for m in matches_2 if m.strip()])
        text_3 = " ".join([m.strip() for m in matches_3 if m.strip()])

        # Remove all <!...!> and <#...#> blocks from original text for text_1
        text_1 = re.sub(pattern_2, "", text, flags=re.DOTALL)
        text_1 = re.sub(pattern_3, "", text_1, flags=re.DOTALL)

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
