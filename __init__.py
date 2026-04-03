"""
ComfyUI Same Nodes - Custom Nodes Package
Float to String conversion utilities, Batch Image Processor, LoRA Wildcard Generator, Embedding Wildcard Generator, Embedding Path Resolver, Extract Prompt from Image, Prompt Extractor PosNeg, Text Split 3, and LoRA Text Dual Input
"""
from .float_to_string import NODE_CLASS_MAPPINGS as FLOAT_MAPPINGS
from .float_to_string import NODE_DISPLAY_NAME_MAPPINGS as FLOAT_DISPLAY_MAPPINGS

from .batch_processor import NODE_CLASS_MAPPINGS as BATCH_MAPPINGS
from .batch_processor import NODE_DISPLAY_NAME_MAPPINGS as BATCH_DISPLAY_MAPPINGS

from .lora_wildcard_generator import NODE_CLASS_MAPPINGS as LORA_MAPPINGS
from .lora_wildcard_generator import NODE_DISPLAY_NAME_MAPPINGS as LORA_DISPLAY_MAPPINGS

from .embedding_wildcard_generator import NODE_CLASS_MAPPINGS as EMBEDDING_MAPPINGS
from .embedding_wildcard_generator import NODE_DISPLAY_NAME_MAPPINGS as EMBEDDING_DISPLAY_MAPPINGS

from .extract_prompt_from_image import NODE_CLASS_MAPPINGS as EXTRACT_MAPPINGS
from .extract_prompt_from_image import NODE_DISPLAY_NAME_MAPPINGS as EXTRACT_DISPLAY_MAPPINGS

from .repeat_text_lines import NODE_CLASS_MAPPINGS as REPEAT_MAPPINGS
from .repeat_text_lines import NODE_DISPLAY_NAME_MAPPINGS as REPEAT_DISPLAY_MAPPINGS

from .prompt_extractor_posneg import NODE_CLASS_MAPPINGS as POSNEG_MAPPINGS
from .prompt_extractor_posneg import NODE_DISPLAY_NAME_MAPPINGS as POSNEG_DISPLAY_MAPPINGS

from .text_split_3 import NODE_CLASS_MAPPINGS as TEXT_SPLIT_MAPPINGS
from .text_split_3 import NODE_DISPLAY_NAME_MAPPINGS as TEXT_SPLIT_DISPLAY_MAPPINGS

from .embedding_path_resolver import NODE_CLASS_MAPPINGS as RESOLVER_MAPPINGS
from .embedding_path_resolver import NODE_DISPLAY_NAME_MAPPINGS as RESOLVER_DISPLAY_MAPPINGS

from .input_path_node import NODE_CLASS_MAPPINGS as INPUT_PATH_MAPPINGS
from .input_path_node import NODE_DISPLAY_NAME_MAPPINGS as INPUT_PATH_DISPLAY_MAPPINGS

from .lora_text_dual_input import NODE_CLASS_MAPPINGS as LORA_DUAL_MAPPINGS
from .lora_text_dual_input import NODE_DISPLAY_NAME_MAPPINGS as LORA_DUAL_DISPLAY_MAPPINGS

from .lora_tag_power_loader_extended import NODE_CLASS_MAPPINGS as LORA_POWER_MAPPINGS
from .lora_tag_power_loader_extended import NODE_DISPLAY_NAME_MAPPINGS as LORA_POWER_DISPLAY_MAPPINGS

from .civitai_lora_searcher import NODE_CLASS_MAPPINGS as LORA_SEARCHER_MAPPINGS
from .civitai_lora_searcher import NODE_DISPLAY_NAME_MAPPINGS as LORA_SEARCHER_DISPLAY_MAPPINGS

from .lora_to_civitai_url import NODE_CLASS_MAPPINGS as LORA_URL_MAPPINGS
from .lora_to_civitai_url import NODE_DISPLAY_NAME_MAPPINGS as LORA_URL_DISPLAY_MAPPINGS

NODE_CLASS_MAPPINGS = {
    **FLOAT_MAPPINGS,
    **BATCH_MAPPINGS,
    **LORA_MAPPINGS,
    **EMBEDDING_MAPPINGS,
    **RESOLVER_MAPPINGS,
    **EXTRACT_MAPPINGS,
    **REPEAT_MAPPINGS,
    **POSNEG_MAPPINGS,
    **TEXT_SPLIT_MAPPINGS,
    **INPUT_PATH_MAPPINGS,
    **LORA_DUAL_MAPPINGS,
    **LORA_POWER_MAPPINGS,
    **LORA_SEARCHER_MAPPINGS,
    **LORA_URL_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FLOAT_DISPLAY_MAPPINGS,
    **BATCH_DISPLAY_MAPPINGS,
    **LORA_DISPLAY_MAPPINGS,
    **EMBEDDING_DISPLAY_MAPPINGS,
    **RESOLVER_DISPLAY_MAPPINGS,
    **EXTRACT_DISPLAY_MAPPINGS,
    **REPEAT_DISPLAY_MAPPINGS,
    **POSNEG_DISPLAY_MAPPINGS,
    **TEXT_SPLIT_DISPLAY_MAPPINGS,
    **INPUT_PATH_DISPLAY_MAPPINGS,
    **LORA_DUAL_DISPLAY_MAPPINGS,
    **LORA_POWER_DISPLAY_MAPPINGS,
    **LORA_SEARCHER_DISPLAY_MAPPINGS,
    **LORA_URL_DISPLAY_MAPPINGS,
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
