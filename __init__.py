"""
ComfyUI Same Nodes - Custom Nodes Package
Float to String conversion utilities, Batch Image Processor, LoRA Wildcard Generator, and Upscale Image By Model Custom
"""

from .float_to_string import NODE_CLASS_MAPPINGS as FLOAT_MAPPINGS
from .float_to_string import NODE_DISPLAY_NAME_MAPPINGS as FLOAT_DISPLAY_MAPPINGS
from .batch_processor import NODE_CLASS_MAPPINGS as BATCH_MAPPINGS
from .batch_processor import NODE_DISPLAY_NAME_MAPPINGS as BATCH_DISPLAY_MAPPINGS
from .lora_wildcard_generator import NODE_CLASS_MAPPINGS as LORA_MAPPINGS
from .lora_wildcard_generator import NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY_MAPPINGS
from .upscale_image_by_model_custom import NODE_CLASS_MAPPINGS as UPSCALE_MAPPINGS
from .upscale_image_by_model_custom import NODE_DISPLAY_NAME_MAPPINGS as UPSCALE_DISPLAY_MAPPINGS

# Combine all node mappings
NODE_CLASS_MAPPINGS = {
    **FLOAT_MAPPINGS,
    **BATCH_MAPPINGS,
    **LORA_MAPPINGS,
    **UPSCALE_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FLOAT_DISPLAY_MAPPINGS,
    **BATCH_DISPLAY_MAPPINGS,
    **LORA_DISPLAY_MAPPINGS,
    **UPSCALE_DISPLAY_MAPPINGS,
}

# Export the mappings for ComfyUI to discover
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
