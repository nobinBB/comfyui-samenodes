"""
ComfyUI Same Nodes - Custom Nodes Package
Float to String conversion utilities, Batch Image Processor, LoRA Wildcard Generator, Embedding Wildcard Generator, Civitai Bulk Downloader, Extract Prompt from Image, Prompt Extractor PosNeg, and Text Split 3
"""
from .float_to_string import NODE_CLASS_MAPPINGS as FLOAT_MAPPINGS
from .float_to_string import NODE_DISPLAY_NAME_MAPPINGS as FLOAT_DISPLAY_MAPPINGS

from .batch_processor import NODE_CLASS_MAPPINGS as BATCH_MAPPINGS
from .batch_processor import NODE_DISPLAY_NAME_MAPPINGS as BATCH_DISPLAY_MAPPINGS

from .lora_wildcard_generator import NODE_CLASS_MAPPINGS as LORA_MAPPINGS
from .lora_wildcard_generator import NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY_MAPPINGS

from .embedding_wildcard_generator import NODE_CLASS_MAPPINGS as EMBEDDING_MAPPINGS
from .embedding_wildcard_generator import NODE_DISPLAY_NAME_MAPPINGS as EMBEDDING_DISPLAY_MAPPINGS

from .civitai_bulk_downloader import NODE_CLASS_MAPPINGS as CIVITAI_MAPPINGS
from .civitai_bulk_downloader import NODE_DISPLAY_NAME_MAPPINGS as CIVITAI_DISPLAY_MAPPINGS

from .extract_prompt_from_image import NODE_CLASS_MAPPINGS as EXTRACT_MAPPINGS
from .extract_prompt_from_image import NODE_DISPLAY_NAME_MAPPINGS as EXTRACT_DISPLAY_MAPPINGS

from .repeat_text_lines import NODE_CLASS_MAPPINGS as REPEAT_MAPPINGS
from .repeat_text_lines import NODE_DISPLAY_NAME_MAPPINGS as REPEAT_DISPLAY_MAPPINGS

from .prompt_extractor_posneg import NODE_CLASS_MAPPINGS as POSNEG_MAPPINGS
from .prompt_extractor_posneg import NODE_DISPLAY_NAME_MAPPINGS as POSNEG_DISPLAY_MAPPINGS

from .text_split_3 import NODE_CLASS_MAPPINGS as TEXT_SPLIT_MAPPINGS
from .text_split_3 import NODE_DISPLAY_NAME_MAPPINGS as TEXT_SPLIT_DISPLAY_MAPPINGS



NODE_CLASS_MAPPINGS = {
    **FLOAT_MAPPINGS,
    **BATCH_MAPPINGS,
    **LORA_MAPPINGS,
    **EMBEDDING_MAPPINGS,
    **CIVITAI_MAPPINGS,
    **EXTRACT_MAPPINGS,
    **REPEAT_MAPPINGS,
    **POSNEG_MAPPINGS,
    **TEXT_SPLIT_MAPPINGS,


}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FLOAT_DISPLAY_MAPPINGS,
    **BATCH_DISPLAY_MAPPINGS,
    **LORA_DISPLAY_MAPPINGS,
    **EMBEDDING_DISPLAY_MAPPINGS,
    **CIVITAI_DISPLAY_MAPPINGS,
    **EXTRACT_DISPLAY_MAPPINGS,
    **REPEAT_DISPLAY_MAPPINGS,
    **POSNEG_DISPLAY_MAPPINGS,
    **TEXT_SPLIT_DISPLAY_MAPPINGS,
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
