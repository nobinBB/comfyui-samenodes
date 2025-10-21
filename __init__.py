"""
ComfyUI Same Nodes - Custom Nodes Package
Float to String conversion utilities
"""

from .float_to_string import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Export the mappings for ComfyUI to discover
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
