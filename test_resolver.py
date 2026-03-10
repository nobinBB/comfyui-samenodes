#!/usr/bin/env python3
"""
Debug script for Embedding Path Resolver
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from embedding_path_resolver import EmbeddingPathResolver

def test_resolver():
    print("=== Embedding Path Resolver Debug ===\n")

    # Create instance
    resolver = EmbeddingPathResolver()

    # Test folder detection
    print("1. Testing folder detection...")
    embeddings_folder = resolver._get_embeddings_folder()
    if embeddings_folder:
        print(f"   ✓ Found: {embeddings_folder}")
        print(f"   Exists: {embeddings_folder.exists()}")
    else:
        print("   ✗ Embeddings folder not found!")
        return

    # Test scanning
    print("\n2. Testing embedding scan...")
    embedding_map = resolver._get_embedding_map()
    print(f"   Found {len(embedding_map)} embeddings:")

    # Show first 10 embeddings
    for i, (name, path) in enumerate(list(embedding_map.items())[:10]):
        print(f"   - {name} -> {path}")

    if len(embedding_map) > 10:
        print(f"   ... and {len(embedding_map) - 10} more")

    # Test specific embedding
    print("\n3. Testing FFF_standing_split...")
    if "FFF_standing_split" in embedding_map:
        print(f"   ✓ Found: {embedding_map['FFF_standing_split']}")
    else:
        print("   ✗ Not found in map")
        print(f"   Available embeddings with 'FFF': {[k for k in embedding_map.keys() if 'FFF' in k]}")

    # Test resolution
    print("\n4. Testing text resolution...")
    test_input = "embedding:FFF_standing_split,"
    result = resolver.resolve_paths(test_input)
    print(f"   Input:  '{test_input}'")
    print(f"   Output: '{result[0]}'")

    if result[0] != test_input:
        print("   ✓ Resolution working!")
    else:
        print("   ✗ No change - resolution not working")

        # Test regex pattern
        import re
        pattern = r'embedding:([a-zA-Z0-9_\-]+)(?![a-zA-Z0-9_\-/\\.])'
        match = re.search(pattern, test_input)
        if match:
            print(f"   Pattern matched: '{match.group(0)}' (captured: '{match.group(1)}')")
        else:
            print("   Pattern did not match!")

if __name__ == "__main__":
    test_resolver()
