"""
Extract Prompt from Image Node for ComfyUI
Extracts positive and negative prompts from image metadata
"""

import json
from PIL import Image
from pathlib import Path


class ExtractPromptFromImage:
    """
    A node that extracts positive and negative prompts from image metadata.
    Supports ComfyUI and Automatic1111 format images.
    Reads directly from image file to preserve metadata.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "image": ("IMAGE",),
                "image_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "extract_prompt"
    CATEGORY = "image/metadata"

    def extract_comfyui_prompt(self, metadata):
        """
        Extract prompt from ComfyUI format metadata.

        Args:
            metadata: PNG metadata dictionary

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        positive = ""
        negative = ""

        # Try to parse 'prompt' key (ComfyUI workflow data)
        if 'prompt' in metadata:
            try:
                prompt_data = json.loads(metadata['prompt'])

                # Search for CLIP Text Encode nodes
                for node_id, node_data in prompt_data.items():
                    if isinstance(node_data, dict):
                        class_type = node_data.get('class_type', '')

                        # CLIPTextEncode nodes contain prompts
                        if 'CLIPTextEncode' in class_type:
                            inputs = node_data.get('inputs', {})
                            text = inputs.get('text', '')

                            # Determine if positive or negative based on node title or position
                            # This is a heuristic - may need adjustment
                            node_title = node_data.get('_meta', {}).get('title', '').lower()

                            if 'negative' in node_title or 'neg' in class_type.lower():
                                negative = text
                            elif not positive:  # First text encode is usually positive
                                positive = text
                            else:
                                # If we already have positive, this might be negative
                                if not negative:
                                    negative = text

            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                print(f"Failed to parse ComfyUI prompt data: {e}")

        return positive, negative

    def extract_automatic1111_prompt(self, metadata):
        """
        Extract prompt from Automatic1111 format metadata.

        Args:
            metadata: PNG metadata dictionary

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        positive = ""
        negative = ""

        # A1111 stores prompts in 'parameters' key
        if 'parameters' in metadata:
            params = metadata['parameters']

            # Format: "positive prompt\nNegative prompt: negative prompt\nSteps: ..."
            if 'Negative prompt:' in params:
                parts = params.split('Negative prompt:', 1)
                positive = parts[0].strip()

                # Extract negative prompt (until the next parameter line)
                negative_part = parts[1]
                # Split by newline and get first line (or until we hit "Steps:" etc)
                lines = negative_part.split('\n')
                negative_lines = []
                for line in lines:
                    # Stop if we hit generation parameters
                    if line.startswith('Steps:') or line.startswith('Sampler:') or line.startswith('CFG'):
                        break
                    negative_lines.append(line.strip())

                negative = '\n'.join(negative_lines).strip()
            else:
                # No negative prompt section, extract just positive
                lines = params.split('\n')
                # Get all lines until we hit parameters
                positive_lines = []
                for line in lines:
                    if line.startswith('Steps:') or line.startswith('Sampler:') or line.startswith('Negative prompt:'):
                        break
                    positive_lines.append(line.strip())
                positive = '\n'.join(positive_lines).strip()

        return positive, negative

    def extract_prompt(self, image=None, image_path=""):
        """
        Extract positive and negative prompts from image file metadata.

        Args:
            image: Optional IMAGE tensor (not supported - will show warning)
            image_path: Path to image file

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        try:
            print(f"\n{'='*60}")
            print(f"Extracting Prompt from Image")
            print(f"{'='*60}\n")

            # Check if image tensor was provided
            if image is not None and not image_path:
                warning_msg = (
                    "⚠️ WARNING: IMAGE tensor input is not supported.\n"
                    "   Image tensors in ComfyUI do not contain metadata.\n"
                    "   Please use 'image_path' input with the file path to the original image.\n"
                    "   Example: C:\\path\\to\\image.png"
                )
                print(warning_msg)
                return ("", "")

            # Validate file path
            if not image_path:
                error_msg = "No image_path provided. Please provide a file path to the image."
                print(f"✗ {error_msg}")
                return ("", "")

            path = Path(image_path)
            if not path.exists():
                error_msg = f"Image file not found: {image_path}"
                print(f"✗ {error_msg}")
                return ("", "")

            if not path.is_file():
                error_msg = f"Path is not a file: {image_path}"
                print(f"✗ {error_msg}")
                return ("", "")

            print(f"Reading image: {path.name}")

            # Open image directly from file
            with Image.open(path) as pil_image:
                # Extract PNG metadata
                metadata = pil_image.info

                if not metadata:
                    print("No metadata found in image")
                    return ("", "")

                print(f"Found metadata keys: {list(metadata.keys())}")

                positive = ""
                negative = ""

                # Try ComfyUI format first
                if 'prompt' in metadata:
                    print("Detected ComfyUI format")
                    positive, negative = self.extract_comfyui_prompt(metadata)

                # Try Automatic1111 format
                if not positive and 'parameters' in metadata:
                    print("Detected Automatic1111 format")
                    positive, negative = self.extract_automatic1111_prompt(metadata)

                # Fallback: check for direct 'positive' and 'negative' keys
                if not positive and 'positive' in metadata:
                    positive = metadata['positive']
                if not negative and 'negative' in metadata:
                    negative = metadata['negative']

                print(f"\n{'='*60}")
                print(f"Extraction Complete")
                print(f"{'='*60}")
                print(f"Positive prompt length: {len(positive)} characters")
                print(f"Negative prompt length: {len(negative)} characters")
                print(f"{'='*60}\n")

                # Preview first 200 characters
                if positive:
                    preview = positive[:200] + "..." if len(positive) > 200 else positive
                    print(f"Positive preview:\n{preview}\n")
                if negative:
                    preview = negative[:200] + "..." if len(negative) > 200 else negative
                    print(f"Negative preview:\n{preview}\n")

                return (positive, negative)

        except Exception as e:
            error_msg = f"Error extracting prompt: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            import traceback
            traceback.print_exc()
            return ("", "")


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "ExtractPromptFromImage": ExtractPromptFromImage,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "ExtractPromptFromImage": "Extract Prompt from Image",
}
