"""
ComfyUI Same Nodes - Custom Nodes Package
Float to String conversion utilities and Batch Image Processor
"""

from .float_to_string import NODE_CLASS_MAPPINGS as FLOAT_MAPPINGS
from .float_to_string import NODE_DISPLAY_NAME_MAPPINGS as FLOAT_DISPLAY_MAPPINGS
from .batch_processor import NODE_CLASS_MAPPINGS as BATCH_MAPPINGS
from .batch_processor import NODE_DISPLAY_NAME_MAPPINGS as BATCH_DISPLAY_MAPPINGS

# Combine all node mappings
NODE_CLASS_MAPPINGS = {
    **FLOAT_MAPPINGS,
    **BATCH_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FLOAT_DISPLAY_MAPPINGS,
    **BATCH_DISPLAY_MAPPINGS,
}

# Export the mappings for ComfyUI to discover
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
