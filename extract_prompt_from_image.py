"""
Extract Prompt from Image Node for ComfyUI
Extracts positive and negative prompts from image metadata
"""

import json
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
import torch


class ExtractPromptFromImage:
    """
    A node that extracts positive and negative prompts from image metadata.
    Supports ComfyUI and Automatic1111 format images.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "extract_prompt"
    CATEGORY = "image/metadata"

    def tensor_to_pil(self, image_tensor):
        """
        Convert ComfyUI image tensor to PIL Image.

        Args:
            image_tensor: Image tensor [B, H, W, C] or [H, W, C]

        Returns:
            PIL Image object
        """
        # Remove batch dimension if present
        if len(image_tensor.shape) == 4:
            image_tensor = image_tensor[0]

        # Convert to numpy and scale to 0-255
        image_np = image_tensor.cpu().numpy()
        image_np = (image_np * 255).astype(np.uint8)

        # Convert to PIL
        return Image.fromarray(image_np)

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

                            if 'negative' in node_title:
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
                # Split by newline and get first line
                negative_lines = negative_part.split('\n')
                negative = negative_lines[0].strip() if negative_lines else ""
            else:
                # No negative prompt section
                positive = params.split('\n')[0].strip()

        return positive, negative

    def extract_prompt(self, image):
        """
        Extract positive and negative prompts from image metadata.

        Args:
            image: ComfyUI image tensor

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        try:
            print(f"\n{'='*60}")
            print(f"Extracting Prompt from Image")
            print(f"{'='*60}\n")

            # Convert tensor to PIL Image
            pil_image = self.tensor_to_pil(image)

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
                print(f"Positive preview: {preview}\n")
            if negative:
                preview = negative[:200] + "..." if len(negative) > 200 else negative
                print(f"Negative preview: {preview}\n")

            return (positive, negative)

        except Exception as e:
            error_msg = f"Error extracting prompt: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return ("", "")


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "ExtractPromptFromImage": ExtractPromptFromImage,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "ExtractPromptFromImage": "Extract Prompt from Image",
}
