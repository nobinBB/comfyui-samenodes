"""
ComfyUI Same Nodes - Custom Nodes Package
Float to String conversion utilities, Batch Image Processor, LoRA Wildcard Generator, Civitai Bulk Downloader, Extract Prompt from Image, Queue Empty Checker, and Cyclic Increment
"""

from .float_to_string import NODE_CLASS_MAPPINGS as FLOAT_MAPPINGS
from .float_to_string import NODE_DISPLAY_NAME_MAPPINGS as FLOAT_DISPLAY_MAPPINGS
from .batch_processor import NODE_CLASS_MAPPINGS as BATCH_MAPPINGS
from .batch_processor import NODE_DISPLAY_NAME_MAPPINGS as BATCH_DISPLAY_MAPPINGS
from .lora_wildcard_generator import NODE_CLASS_MAPPINGS as LORA_MAPPINGS
from .lora_wildcard_generator import NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY_MAPPINGS
from .civitai_bulk_downloader import NODE_CLASS_MAPPINGS as CIVITAI_MAPPINGS
from .civitai_bulk_downloader import NODE_DISPLAY_NAME_MAPPINGS as CIVITAI_DISPLAY_MAPPINGS
from .extract_prompt_from_image import NODE_CLASS_MAPPINGS as EXTRACT_MAPPINGS
from .extract_prompt_from_image import NODE_DISPLAY_NAME_MAPPINGS as EXTRACT_DISPLAY_MAPPINGS
from .repeat_text_lines import NODE_CLASS_MAPPINGS as REPEAT_MAPPINGS
from .repeat_text_lines import NODE_DISPLAY_NAME_MAPPINGS as REPEAT_DISPLAY_MAPPINGS
from .queue_empty_checker import NODE_CLASS_MAPPINGS as QUEUE_MAPPINGS
from .queue_empty_checker import NODE_DISPLAY_NAME_MAPPINGS as QUEUE_DISPLAY_MAPPINGS
from .cyclic_increment import NODE_CLASS_MAPPINGS as CYCLIC_MAPPINGS
from .cyclic_increment import NODE_DISPLAY_NAME_MAPPINGS as CYCLIC_DISPLAY_MAPPINGS




NODE_CLASS_MAPPINGS = {
    **FLOAT_MAPPINGS,
    **BATCH_MAPPINGS,
    **LORA_MAPPINGS,
    **CIVITAI_MAPPINGS,
    **EXTRACT_MAPPINGS,
    **REPEAT_MAPPINGS,
    **QUEUE_MAPPINGS,
    **CYCLIC_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FLOAT_DISPLAY_MAPPINGS,
    **BATCH_DISPLAY_MAPPINGS,
    **LORA_DISPLAY_MAPPINGS,
    **CIVITAI_DISPLAY_MAPPINGS,
    **EXTRACT_DISPLAY_MAPPINGS,
    **REPEAT_DISPLAY_MAPPINGS,
    **QUEUE_DISPLAY_MAPPINGS,
    **CYCLIC_DISPLAY_MAPPINGS,
}

# Export the mappings for ComfyUI to discover
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
