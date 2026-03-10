"""
Embedding Path Resolver Node for ComfyUI
Resolves embedding:name to embedding:subpath/filename.ext by searching models/embeddings recursively
"""

import os
import re
from pathlib import Path

try:
    import folder_paths
    HAS_FOLDER_PATHS = True
except ImportError:
    HAS_FOLDER_PATHS = False


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
        Uses ComfyUI's folder_paths module if available.
        """
        # Try using ComfyUI's folder_paths module first
        if HAS_FOLDER_PATHS:
            try:
                embeddings_dir = folder_paths.get_folder_paths("embeddings")
                if embeddings_dir and len(embeddings_dir) > 0:
                    # Use first embeddings folder
                    embeddings_path = Path(embeddings_dir[0])
                    if embeddings_path.exists():
                        return embeddings_path
            except Exception as e:
                print(f"[EmbeddingPathResolver] Error using folder_paths: {e}")

        # Fallback: Try to find ComfyUI root directory manually
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
        Scan all embeddings folders recursively and build a mapping
        from basename (without extension) to relative path.

        Returns:
            dict: {basename: relative_path_with_extension}
        """
        embedding_map = {}
        folders_to_scan = []

        # Get all embeddings folders from folder_paths
        if HAS_FOLDER_PATHS:
            try:
                embeddings_dirs = folder_paths.get_folder_paths("embeddings")
                if embeddings_dirs:
                    folders_to_scan = [Path(d) for d in embeddings_dirs if Path(d).exists()]
                    print(f"[EmbeddingPathResolver] Found {len(folders_to_scan)} embeddings folder(s) from folder_paths")
            except Exception as e:
                print(f"[EmbeddingPathResolver] Error using folder_paths: {e}")

        # Fallback: Try to find embeddings folder manually
        if not folders_to_scan:
            embeddings_folder = self._get_embeddings_folder()
            if embeddings_folder and embeddings_folder.exists():
                folders_to_scan = [embeddings_folder]

        if not folders_to_scan:
            print(f"[EmbeddingPathResolver] Warning: No embeddings folders found")
            return {}

        # Scan all folders
        for embeddings_folder in folders_to_scan:
            print(f"[EmbeddingPathResolver] Scanning: {embeddings_folder}")

            # Recursively scan for embedding files
            for file_path in embeddings_folder.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.EMBEDDING_EXTENSIONS:
                    # Get basename without extension
                    basename = file_path.stem

                    # Get relative path from embeddings folder
                    relative_path = file_path.relative_to(embeddings_folder)

                    # Remove extension from the relative path
                    # Keep directory structure but remove extension from filename
                    relative_path_without_ext = relative_path.parent / file_path.stem

                    # Convert to string with forward slashes (cross-platform)
                    relative_path_str = str(relative_path_without_ext).replace('\\', '/')

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
                print(f"[EmbeddingPathResolver] Resolved: {embedding_name} -> {resolved_path}")
                return f"embedding:{resolved_path}"
            else:
                # Not found, keep original
                print(f"[EmbeddingPathResolver] Not found: {embedding_name}")
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
