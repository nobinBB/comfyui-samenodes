"""
TIPO nobin custom - Enhanced TIPO with semantic ban tag filtering
Based on z-tipo-extension by KohakuBlueleaf

Features:
- Semantic similarity checking for ban tags
- Automatic exclusion of related keywords in natural language
- Regeneration if output becomes too short
- Regex support for ban tags
"""

import os
import re
from pathlib import Path
from typing import Any, List, Tuple

import torch
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("[TIPO nobin custom] Warning: sentence-transformers not installed. Semantic filtering disabled.")

# Try to import TIPO from z-tipo-extension
TIPO_AVAILABLE = False
OriginalTIPO = None
TIPO_ERROR_MESSAGE = ""

def try_import_tipo():
    """Try multiple methods to import TIPO from z-tipo-extension"""
    global TIPO_AVAILABLE, OriginalTIPO, TIPO_ERROR_MESSAGE

    import sys
    import importlib
    import importlib.util
    from pathlib import Path as PathlibPath

    # Method 1: Try to find already-loaded z-tipo module in sys.modules
    print("[TIPO nobin custom] Method 1: Checking sys.modules for z-tipo...")
    for module_name in sys.modules:
        if 'tipo' in module_name.lower() and 'nodes' in module_name.lower():
            try:
                module = sys.modules[module_name]
                if hasattr(module, 'TIPO'):
                    OriginalTIPO = module.TIPO
                    TIPO_AVAILABLE = True
                    print(f"[TIPO nobin custom] Success! Found TIPO in {module_name}")
                    return True
            except:
                pass

    # Method 2: Try direct import (if z-tipo is in PYTHONPATH)
    print("[TIPO nobin custom] Method 2: Trying direct import...")
    try:
        # Try importing as if it's already in path
        if 'nodes.tipo' in sys.modules:
            tipo_module = sys.modules['nodes.tipo']
        else:
            tipo_module = importlib.import_module('nodes.tipo')

        if hasattr(tipo_module, 'TIPO'):
            OriginalTIPO = tipo_module.TIPO
            TIPO_AVAILABLE = True
            print("[TIPO nobin custom] Success! Imported nodes.tipo directly")
            return True
    except ImportError as e:
        print(f"[TIPO nobin custom] Direct import failed: {e}")

    # Method 3: Search filesystem
    print("[TIPO nobin custom] Method 3: Searching filesystem...")
    current_dir = PathlibPath(__file__).parent
    custom_nodes_dir = current_dir.parent

    # Try multiple possible names
    possible_names = [
        "z-tipo-extension",
        "ComfyUI-z-tipo-extension",
        "z_tipo_extension",
        "tipo-extension",
        "ComfyUI-tipo",
        "tipo",
    ]

    print(f"[TIPO nobin custom] Searching in: {custom_nodes_dir}")

    for name in possible_names:
        tipo_dir = custom_nodes_dir / name
        tipo_py = tipo_dir / "nodes" / "tipo.py"

        if tipo_py.exists():
            print(f"[TIPO nobin custom] Found tipo.py at: {tipo_py}")
            try:
                # Load the module
                spec = importlib.util.spec_from_file_location(
                    f"tipo_extension_{name}",
                    tipo_py
                )
                if spec and spec.loader:
                    tipo_module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = tipo_module
                    spec.loader.exec_module(tipo_module)

                    if hasattr(tipo_module, 'TIPO'):
                        OriginalTIPO = tipo_module.TIPO
                        TIPO_AVAILABLE = True
                        print(f"[TIPO nobin custom] Success! Loaded TIPO from {tipo_dir}")
                        return True
                    else:
                        print(f"[TIPO nobin custom] Warning: {tipo_py} has no TIPO class")
            except Exception as e:
                print(f"[TIPO nobin custom] Error loading {tipo_py}: {e}")
                import traceback
                traceback.print_exc()

    # All methods failed
    TIPO_ERROR_MESSAGE = (
        f"z-tipo-extension not found!\n"
        f"Searched in: {custom_nodes_dir}\n"
        f"Tried names: {', '.join(possible_names)}\n"
        f"Please install: https://github.com/KohakuBlueleaf/z-tipo-extension"
    )
    print(f"[TIPO nobin custom] {TIPO_ERROR_MESSAGE}")
    return False

# Try to import on module load
try:
    try_import_tipo()
except Exception as e:
    print(f"[TIPO nobin custom] Fatal error during import: {e}")
    import traceback
    traceback.print_exc()


# Semantic similarity model (lazy loaded)
_semantic_model = None
SEMANTIC_THRESHOLD = 0.5  # Fixed threshold for "related" detection


def get_semantic_model():
    """Load sentence-transformers model (cached)"""
    global _semantic_model
    if _semantic_model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            print("[TIPO nobin custom] Loading semantic model (all-MiniLM-L6-v2)...")
            _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[TIPO nobin custom] Semantic model loaded successfully")
        except Exception as e:
            print(f"[TIPO nobin custom] Error loading semantic model: {e}")
    return _semantic_model


def compute_similarity(text1: str, text2: str, model) -> float:
    """Compute semantic similarity between two texts"""
    if model is None:
        return 0.0

    try:
        embeddings = model.encode([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    except Exception as e:
        print(f"[TIPO nobin custom] Similarity computation error: {e}")
        return 0.0


def is_related_to_ban_tags(word: str, ban_tags: List[str], model) -> Tuple[bool, str, float]:
    """
    Check if a word is semantically related to any ban tag

    Returns:
        (is_related, matched_ban_tag, similarity_score)
    """
    if not model or not ban_tags:
        return False, "", 0.0

    word_clean = word.strip().lower()

    for ban_tag in ban_tags:
        # Skip empty tags
        if not ban_tag.strip():
            continue

        # Remove regex syntax for semantic comparison
        ban_clean = ban_tag.strip()
        ban_clean = re.sub(r'[\.\*\+\?\[\]\(\)\{\}\^\$\|\\]', ' ', ban_clean)
        ban_clean = ' '.join(ban_clean.split()).lower()

        if not ban_clean:
            continue

        # Compute similarity
        similarity = compute_similarity(word_clean, ban_clean, model)

        if similarity >= SEMANTIC_THRESHOLD:
            return True, ban_tag, similarity

    return False, "", 0.0


def filter_natural_language(
    nl_text: str,
    ban_tags: List[str],
    model,
    show_log: bool = True
) -> Tuple[str, List[Tuple[str, str, float]]]:
    """
    Filter natural language text to remove semantically related words

    Returns:
        (filtered_text, excluded_words_list)
        excluded_words_list: [(word, matched_ban_tag, similarity)]
    """
    if not nl_text or not model:
        return nl_text, []

    excluded = []
    words = nl_text.split()
    filtered_words = []

    for word in words:
        # Clean word (remove punctuation for checking)
        word_clean = re.sub(r'[^\w\s-]', '', word)

        if not word_clean:
            filtered_words.append(word)
            continue

        is_related, matched_tag, similarity = is_related_to_ban_tags(
            word_clean, ban_tags, model
        )

        if is_related:
            excluded.append((word_clean, matched_tag, similarity))
            if show_log:
                print(f"[TIPO nobin custom] Excluded: '{word_clean}' (similar to '{matched_tag}', score: {similarity:.3f})")
        else:
            filtered_words.append(word)

    filtered_text = ' '.join(filtered_words)
    return filtered_text, excluded


def count_keywords(text: str) -> int:
    """Count meaningful keywords in text"""
    if not text:
        return 0
    # Simple word count, excluding common words
    words = text.split()
    return len([w for w in words if len(w) > 2])


class TIPONobinCustom:
    """
    TIPO with semantic ban tag filtering

    Extends TIPO functionality with:
    - Semantic similarity checking
    - Automatic exclusion of related keywords
    - Regeneration if output is too short
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Get model list from TIPO if available
        if TIPO_AVAILABLE and hasattr(OriginalTIPO, 'INPUT_TYPES'):
            tipo_inputs = OriginalTIPO.INPUT_TYPES()
            model_list = tipo_inputs["required"].get("tipo_model", (["default"], {}))[0]
        else:
            model_list = ["Install z-tipo-extension first"]

        return {
            "required": {
                "tags": ("STRING", {"defaultInput": True, "multiline": True}),
                "nl_prompt": ("STRING", {"defaultInput": True, "multiline": True}),
                "ban_tags": ("STRING", {"defaultInput": True, "multiline": True}),
                "tipo_model": (model_list, {"default": model_list[0]}),
                "format": (
                    "STRING",
                    {
                        "default": """<|special|>,
<|characters|>, <|copyrights|>,
<|artist|>,

<|general|>,

<|extended|>.

<|quality|>, <|meta|>, <|rating|>""",
                        "multiline": True,
                    },
                ),
                "width": ("INT", {"default": 1024, "max": 16384}),
                "height": ("INT", {"default": 1024, "max": 16384}),
                "temperature": ("FLOAT", {"default": 0.5, "step": 0.01}),
                "top_p": ("FLOAT", {"default": 0.95, "step": 0.01}),
                "min_p": ("FLOAT", {"default": 0.05, "step": 0.01}),
                "top_k": ("INT", {"default": 80}),
                "tag_length": (
                    ["very_short", "short", "long", "very_long"],
                    {"default": "long"},
                ),
                "nl_length": (
                    ["very_short", "short", "long", "very_long"],
                    {"default": "long"},
                ),
                "seed": ("INT", {"default": 1234}),
                "device": (["cpu", "cuda"], {"default": "cuda"}),
                # Semantic filtering options
                "minimum_keyword_count": ("INT", {"default": 5, "min": 1, "max": 50}),
                "max_regeneration_attempts": ("INT", {"default": 10, "min": 1, "max": 50}),
                "show_filtering_log": ("BOOLEAN", {"default": True}),
                "enable_semantic_filtering": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = (
        "filtered_output",
        "original_output",
        "regeneration_count",
        "excluded_words"
    )
    FUNCTION = "execute"
    CATEGORY = "SameNodes/TIPO"
    OUTPUT_NODE = True

    DESCRIPTION = (
        "TIPO with semantic ban tag filtering.\n\n"
        "Excludes semantically related words from natural language output.\n"
        "Regenerates if output becomes too short after filtering.\n\n"
        "Requires: sentence-transformers library"
    )

    def execute(
        self,
        tags: str,
        nl_prompt: str,
        ban_tags: str,
        tipo_model: str,
        format: str,
        width: int,
        height: int,
        temperature: float,
        top_p: float,
        min_p: float,
        top_k: int,
        tag_length: str,
        nl_length: str,
        seed: int,
        device: str,
        minimum_keyword_count: int,
        max_regeneration_attempts: int,
        show_filtering_log: bool,
        enable_semantic_filtering: bool,
    ):
        # Check if TIPO is available
        if not TIPO_AVAILABLE or OriginalTIPO is None:
            error_msg = TIPO_ERROR_MESSAGE or "z-tipo-extension not found. Please install it in custom_nodes/"
            print(f"\n{'='*60}")
            print(f"[TIPO nobin custom] ERROR")
            print(error_msg)
            print(f"{'='*60}\n")
            return (
                f"ERROR: {error_msg}",
                "",
                0,
                "z-tipo-extension required"
            )

        # Check if semantic filtering is available
        if enable_semantic_filtering and not SENTENCE_TRANSFORMERS_AVAILABLE:
            return (
                "ERROR: sentence-transformers not installed. Run: pip install sentence-transformers",
                "",
                0,
                "sentence-transformers required"
            )

        # Load semantic model
        model = None
        if enable_semantic_filtering:
            model = get_semantic_model()
            if model is None:
                return (
                    "ERROR: Failed to load semantic model",
                    "",
                    0,
                    "model loading failed"
                )

        # Parse ban tags
        ban_tag_list = [tag.strip() for tag in ban_tags.split(",") if tag.strip()]

        if show_filtering_log:
            print(f"\n{'='*60}")
            print(f"[TIPO nobin custom] Starting generation...")
            print(f"Ban tags: {ban_tag_list}")
            print(f"Minimum keywords: {minimum_keyword_count}")
            print(f"Semantic filtering: {'Enabled' if enable_semantic_filtering else 'Disabled'}")
            print(f"{'='*60}\n")

        # Create TIPO instance and call it
        tipo_instance = OriginalTIPO()

        # Apply semantic filtering with regeneration
        regeneration_count = 0
        current_seed = seed
        all_excluded = []
        filtered_output = ""
        original_output = ""

        for attempt in range(max_regeneration_attempts):
            # Call original TIPO
            tipo_result = tipo_instance.execute(
                tipo_model=tipo_model,
                tags=tags,
                nl_prompt=nl_prompt,
                width=width,
                height=height,
                seed=current_seed,
                tag_length=tag_length,
                nl_length=nl_length,
                ban_tags=ban_tags,
                format=format,
                temperature=temperature,
                top_p=top_p,
                min_p=min_p,
                top_k=top_k,
                device=device,
            )

            # Extract outputs
            # TIPO returns: (prompt, user_prompt, unformatted_prompt, unformatted_user_prompt)
            formatted_prompt = tipo_result[0]
            original_output = formatted_prompt

            # Apply semantic filtering if enabled
            if enable_semantic_filtering and model:
                filtered_output, excluded = filter_natural_language(
                    formatted_prompt,
                    ban_tag_list,
                    model,
                    show_filtering_log
                )

                all_excluded.extend(excluded)

                # Check keyword count
                keyword_count = count_keywords(filtered_output)

                if show_filtering_log:
                    print(f"[TIPO nobin custom] Attempt {attempt + 1}: {keyword_count} keywords")

                if keyword_count >= minimum_keyword_count:
                    break

                # Regenerate with new seed
                regeneration_count += 1
                current_seed += 1

                if show_filtering_log:
                    print(f"[TIPO nobin custom] Regenerating with seed {current_seed}...")
            else:
                # No semantic filtering
                filtered_output = formatted_prompt
                break

        # Format excluded words
        excluded_words_str = "\n".join([
            f"{word} (similar to '{tag}', score: {score:.3f})"
            for word, tag, score in all_excluded
        ])

        if show_filtering_log:
            print(f"\n{'='*60}")
            print(f"[TIPO nobin custom] Generation complete")
            print(f"Regenerations: {regeneration_count}")
            print(f"Excluded words: {len(all_excluded)}")
            print(f"{'='*60}\n")

        return (
            filtered_output,
            original_output,
            regeneration_count,
            excluded_words_str
        )



NODE_CLASS_MAPPINGS = {
    "TIPONobinCustom": TIPONobinCustom,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TIPONobinCustom": "TIPO nobin custom",
}
