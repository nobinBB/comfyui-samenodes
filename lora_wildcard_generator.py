"""
LoRA Wildcard Generator Node for ComfyUI
Generates YAML wildcard files from Civitai JSON metadata
"""

import os
import json
import yaml
from pathlib import Path


class LoraWildcardGenerator:
    """
    A node that generates YAML wildcard files from Civitai JSON metadata.
    Extracts trainedWords from JSON files and creates LoRA syntax entries.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Folder containing JSON files
                "json_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                # Wildcard name (also used as YAML filename)
                "wildcard_name": ("STRING", {
                    "default": "lora_triggers",
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
    CATEGORY = "utils/lora"

    def parse_json_file(self, json_path):
        """
        Parse JSON file and extract civitai metadata

        Args:
            json_path: Path to JSON file

        Returns:
            Dictionary with filename and trainedWords, or None if parsing fails
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract civitai metadata
            civitai = data.get('civitai', {})
            trained_words = civitai.get('trainedWords', [])

            if not trained_words:
                return None

            # Get filename without extension for LoRA name
            lora_name = json_path.stem

            return {
                'lora_name': lora_name,
                'trained_words': trained_words
            }

        except Exception as e:
            print(f"Error parsing {json_path.name}: {e}")
            return None

    def generate_lora_entry(self, lora_name, trained_words):
        """
        Generate LoRA syntax entry

        Args:
            lora_name: Name of the LoRA model
            trained_words: List of trained words/triggers

        Returns:
            String with LoRA syntax
        """
        # Join trained words with comma and space
        words = ', '.join(trained_words)

        # Replace newlines with | to handle multi-line trigger words
        words = words.replace('\n', '|').replace('\r', '')

        # Clean up comma before pipe (e.g., ", |" or ",|" becomes "|")
        words = words.replace(', |', '|').replace(',|', '|')

        # Clean up space after pipe (e.g., "| " becomes "|")
        words = words.replace('| ', '|')

        # Normalize whitespace for each part separated by pipe
        # Split by pipe, trim and normalize each part, then rejoin
        parts = words.split('|')
        parts = [' '.join(part.strip().split()) for part in parts]
        words = '|'.join(parts)

        # Remove trailing commas, pipes, and spaces
        words = words.rstrip(',| ')

        # Wrap trigger words in braces and generate LoRA syntax
        # Format: <lora:name:{0.4|0.5|0.6|0.7|0.8}>{trigger words}
        lora_syntax = f"<lora:{lora_name}:{{0.4|0.5|0.6|0.7|0.8}}>{{{words}}}"

        return lora_syntax

    def create_yaml_content(self, entries):
        """
        Create YAML content from entries

        Args:
            entries: List of dictionaries with lora_name and trained_words

        Returns:
            YAML formatted string
        """
        # Create dictionary for YAML
        yaml_dict = {}

        for entry in entries:
            lora_name = entry['lora_name']
            trained_words = entry['trained_words']

            # Generate LoRA entry
            lora_entry = self.generate_lora_entry(lora_name, trained_words)

            # Add to dictionary
            # Format: filename: [<lora:...>triggers]
            yaml_dict[lora_name] = [lora_entry]

        # Convert to YAML
        # Use large width to prevent line wrapping
        yaml_content = yaml.dump(
            yaml_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=float('inf')  # Prevent automatic line wrapping
        )

        return yaml_content

    def generate_wildcard(self, json_folder, wildcard_name, output_folder):
        """
        Generate YAML wildcard file from JSON files

        Args:
            json_folder: Folder containing JSON files with Civitai metadata
            wildcard_name: Name for the wildcard (used as filename)
            output_folder: Folder to save the YAML file

        Returns:
            Tuple of (status_message, entry_count)
        """
        try:
            # Validate input folder
            folder = Path(json_folder)
            if not folder.exists():
                return (f"Error: Folder does not exist: {json_folder}", 0)

            if not folder.is_dir():
                return (f"Error: Path is not a directory: {json_folder}", 0)

            # Find all JSON files
            json_files = list(folder.glob('*.json'))

            if not json_files:
                return (f"No JSON files found in: {json_folder}", 0)

            print(f"\n{'='*60}")
            print(f"Processing JSON files for LoRA wildcards...")
            print(f"JSON folder: {json_folder}")
            print(f"Found {len(json_files)} JSON files")
            print(f"{'='*60}\n")

            # Parse all JSON files
            entries = []
            skipped = 0

            for json_file in json_files:
                print(f"Processing: {json_file.name}")
                entry = self.parse_json_file(json_file)

                if entry:
                    entries.append(entry)
                    print(f"  ✓ Extracted: {entry['lora_name']}")
                    print(f"    Triggers: {', '.join(entry['trained_words'])}")
                else:
                    skipped += 1
                    print(f"  ✗ Skipped (no trainedWords found)")

            if not entries:
                return ("No valid entries found in JSON files", 0)

            # Create YAML content
            print(f"\nGenerating YAML wildcard file...")
            yaml_content = self.create_yaml_content(entries)

            # Create output folder if it doesn't exist
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save YAML file
            # Filename and title are the same as wildcard_name
            yaml_filename = f"{wildcard_name}.yaml"
            yaml_filepath = output_path / yaml_filename

            with open(yaml_filepath, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            print(f"\n{'='*60}")
            print(f"✓ Wildcard file generated successfully!")
            print(f"Output: {yaml_filepath}")
            print(f"Entries: {len(entries)}")
            if skipped > 0:
                print(f"Skipped: {skipped} files")
            print(f"{'='*60}\n")

            # Preview first few entries
            if entries:
                print("Preview (first 3 entries):")
                for i, entry in enumerate(entries[:3], 1):
                    lora_entry = self.generate_lora_entry(
                        entry['lora_name'],
                        entry['trained_words']
                    )
                    print(f"  {i}. {entry['lora_name']}:")
                    print(f"     - {lora_entry}")
                print()

            status = f"Generated {len(entries)} entries in {yaml_filename}"
            if skipped > 0:
                status += f" ({skipped} skipped)"

            return (status, len(entries))

        except Exception as e:
            error_msg = f"Error generating wildcard: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return (error_msg, 0)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "LoraWildcardGenerator": LoraWildcardGenerator,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraWildcardGenerator": "LoRA Wildcard Generator",
}
