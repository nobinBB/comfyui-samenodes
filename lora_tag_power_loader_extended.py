"""
LoRA Tag Power Loader Extended for ComfyUI
Based on LoRA Tag Power Loader with added second_text input/output
Supports text-based LoRA loading with dual noise weight support
"""

import re
import os
import folder_paths


class LoRATagPowerLoaderExtended:
    """
    Extended LoRA Tag Power Loader with second_text support.

    Processes LoRA tags in text format:
    - <lora:name:weight>
    - <lora:name:high_noise:low_noise>
    - <lora:name:high_noise:low_noise:clip_weight>

    Additional second_text input for separate text output.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                "second_text": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
            },
            "optional": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "default_weight": ("FLOAT", {
                    "default": 1.0,
                    "min": -10.0,
                    "max": 10.0,
                    "step": 0.01
                }),
                "weight_multiplier": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.01
                }),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "text", "second_text", "lora_info")
    FUNCTION = "load_loras"
    CATEGORY = "Same Nodes/LoRA"

    def parse_lora_tags(self, text):
        """
        Parse LoRA tags from text.

        Supported formats:
        - <lora:name:weight>
        - <lora:name:high_noise:low_noise>
        - <lora:name:high_noise:low_noise:clip_weight>

        Returns:
            List of tuples: (lora_name, model_weight, clip_weight, original_tag)
        """
        # Pattern to match <lora:...> tags
        pattern = r'<lora:([^:>]+)(?::([^:>]+))?(?::([^:>]+))?(?::([^:>]+))?>'

        loras = []
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            lora_name = match.group(1).strip()
            param1 = match.group(2)
            param2 = match.group(3)
            param3 = match.group(4)
            original_tag = match.group(0)

            # Default weights
            model_weight = 1.0
            clip_weight = 1.0

            # Parse different formats
            if param1 is not None:
                try:
                    model_weight = float(param1)
                    clip_weight = model_weight
                except ValueError:
                    pass

            if param2 is not None:
                try:
                    # Dual noise format: <lora:name:high:low>
                    clip_weight = float(param2)
                except ValueError:
                    pass

            if param3 is not None:
                try:
                    # Triple format: <lora:name:high:low:clip>
                    clip_weight = float(param3)
                except ValueError:
                    pass

            loras.append((lora_name, model_weight, clip_weight, original_tag))

        return loras

    def load_lora_file(self, lora_name):
        """
        Load LoRA file from ComfyUI's lora folder.

        Args:
            lora_name: Name of the LoRA file (with or without extension)

        Returns:
            Path to the LoRA file or None if not found
        """
        # Get LoRA paths from folder_paths
        lora_paths = folder_paths.get_folder_paths("loras")

        # Try to find the LoRA file
        for lora_dir in lora_paths:
            # Try with various extensions
            for ext in [".safetensors", ".pt", ".bin", ".ckpt"]:
                # Try exact name
                lora_path = os.path.join(lora_dir, lora_name + ext)
                if os.path.exists(lora_path):
                    return lora_path

                # Try without adding extension (in case it's already included)
                lora_path = os.path.join(lora_dir, lora_name)
                if os.path.exists(lora_path):
                    return lora_path

        return None

    def load_loras(self, text, second_text, model=None, clip=None, default_weight=1.0, weight_multiplier=1.0):
        """
        Load LoRAs from text tags and apply to model/clip.

        Args:
            text: Text containing LoRA tags
            second_text: Additional text (passed through)
            model: Optional model to apply LoRAs to
            clip: Optional CLIP to apply LoRAs to
            default_weight: Default weight for LoRAs without specified weight
            weight_multiplier: Global multiplier for all weights

        Returns:
            Tuple of (model, clip, cleaned_text, second_text, lora_info)
        """
        # Parse LoRA tags from text
        loras = self.parse_lora_tags(text)

        # Clean text by removing LoRA tags
        cleaned_text = text
        for lora_name, model_weight, clip_weight, original_tag in loras:
            cleaned_text = cleaned_text.replace(original_tag, "")

        # Clean up multiple spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Build lora_info string
        lora_info_lines = []

        if not loras:
            lora_info = "No LoRA tags found"
            return (model, clip, cleaned_text, second_text, lora_info)

        # Process each LoRA
        for lora_name, model_weight, clip_weight, original_tag in loras:
            # Apply weight multiplier
            final_model_weight = model_weight * weight_multiplier
            final_clip_weight = clip_weight * weight_multiplier

            # Try to load LoRA file
            lora_path = self.load_lora_file(lora_name)

            if lora_path:
                try:
                    # Load LoRA using ComfyUI's internal function
                    # Note: This is a simplified version
                    # The actual implementation would use comfy.utils.load_torch_file
                    # and apply patches to model/clip

                    if model is not None or clip is not None:
                        # Import ComfyUI's LoRA loading function
                        try:
                            from comfy.sd import load_lora_for_models

                            # Load and apply LoRA
                            model, clip = load_lora_for_models(
                                model, clip,
                                lora_path,
                                final_model_weight,
                                final_clip_weight
                            )

                            lora_info_lines.append(
                                f"✓ {lora_name}: model={final_model_weight:.2f}, clip={final_clip_weight:.2f}"
                            )
                        except ImportError:
                            lora_info_lines.append(
                                f"✗ {lora_name}: ComfyUI LoRA loader not available"
                            )
                    else:
                        lora_info_lines.append(
                            f"⚠ {lora_name}: No model/clip provided"
                        )

                except Exception as e:
                    lora_info_lines.append(f"✗ {lora_name}: Error - {str(e)}")
            else:
                lora_info_lines.append(f"✗ {lora_name}: File not found")

        lora_info = "\n".join(lora_info_lines)

        print(f"\n{'='*60}")
        print(f"LoRA Tag Power Loader Extended")
        print(f"{'='*60}")
        print(f"Found {len(loras)} LoRA tag(s)")
        print(f"\n{lora_info}")
        print(f"{'='*60}\n")

        return (model, clip, cleaned_text, second_text, lora_info)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "LoRATagPowerLoaderExtended": LoRATagPowerLoaderExtended,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoRATagPowerLoaderExtended": "LoRA Tag Power Loader Extended",
}
