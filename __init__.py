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

from .lora_wildcard_generator_v2 import NODE_CLASS_MAPPINGS as LORA_V2_MAPPINGS
from .lora_wildcard_generator_v2 import NODE_DISPLAY_NAME_MAPPINGS as LORA_V2_DISPLAY_MAPPINGS

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

from .batch_image_compressor import NODE_CLASS_MAPPINGS as IMAGE_COMPRESSOR_MAPPINGS
from .batch_image_compressor import NODE_DISPLAY_NAME_MAPPINGS as IMAGE_COMPRESSOR_DISPLAY_MAPPINGS

from .images_to_pdf import NODE_CLASS_MAPPINGS as IMAGES_PDF_MAPPINGS
from .images_to_pdf import NODE_DISPLAY_NAME_MAPPINGS as IMAGES_PDF_DISPLAY_MAPPINGS

from .image_format_converter import NODE_CLASS_MAPPINGS as FORMAT_CONVERTER_MAPPINGS
from .image_format_converter import NODE_DISPLAY_NAME_MAPPINGS as FORMAT_CONVERTER_DISPLAY_MAPPINGS

from .seed_step_n import NODE_CLASS_MAPPINGS as SEED_STEP_MAPPINGS
from .seed_step_n import NODE_DISPLAY_NAME_MAPPINGS as SEED_STEP_DISPLAY_MAPPINGS

from .sd_prompt_saver_optimized import NODE_CLASS_MAPPINGS as SD_PROMPT_MAPPINGS
from .sd_prompt_saver_optimized import NODE_DISPLAY_NAME_MAPPINGS as SD_PROMPT_DISPLAY_MAPPINGS

from .impact_wildcard_processor_seed import NODE_CLASS_MAPPINGS as WILDCARD_SEED_MAPPINGS
from .impact_wildcard_processor_seed import NODE_DISPLAY_NAME_MAPPINGS as WILDCARD_SEED_DISPLAY_MAPPINGS

NODE_CLASS_MAPPINGS = {
    **FLOAT_MAPPINGS,
    **BATCH_MAPPINGS,
    **LORA_MAPPINGS,
    **LORA_V2_MAPPINGS,
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
    **IMAGE_COMPRESSOR_MAPPINGS,
    **IMAGES_PDF_MAPPINGS,
    **FORMAT_CONVERTER_MAPPINGS,
    **SEED_STEP_MAPPINGS,
    **SD_PROMPT_MAPPINGS,
    **WILDCARD_SEED_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **FLOAT_DISPLAY_MAPPINGS,
    **BATCH_DISPLAY_MAPPINGS,
    **LORA_DISPLAY_MAPPINGS,
    **LORA_V2_DISPLAY_MAPPINGS,
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
    **IMAGE_COMPRESSOR_DISPLAY_MAPPINGS,
    **IMAGES_PDF_DISPLAY_MAPPINGS,
    **FORMAT_CONVERTER_DISPLAY_MAPPINGS,
    **SEED_STEP_DISPLAY_MAPPINGS,
    **SD_PROMPT_DISPLAY_MAPPINGS,
    **WILDCARD_SEED_DISPLAY_MAPPINGS,
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

# Register custom API routes
WEB_DIRECTORY = "./web"

# Setup custom API endpoints
try:
    from server import PromptServer
    from aiohttp import web
    from .seed_step_n import SeedStepN
    from .impact_wildcard_processor_seed import ImpactWildcardProcessorSeed

    @PromptServer.instance.routes.post("/samenodes/reset_seed_counter")
    async def reset_seed_counter(request):
        """API endpoint to reset seed counter for a specific node instance"""
        try:
            data = await request.json()
            unique_id = data.get("unique_id")

            if unique_id is None:
                return web.json_response({"success": False, "error": "unique_id is required"}, status=400)

            # Call reset_counter method
            success = SeedStepN.reset_counter(unique_id)

            return web.json_response({"success": success})
        except Exception as e:
            print(f"Error in reset_seed_counter API: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

    @PromptServer.instance.routes.post("/samenodes/reset_wildcard_seed_counter")
    async def reset_wildcard_seed_counter(request):
        """API endpoint to reset wildcard seed counter for a specific node instance"""
        try:
            data = await request.json()
            unique_id = data.get("unique_id")

            if unique_id is None:
                return web.json_response({"success": False, "error": "unique_id is required"}, status=400)

            # Call reset_counter method
            success = ImpactWildcardProcessorSeed.reset_counter(unique_id)

            return web.json_response({"success": success})
        except Exception as e:
            print(f"Error in reset_wildcard_seed_counter API: {e}")
            return web.json_response({"success": False, "error": str(e)}, status=500)

except ImportError:
    print("Warning: Could not register custom API routes (server module not available)")
