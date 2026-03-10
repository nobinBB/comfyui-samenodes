"""
Embedding Path Resolver Node for ComfyUI
Resolves embedding:name to embedding:subpath/filename.ext by searching models/embeddings recursively
"""

import os
import re
from pathlib import Path


class EmbeddingPathResolver:
    """
    Resolves embedding paths from short names to full relative paths.

    Searches models/embeddings recursively for matching embedding files
    and replaces embedding:name with embedding:subpath/filename.ext

    Example:
    Input: "1girl, embedding:sit_front, masterpiece"
    Output: "1girl, embedding:pose/sit_front.pt, masterpiece"
    """

    # Supported embedding file extensions
    EMBEDDING_EXTENSIONS = {'.pt', '.safetensors', '.bin', '.ckpt', '.pth'}

    def __init__(self):
        self._embedding_cache = None
        self._cache_timestamp = 0

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "resolve_paths"
    CATEGORY = "utils/text"

    def _get_embeddings_folder(self):
        """
        Get the embeddings folder path.
        Tries to find ComfyUI's models/embeddings folder.
        """
        # Try to find ComfyUI root directory
        current_dir = Path(__file__).resolve().parent

        # Search upward for models/embeddings folder
        for parent in [current_dir] + list(current_dir.parents):
            embeddings_path = parent / "models" / "embeddings"
            if embeddings_path.exists() and embeddings_path.is_dir():
                return embeddings_path

        # Fallback: assume models/embeddings relative to current working directory
        fallback_path = Path.cwd() / "models" / "embeddings"
        if fallback_path.exists():
            return fallback_path

        return None

    def _scan_embeddings(self):
        """
        Scan the embeddings folder recursively and build a mapping
        from basename (without extension) to relative path.

        Returns:
            dict: {basename: relative_path_with_extension}
        """
        embeddings_folder = self._get_embeddings_folder()

        if not embeddings_folder or not embeddings_folder.exists():
            print(f"[EmbeddingPathResolver] Warning: embeddings folder not found")
            return {}

        embedding_map = {}

        # Recursively scan for embedding files
        for file_path in embeddings_folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.EMBEDDING_EXTENSIONS:
                # Get basename without extension
                basename = file_path.stem

                # Get relative path from embeddings folder
                relative_path = file_path.relative_to(embeddings_folder)

                # Convert to string with forward slashes (cross-platform)
                relative_path_str = str(relative_path).replace('\\', '/')

                # Store first occurrence only (in case of duplicates)
                if basename not in embedding_map:
                    embedding_map[basename] = relative_path_str

        return embedding_map

    def _get_embedding_map(self):
        """
        Get embedding map with caching.
        Cache is refreshed if folder modification time changes.
        """
        embeddings_folder = self._get_embeddings_folder()

        if not embeddings_folder or not embeddings_folder.exists():
            return {}

        # Check if cache needs refresh
        try:
            current_mtime = embeddings_folder.stat().st_mtime
        except:
            current_mtime = 0

        # Refresh cache if needed
        if self._embedding_cache is None or current_mtime > self._cache_timestamp:
            self._embedding_cache = self._scan_embeddings()
            self._cache_timestamp = current_mtime
            print(f"[EmbeddingPathResolver] Scanned {len(self._embedding_cache)} embeddings")

        return self._embedding_cache

    def resolve_paths(self, text):
        """
        Resolve embedding:name patterns to embedding:subpath/filename.ext

        Args:
            text: Input text with embedding:name patterns

        Returns:
            Tuple containing the resolved text
        """
        if not text:
            return (text,)

        # Get embedding mapping
        embedding_map = self._get_embedding_map()

        if not embedding_map:
            # No embeddings found, return original text
            return (text,)

        # Pattern to match embedding:name (but not embedding:path/name)
        # This matches "embedding:" followed by a name without path separators
        pattern = r'embedding:([a-zA-Z0-9_\-]+)(?![a-zA-Z0-9_\-/\\.])'

        def replace_embedding(match):
            """Replace callback for regex substitution"""
            embedding_name = match.group(1)

            # Look up the embedding in our map
            if embedding_name in embedding_map:
                resolved_path = embedding_map[embedding_name]
                return f"embedding:{resolved_path}"
            else:
                # Not found, keep original
                return match.group(0)

        # Perform replacement
        resolved_text = re.sub(pattern, replace_embedding, text)

        return (resolved_text,)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "EmbeddingPathResolver": EmbeddingPathResolver,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "EmbeddingPathResolver": "Embedding Path Resolver",
}
