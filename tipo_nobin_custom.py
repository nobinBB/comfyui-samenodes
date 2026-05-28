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

# TIPO will be imported lazily when needed
_TIPO_CLASS = None
_TIPO_IMPORT_ATTEMPTED = False

# Cache for ban tag embeddings (optimization)
_BAN_TAG_EMBEDDINGS_CACHE = {}


def get_ban_tag_embeddings(ban_tags: List[str], model) -> dict:
    """
    Get embeddings for ban tags (with caching)

    Returns:
        dict: {ban_tag: embedding_vector}
    """
    if not model or not ban_tags:
        return {}

    # Create cache key from ban tags
    cache_key = tuple(sorted(ban_tags))

    # Check cache
    if cache_key in _BAN_TAG_EMBEDDINGS_CACHE:
        return _BAN_TAG_EMBEDDINGS_CACHE[cache_key]

    # Compute embeddings
    embeddings = {}
    clean_tags = []
    original_tags = []

    for ban_tag in ban_tags:
        if not ban_tag.strip():
            continue

        # Remove regex syntax for semantic comparison
        ban_clean = ban_tag.strip()
        ban_clean = re.sub(r'[\.\*\+\?\[\]\(\)\{\}\^\$\|\\]', ' ', ban_clean)
        ban_clean = ' '.join(ban_clean.split()).lower()

        if ban_clean:
            clean_tags.append(ban_clean)
            original_tags.append(ban_tag)

    if clean_tags:
        # Batch encode all ban tags at once (faster!)
        try:
            encoded = model.encode(clean_tags, show_progress_bar=False)
            for i, tag in enumerate(original_tags):
                embeddings[tag] = encoded[i]
        except Exception as e:
            print(f"[TIPO nobin custom] Error encoding ban tags: {e}")

    # Cache the result
    _BAN_TAG_EMBEDDINGS_CACHE[cache_key] = embeddings

    return embeddings


def get_tipo_class():
    """Lazy load TIPO class when first needed"""
    global _TIPO_CLASS, _TIPO_IMPORT_ATTEMPTED

    if _TIPO_IMPORT_ATTEMPTED:
        return _TIPO_CLASS

    _TIPO_IMPORT_ATTEMPTED = True

    import sys
    import importlib
    import importlib.util
    from pathlib import Path as PathlibPath

    print("[TIPO nobin custom] Attempting to import TIPO...")

    # Method 1: Check sys.modules (z-tipo should be loaded by ComfyUI by now)
    print("[TIPO nobin custom] Method 1: Checking sys.modules...")
    for module_name, module in list(sys.modules.items()):
        if 'tipo' in module_name.lower():
            try:
                if hasattr(module, 'TIPO'):
                    _TIPO_CLASS = module.TIPO
                    print(f"[TIPO nobin custom] ✓ Found TIPO in sys.modules['{module_name}']")
                    return _TIPO_CLASS
            except:
                pass

    # Method 2: Try direct import
    print("[TIPO nobin custom] Method 2: Trying direct import...")
    try:
        import nodes.tipo
        if hasattr(nodes.tipo, 'TIPO'):
            _TIPO_CLASS = nodes.tipo.TIPO
            print("[TIPO nobin custom] ✓ Successfully imported nodes.tipo")
            return _TIPO_CLASS
    except ImportError:
        pass

    # Method 3: Filesystem search
    print("[TIPO nobin custom] Method 3: Searching filesystem...")
    current_dir = PathlibPath(__file__).parent
    custom_nodes_dir = current_dir.parent

    possible_names = [
        "z-tipo-extension",
        "ComfyUI-z-tipo-extension",
        "z_tipo_extension",
        "z-tipo",
        "tipo-extension",
        "ComfyUI-tipo",
        "tipo",
    ]

    for name in possible_names:
        tipo_dir = custom_nodes_dir / name
        tipo_py = tipo_dir / "nodes" / "tipo.py"

        if tipo_py.exists():
            print(f"[TIPO nobin custom] Found: {tipo_py}")
            try:
                spec = importlib.util.spec_from_file_location(
                    f"tipo_loaded_{name}",
                    tipo_py
                )
                if spec and spec.loader:
                    tipo_module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = tipo_module
                    spec.loader.exec_module(tipo_module)

                    if hasattr(tipo_module, 'TIPO'):
                        _TIPO_CLASS = tipo_module.TIPO
                        print(f"[TIPO nobin custom] ✓ Loaded TIPO from {tipo_dir}")
                        return _TIPO_CLASS
            except Exception as e:
                print(f"[TIPO nobin custom] Error loading {tipo_py}: {e}")

    # All methods failed
    error_msg = (
        f"z-tipo-extension not found!\n"
        f"Searched in: {custom_nodes_dir}\n"
        f"Tried: {', '.join(possible_names)}"
    )
    print(f"[TIPO nobin custom] ✗ {error_msg}")
    return None


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


def is_related_to_ban_tags_batch(
    words: List[str],
    ban_tag_embeddings: dict,
    model
) -> dict:
    """
    Check if words are semantically related to any ban tag (batch processing)

    Args:
        words: List of words to check
        ban_tag_embeddings: Pre-computed ban tag embeddings
        model: Semantic model

    Returns:
        dict: {word: (is_related, matched_ban_tag, similarity_score)}
    """
    if not model or not words or not ban_tag_embeddings:
        return {word: (False, "", 0.0) for word in words}

    results = {}

    # Clean words
    word_clean_map = {}
    clean_words = []
    for word in words:
        cleaned = word.strip().lower()
        if cleaned:
            word_clean_map[word] = cleaned
            clean_words.append(cleaned)

    if not clean_words:
        return {word: (False, "", 0.0) for word in words}

    try:
        # Batch encode all words at once (faster!)
        word_embeddings = model.encode(clean_words, show_progress_bar=False)

        # Check each word against ban tags
        for i, word in enumerate(words):
            if word not in word_clean_map:
                results[word] = (False, "", 0.0)
                continue

            word_embedding = word_embeddings[i]
            max_similarity = 0.0
            matched_tag = ""

            # Compare against all ban tag embeddings
            for ban_tag, ban_embedding in ban_tag_embeddings.items():
                similarity = float(np.dot(word_embedding, ban_embedding) / (
                    np.linalg.norm(word_embedding) * np.linalg.norm(ban_embedding)
                ))

                if similarity > max_similarity:
                    max_similarity = similarity
                    matched_tag = ban_tag

            is_related = max_similarity >= SEMANTIC_THRESHOLD
            results[word] = (is_related, matched_tag, max_similarity)

    except Exception as e:
        print(f"[TIPO nobin custom] Error in batch similarity: {e}")
        results = {word: (False, "", 0.0) for word in words}

    return results


def filter_generated_content(
    original_input: str,
    tipo_output: str,
    ban_tags: List[str],
    model,
    show_log: bool = True
) -> Tuple[str, List[Tuple[str, str, float]]]:
    """
    Filter only the content ADDED by TIPO, keep original input intact

    IMPORTANT: Original user input is NEVER filtered, even if it matches ban tags
    Only TIPO's generated additions are filtered

    Uses regex for tags and semantic similarity for natural language

    Args:
        original_input: Original user input (tags + nl_prompt) - PROTECTED
        tipo_output: TIPO's full output (original + generated)
        ban_tags: List of ban tag patterns
        model: Semantic model
        show_log: Show filtering logs

    Returns:
        (filtered_output, excluded_words_list)
    """
    if not tipo_output:
        return tipo_output, []

    # Normalize original input for matching
    original_normalized = original_input.strip()

    if show_log:
        print(f"[TIPO nobin custom] Original input (PROTECTED): '{original_normalized[:100]}...'")

    # Find what TIPO added by removing original input from output
    # TIPO typically appends to the original input
    if original_normalized in tipo_output:
        # Find where original input appears
        idx = tipo_output.find(original_normalized)

        # Everything after original input is generated content
        generated_part = tipo_output[idx + len(original_normalized):].strip()

        # Remove leading comma/separator if present
        generated_part = generated_part.lstrip(',').lstrip('\n').strip()

        if show_log:
            print(f"[TIPO nobin custom] Generated content (will filter): '{generated_part[:100]}...'")
    else:
        # Can't find exact match - fallback: filter everything (not ideal)
        if show_log:
            print("[TIPO nobin custom] Warning: Could not find original input in output, filtering all")
        generated_part = tipo_output
        original_normalized = ""

    # If no generated content, just return original
    if not generated_part:
        return original_normalized, []

    # Split generated content into tags and natural language
    # Format is usually: "tags, tags, tags\nnatural language"
    if '\n' in generated_part:
        generated_tags, generated_nl = generated_part.split('\n', 1)
    else:
        # All tags, no NL
        generated_tags = generated_part
        generated_nl = ""

    # Filter generated tags with regex
    filtered_tags_excluded = []
    if generated_tags:
        filtered_generated_tags, filtered_tags_excluded = filter_tags_regex(
            generated_tags,
            ban_tags,
            show_log
        )
    else:
        filtered_generated_tags = ""

    # Filter generated natural language with semantic similarity
    excluded_nl = []
    if generated_nl and model:
        filtered_generated_nl, excluded_nl = filter_natural_language(
            generated_nl,
            ban_tags,
            model,
            show_log
        )
    else:
        filtered_generated_nl = generated_nl

    # Reconstruct: original (protected) + filtered generated
    result_parts = []

    # Always include original input first (never filtered!)
    if original_normalized:
        result_parts.append(original_normalized)

    # Add filtered generated tags
    if filtered_generated_tags:
        result_parts.append(filtered_generated_tags)

    # Join tags with comma
    if len(result_parts) > 0:
        tags_output = ', '.join(result_parts)
    else:
        tags_output = ""

    # Add filtered NL
    if tags_output and filtered_generated_nl:
        final_output = f"{tags_output}\n{filtered_generated_nl}"
    elif tags_output:
        final_output = tags_output
    elif filtered_generated_nl:
        final_output = filtered_generated_nl
    else:
        final_output = ""

    return final_output, excluded_nl


def filter_tags_regex(tags_text: str, ban_tags: List[str], show_log: bool = True) -> Tuple[str, List[str]]:
    """
    Filter tags using regex patterns

    Args:
        tags_text: Comma-separated tags
        ban_tags: List of regex patterns
        show_log: Show filtering logs

    Returns:
        (filtered_tags, excluded_tags)
    """
    if not tags_text or not ban_tags:
        return tags_text, []

    tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
    filtered_tags = []
    excluded_tags = []

    for tag in tags:
        excluded = False
        for ban_pattern in ban_tags:
            if not ban_pattern.strip():
                continue
            try:
                if re.search(ban_pattern, tag, re.IGNORECASE):
                    excluded_tags.append(tag)
                    if show_log:
                        print(f"[TIPO nobin custom] Excluded tag: '{tag}' (matched '{ban_pattern}')")
                    excluded = True
                    break
            except re.error:
                # Invalid regex, skip
                pass

        if not excluded:
            filtered_tags.append(tag)

    return ', '.join(filtered_tags), excluded_tags


def filter_natural_language(
    nl_text: str,
    ban_tags: List[str],
    model,
    show_log: bool = True
) -> Tuple[str, List[Tuple[str, str, float]]]:
    """
    Filter natural language text to remove semantically related words (optimized with batching)

    Returns:
        (filtered_text, excluded_words_list)
        excluded_words_list: [(word, matched_ban_tag, similarity)]
    """
    if not nl_text or not model:
        return nl_text, []

    # Get ban tag embeddings (cached!)
    ban_tag_embeddings = get_ban_tag_embeddings(ban_tags, model)

    if not ban_tag_embeddings:
        return nl_text, []

    excluded = []
    words = nl_text.split()

    # Clean words
    word_map = {}  # original_word -> cleaned_word
    words_to_check = []

    for word in words:
        word_clean = re.sub(r'[^\w\s-]', '', word)
        if word_clean:
            word_map[word] = word_clean
            words_to_check.append(word_clean)

    if not words_to_check:
        return nl_text, []

    # Batch check all words
    similarity_results = is_related_to_ban_tags_batch(
        words_to_check,
        ban_tag_embeddings,
        model
    )

    # Filter based on results
    filtered_words = []
    for word in words:
        if word not in word_map:
            filtered_words.append(word)
            continue

        word_clean = word_map[word]
        is_related, matched_tag, similarity = similarity_results.get(
            word_clean, (False, "", 0.0)
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


def deduplicate_tags(tags_text: str) -> str:
    """
    Remove duplicate tags while preserving order

    Example:
        Input: "1girl, standing, seiza, standing, seiza, armor"
        Output: "1girl, standing, seiza, armor"
    """
    if not tags_text:
        return tags_text

    tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
    seen = set()
    unique_tags = []

    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)

    return ', '.join(unique_tags)


def filter_character_tags_from_text(tags_text: str, show_log: bool = True) -> Tuple[str, List[str]]:
    """
    Filter character tags from comma-separated tags

    Character tags typically follow the pattern: character_name_(series)
    For example: "hatsune_miku_(vocaloid)", "asuna_(sao)"

    Args:
        tags_text: Comma-separated tags
        show_log: Show filtering logs

    Returns:
        (filtered_tags, removed_character_tags)
    """
    if not tags_text:
        return tags_text, []

    tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
    filtered_tags = []
    removed_tags = []

    # Pattern: anything_(anything) - matches character tags like "character_name_(series)"
    # Allows multiple underscores in character name (e.g., "hatsune_miku_(vocaloid)")
    character_tag_pattern = re.compile(r'.+_\(.+\)$')

    for tag in tags:
        if character_tag_pattern.match(tag):
            removed_tags.append(tag)
            if show_log:
                print(f"[TIPO nobin custom] Removed character tag: '{tag}'")
        else:
            filtered_tags.append(tag)

    return ', '.join(filtered_tags), removed_tags


def check_output_quality(output: str, input_tags: str, max_word_repetition: int = 3) -> Tuple[bool, str]:
    """
    Check output quality to detect broken/corrupted TIPO generations

    Checks:
        1. Excessive word repetition
        2. Contradictory tags (1girl + no humans, solo + multiple)
        3. Broken syntax (unescaped brackets)

    Returns:
        (is_valid, reason)
    """
    if not output:
        return (True, "")

    tags = [t.strip() for t in output.split(',') if t.strip()]

    # Check 1: Excessive repetition
    word_count = {}
    for tag in tags:
        words = tag.lower().split()
        for word in words:
            if len(word) > 2:
                word_count[word] = word_count.get(word, 0) + 1
                if word_count[word] > max_word_repetition:
                    return (False, f"Excessive repetition: '{word}' appears {word_count[word]} times")

    # Check 2: Contradictory tags
    tags_lower = [t.lower() for t in tags]
    has_girl = any('girl' in t and 'no' not in t for t in tags_lower)
    has_no_humans = 'no humans' in tags_lower
    if has_girl and has_no_humans:
        return (False, "Contradiction: character tag + 'no humans'")

    has_solo = 'solo' in tags_lower
    has_multiple = any('multiple' in t for t in tags_lower)
    if has_solo and has_multiple:
        return (False, "Contradiction: 'solo' + 'multiple'")

    # Check 3: Broken syntax
    if '][' in output:
        return (False, "Broken syntax: '][' found")

    unescaped_open = output.count('[') - output.count('\\[')
    unescaped_close = output.count(']') - output.count('\\]')
    if unescaped_open > 0 or unescaped_close > 0:
        return (False, "Broken syntax: unescaped brackets found")

    return (True, "")


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
        # Try to get model list from TIPO
        # Don't use lazy loading here - if it fails, provide empty list
        # The actual validation happens at execution time
        try:
            import sys
            # Check if tipo is already loaded in sys.modules
            tipo_module = None
            for module_name, module in list(sys.modules.items()):
                if 'tipo' in module_name.lower() and hasattr(module, 'TIPO'):
                    tipo_module = module
                    break

            if tipo_module and hasattr(tipo_module, 'MODEL_NAME_LIST'):
                model_list = tipo_module.MODEL_NAME_LIST
            elif tipo_module and hasattr(tipo_module.TIPO, 'INPUT_TYPES'):
                tipo_inputs = tipo_module.TIPO.INPUT_TYPES()
                model_list = tipo_inputs["required"].get("tipo_model", ([], {}))[0]
            else:
                # Fallback: empty list will show as dropdown, won't cause errors
                model_list = []
        except Exception as e:
            # If anything fails, use empty list
            model_list = []

        # If model_list is empty, use a placeholder that won't break
        if not model_list:
            model_list = ["default"]

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
                "minimum_keyword_count": ("INT", {"default": 3, "min": 1, "max": 50}),
                "max_regeneration_attempts": ("INT", {"default": 4, "min": 1, "max": 50}),
                "show_filtering_log": ("BOOLEAN", {"default": True}),
                "enable_semantic_filtering": ("BOOLEAN", {"default": True}),
                "remove_duplicate_tags": ("BOOLEAN", {"default": True}),
                "enable_quality_check": ("BOOLEAN", {"default": True}),
                "max_word_repetition": ("INT", {"default": 3, "min": 2, "max": 10}),
                "filter_character_tags": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = (
        "filtered_output",
        "original_output",
        "regeneration_count",
        "excluded_words",
        "removed_character_tags"
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
        remove_duplicate_tags: bool = True,
        enable_quality_check: bool = True,
        max_word_repetition: int = 3,
        filter_character_tags: bool = False,
    ):
        # Get TIPO class (lazy load)
        TIPO = get_tipo_class()
        if TIPO is None:
            error_msg = "z-tipo-extension not found or failed to load. Check console for details."
            print(f"\n{'='*60}")
            print(f"[TIPO nobin custom] ERROR: {error_msg}")
            print(f"{'='*60}\n")
            return (
                f"ERROR: {error_msg}",
                "",
                0,
                "z-tipo-extension required",
                ""
            )

        # Check if semantic filtering is available
        if enable_semantic_filtering and not SENTENCE_TRANSFORMERS_AVAILABLE:
            return (
                "ERROR: sentence-transformers not installed. Run: pip install sentence-transformers",
                "",
                0,
                "sentence-transformers required",
                ""
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
                    "model loading failed",
                    ""
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
        tipo_instance = TIPO()

        # Store original user input (to protect from filtering)
        original_user_input = f"{tags} {nl_prompt}".strip()

        # Apply semantic filtering with regeneration
        regeneration_count = 0
        current_seed = seed
        all_excluded = []
        all_removed_character_tags = []
        filtered_output = ""
        original_output = ""

        for attempt in range(max_regeneration_attempts):
            # Call original TIPO
            # Pass ban_tags to TIPO so it can stop generation early when banned tags appear
            # (without ban_tags, TIPO generates longer outputs that can overflow context)
            try:
                tipo_result = tipo_instance.execute(
                    tipo_model=tipo_model,
                    tags=tags,
                    nl_prompt=nl_prompt,
                    width=width,
                    height=height,
                    seed=current_seed,
                    tag_length=tag_length,
                    nl_length=nl_length,
                    ban_tags=ban_tags,  # Pass to TIPO for early stopping
                    format=format,
                    temperature=temperature,
                    top_p=top_p,
                    min_p=min_p,
                    top_k=top_k,
                    device=device,
                )
            except ValueError as e:
                # Handle TIPO context window overflow (1024 token limit)
                error_msg = str(e)
                if "context window" in error_msg or "exceed" in error_msg.lower():
                    if show_filtering_log:
                        print(f"\n[TIPO nobin custom] WARNING: TIPO context window overflow!")
                        print(f"  Error: {error_msg}")
                        print(f"  Cause: Input + generation exceeds TIPO's 1024 token limit")
                        print(f"  Fallback: Returning original input without TIPO additions\n")
                    # Return original input as-is (no TIPO additions)
                    original_combined = tags
                    if nl_prompt:
                        original_combined = f"{tags}\n{nl_prompt}" if tags else nl_prompt
                    filtered_output = original_combined
                    original_output = original_combined
                    # Apply dedup if enabled
                    if remove_duplicate_tags:
                        filtered_output = deduplicate_tags(filtered_output)
                    return (
                        filtered_output,
                        original_output,
                        regeneration_count,
                        f"TIPO context overflow - returned original input. Reduce input length or use shorter tag_length/nl_length.",
                        ""
                    )
                else:
                    # Re-raise other ValueErrors
                    raise

            # Extract outputs from TIPO
            # TIPO returns: (formatted_prompt_by_tipo, formatted_prompt_by_user,
            #                unformatted_prompt_by_tipo, unformatted_prompt_by_user)
            formatted_by_tipo = tipo_result[0]      # Full output with TIPO additions
            formatted_by_user = tipo_result[1]      # Original user input formatted
            unformatted_by_tipo = tipo_result[2]    # tags + addon_tags + addon_nl
            unformatted_by_user = tipo_result[3]    # Original user input unformatted

            original_output = formatted_by_tipo

            if show_filtering_log:
                print(f"\n[TIPO nobin custom] TIPO output analysis:")
                print(f"  Original user input: '{unformatted_by_user[:100]}...'")
                print(f"  TIPO full output: '{unformatted_by_tipo[:100]}...'")

            # Extract what TIPO added (works regardless of semantic filtering)
            if unformatted_by_user in unformatted_by_tipo:
                addon_part = unformatted_by_tipo.replace(unformatted_by_user, '', 1).strip()
                addon_part = addon_part.lstrip(',').lstrip('\n').strip()

                if show_filtering_log:
                    print(f"  TIPO additions: '{addon_part[:100]}...'")

                # Split addon into tags and NL
                if '\n' in addon_part:
                    addon_tags, addon_nl = addon_part.split('\n', 1)
                else:
                    addon_tags = addon_part
                    addon_nl = ""

                # STEP 1: Filter character tags (independent of semantic filtering)
                if filter_character_tags:
                    addon_tags, removed_char_tags = filter_character_tags_from_text(
                        addon_tags,
                        show_filtering_log
                    )
                    all_removed_character_tags.extend(removed_char_tags)

                # STEP 2: Apply semantic filtering if enabled
                if enable_semantic_filtering and model:
                    # Filter addon tags with regex
                    filtered_addon_tags, excluded_tags = filter_tags_regex(
                        addon_tags,
                        ban_tag_list,
                        show_filtering_log
                    )

                    # Filter addon NL with semantic similarity
                    filtered_addon_nl, excluded_nl = filter_natural_language(
                        addon_nl,
                        ban_tag_list,
                        model,
                        show_filtering_log
                    )

                    all_excluded.extend(excluded_nl)
                else:
                    # No semantic filtering - use addon as-is (but character tags already filtered)
                    filtered_addon_tags = addon_tags
                    filtered_addon_nl = addon_nl

                # Reconstruct: original (protected) + filtered addon
                result_parts = [unformatted_by_user]  # Always include original!

                if filtered_addon_tags:
                    result_parts.append(filtered_addon_tags)

                tags_part = ', '.join(result_parts)

                if filtered_addon_nl:
                    filtered_output = f"{tags_part}\n{filtered_addon_nl}"
                else:
                    filtered_output = tags_part

                # Quality check (if enabled)
                if enable_quality_check:
                    is_valid, reason = check_output_quality(filtered_output, tags, max_word_repetition)
                    if not is_valid:
                        if show_filtering_log:
                            print(f"[TIPO nobin custom] Quality check failed: {reason}")
                            print(f"[TIPO nobin custom] Regenerating with seed {current_seed + 1}...")
                        regeneration_count += 1
                        current_seed += 1
                        continue

                # Count keywords in ADDED content only (only if semantic filtering is on)
                if enable_semantic_filtering:
                    addon_keyword_count = count_keywords(filtered_addon_tags) + count_keywords(filtered_addon_nl)

                    if show_filtering_log:
                        print(f"[TIPO nobin custom] Attempt {attempt + 1}: {addon_keyword_count} new keywords after filtering")

                    if addon_keyword_count >= minimum_keyword_count:
                        break

                    # Regenerate with new seed
                    regeneration_count += 1
                    current_seed += 1

                    if show_filtering_log:
                        print(f"[TIPO nobin custom] Regenerating with seed {current_seed}...")
                else:
                    # No regeneration without semantic filtering
                    break
            else:
                # Can't find original in output - use full output (shouldn't happen)
                if show_filtering_log:
                    print(f"[TIPO nobin custom] Warning: Could not find original in output")
                filtered_output = formatted_by_tipo
                break

        # Format excluded words
        excluded_words_str = "\n".join([
            f"{word} (similar to '{tag}', score: {score:.3f})"
            for word, tag, score in all_excluded
        ])

        # Format removed character tags
        removed_character_tags_str = ", ".join(all_removed_character_tags)

        # Remove duplicate tags if enabled
        if remove_duplicate_tags:
            filtered_output = deduplicate_tags(filtered_output)
            if show_filtering_log:
                print(f"[TIPO nobin custom] Duplicate tags removed")

        if show_filtering_log:
            print(f"\n{'='*60}")
            print(f"[TIPO nobin custom] Generation complete")
            print(f"Regenerations: {regeneration_count}")
            print(f"Excluded words: {len(all_excluded)}")
            print(f"Removed character tags: {len(all_removed_character_tags)}")
            print(f"{'='*60}\n")

        return (
            filtered_output,
            original_output,
            regeneration_count,
            excluded_words_str,
            removed_character_tags_str
        )



NODE_CLASS_MAPPINGS = {
    "TIPONobinCustom": TIPONobinCustom,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TIPONobinCustom": "TIPO nobin custom",
}
