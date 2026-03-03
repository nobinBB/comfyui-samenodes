"""
Embedding Wildcard Generator Node for ComfyUI
Generates YAML wildcard files from embedding files
"""

import os
import yaml
from pathlib import Path


class FoldedString(str):
    """Custom string class for YAML folded scalar output (>-)"""
    pass


def folded_string_representer(dumper, data):
    """Representer for folded scalar style in YAML"""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='>')


# Register custom representer
yaml.add_representer(FoldedString, folded_string_representer)


class EmbeddingWildcardGenerator:
    """
    A node that generates YAML wildcard files from embedding files.
    Scans a folder for embedding files and creates embedding: syntax entries.
    """

    # Supported embedding file extensions
    EMBEDDING_EXTENSIONS = {'.pt', '.safetensors', '.bin', '.ckpt', '.pth'}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Folder containing embedding files
                "embedding_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                # Wildcard name (also used as YAML filename)
                "wildcard_name": ("STRING", {
                    "default": "embedding_triggers",
                    "multiline": False
                }),
                # Output folder for YAML file
                "output_folder": ("STRING", {
                    "default": "wildcards",
                    "multiline": False
                }),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("status", "entry_count")
    FUNCTION = "generate_wildcard"
    CATEGORY = "utils/embedding"
    OUTPUT_NODE = True

    def scan_embedding_files(self, folder_path):
        """
        Scan folder for embedding files

        Args:
            folder_path: Path object to the embedding folder

        Returns:
            List of embedding filenames (without extension)
        """
        embeddings = []

        try:
            # Scan all files in the folder
            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    # Check if file has a supported embedding extension
                    if file_path.suffix.lower() in self.EMBEDDING_EXTENSIONS:
                        # Get filename without extension
                        embedding_name = file_path.stem
                        embeddings.append(embedding_name)
                        print(f"  Found: {embedding_name}{file_path.suffix}")

        except Exception as e:
            print(f"Error scanning folder: {e}")

        return embeddings

    def generate_embedding_entry(self, embedding_name):
        """
        Generate embedding syntax entry

        Args:
            embedding_name: Name of the embedding

        Returns:
            String with embedding syntax
        """
        return f"embedding:{embedding_name}"

    def create_yaml_content(self, embeddings, wildcard_name):
        """
        Create YAML content from embedding names

        Args:
            embeddings: List of embedding names
            wildcard_name: Name for the wildcard (used as top-level key)

        Returns:
            YAML formatted string
        """
        # Create nested dictionary for YAML
        nested_dict = {}

        # Collect all embedding references for the 'all' entry
        all_embedding_refs = []

        for embedding_name in embeddings:
            # Generate embedding entry
            embedding_entry = self.generate_embedding_entry(embedding_name)

            # Wrap in FoldedString for >- YAML format
            embedding_entry_folded = FoldedString(embedding_entry)

            # Add to nested dictionary
            # Format: embedding_name: >-\n  embedding:name
            nested_dict[embedding_name] = [embedding_entry_folded]

            # Add reference for 'all' entry
            all_embedding_refs.append(f"__{embedding_name}__")

        # Create 'all' entry that randomly selects one embedding
        all_key = f"all-{wildcard_name}"
        all_entry = "{" + "|".join(all_embedding_refs) + "}"

        # Wrap in FoldedString for >- YAML format
        all_entry_folded = FoldedString(all_entry)

        # Create final dictionary with wildcard_name as top-level key
        # Order: wildcard_name -> all-<wildcard_name> first, then individual entries
        final_dict = {
            wildcard_name: {
                all_key: [all_entry_folded],
                **nested_dict
            }
        }

        # Convert to YAML
        yaml_content = yaml.dump(
            final_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=float('inf')  # Prevent automatic line wrapping
        )

        return yaml_content

    def generate_wildcard(self, embedding_folder, wildcard_name, output_folder):
        """
        Generate YAML wildcard file from embedding files

        Args:
            embedding_folder: Folder containing embedding files
            wildcard_name: Name for the wildcard (used as filename)
            output_folder: Folder to save the YAML file

        Returns:
            Tuple of (status_message, entry_count)
        """
        try:
            # Validate input folder
            folder = Path(embedding_folder)
            if not folder.exists():
                return (f"Error: Folder does not exist: {embedding_folder}", 0)

            if not folder.is_dir():
                return (f"Error: Path is not a directory: {embedding_folder}", 0)

            print(f"\n{'='*60}")
            print(f"Scanning embedding folder for wildcard generation...")
            print(f"Embedding folder: {embedding_folder}")
            print(f"Supported extensions: {', '.join(self.EMBEDDING_EXTENSIONS)}")
            print(f"{'='*60}\n")

            # Scan for embedding files
            embeddings = self.scan_embedding_files(folder)

            if not embeddings:
                return (f"No embedding files found in: {embedding_folder}", 0)

            print(f"\nFound {len(embeddings)} embedding files")

            # Sort embeddings alphabetically
            embeddings.sort()

            # Create YAML content
            print(f"\nGenerating YAML wildcard file...")
            yaml_content = self.create_yaml_content(embeddings, wildcard_name)

            # Create output folder if it doesn't exist
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save YAML file
            yaml_filename = f"{wildcard_name}.yaml"
            yaml_filepath = output_path / yaml_filename

            with open(yaml_filepath, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            print(f"\n{'='*60}")
            print(f"✓ Wildcard file generated successfully!")
            print(f"Output: {yaml_filepath}")
            print(f"Entries: {len(embeddings)}")
            print(f"{'='*60}\n")

            # Preview first few entries
            if embeddings:
                print("Preview (first 5 entries):")
                for i, embedding_name in enumerate(embeddings[:5], 1):
                    embedding_entry = self.generate_embedding_entry(embedding_name)
                    print(f"  {i}. {embedding_name}:")
                    print(f"     - {embedding_entry}")
                print()

            status = f"Generated {len(embeddings)} entries in {yaml_filename}"
            return (status, len(embeddings))

        except Exception as e:
            error_msg = f"Error generating wildcard: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return (error_msg, 0)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "EmbeddingWildcardGenerator": EmbeddingWildcardGenerator,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "EmbeddingWildcardGenerator": "Embedding Wildcard Generator",
}
