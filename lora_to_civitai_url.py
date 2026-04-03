"""
LoRA to Civitai URL Node for ComfyUI
Parses LoRA syntax and returns Civitai URL
"""

import os
import re
import json
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv


class LoraToCivitaiUrl:
    """
    A node that parses LoRA syntax (<lora:name:weight>) and returns the Civitai URL.
    Searches by SHA256 hash from JSON metadata or calculates from file.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "lora_syntax": ("STRING", {
                    "default": "<lora:filename:0.8>",
                    "multiline": True
                }),
                "json_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
            "optional": {
                "lora_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("civitai_url", "archive_url")
    FUNCTION = "get_civitai_url"
    CATEGORY = "utils/civitai"
    OUTPUT_NODE = True

    def __init__(self):
        # Load API key from .env file
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path)
        self.api_key = os.getenv('CIVITAI_API_KEY', '')

    def parse_lora_syntax(self, lora_syntax):
        """
        Parse LoRA syntax to extract LoRA names.
        Format: <lora:name:weight> or <lora:name:weight:another_param>

        Returns:
            List of LoRA names
        """
        pattern = r'<lora:([^:>]+):[^>]*>'
        matches = re.findall(pattern, lora_syntax)
        return matches

    def get_sha256_from_json(self, lora_name, json_folder):
        """
        Get SHA256 from JSON metadata file.
        Searches recursively in subfolders.

        Args:
            lora_name: Name of the LoRA
            json_folder: Folder containing JSON files

        Returns:
            SHA256 hash string or None
        """
        folder = Path(json_folder)
        if not folder.exists() or not folder.is_dir():
            print(f"  ✗ JSON folder not found: {json_folder}")
            return None

        # Search all JSON files recursively for matching file_name
        print(f"  Searching JSON files in: {json_folder}")
        for json_file in folder.rglob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                file_name = data.get('file_name', '')

                # Match by file_name
                if file_name == lora_name:
                    sha256 = data.get('sha256', '')
                    if sha256:
                        print(f"  ✓ Matched: {json_file.name} → SHA256: {sha256[:16]}...")
                        return sha256
            except Exception as e:
                continue

        print(f"  ✗ No matching JSON found for: {lora_name}")
        return None

    def calculate_sha256_from_file(self, lora_name, lora_folder):
        """
        Calculate SHA256 hash directly from LoRA file.
        Searches recursively in subfolders.

        Args:
            lora_name: Name of the LoRA
            lora_folder: Folder containing LoRA files

        Returns:
            SHA256 hash string or None
        """
        folder = Path(lora_folder)
        if not folder.exists() or not folder.is_dir():
            print(f"  ✗ LoRA folder not found: {lora_folder}")
            return None

        # Search recursively for LoRA file
        print(f"  Searching LoRA files in: {lora_folder}")
        extensions = ['*.safetensors', '*.pt', '*.ckpt']

        for ext in extensions:
            for lora_file in folder.rglob(ext):
                # Match by filename (without extension)
                if lora_file.stem == lora_name:
                    try:
                        print(f"  Calculating SHA256 for {lora_file.name}...")
                        sha256_hash = hashlib.sha256()
                        with open(lora_file, 'rb') as f:
                            for chunk in iter(lambda: f.read(8192), b''):
                                sha256_hash.update(chunk)
                        sha256 = sha256_hash.hexdigest()
                        print(f"  ✓ Calculated SHA256: {sha256[:16]}...")
                        return sha256
                    except Exception as e:
                        print(f"  ✗ Error calculating SHA256: {e}")

        print(f"  ✗ No LoRA file found for: {lora_name}")
        return None

    def search_civitai_by_hash(self, sha256):
        """
        Search Civitai API by SHA256 hash.

        Args:
            sha256: SHA256 hash of the LoRA file

        Returns:
            Civitai URL string or None
        """
        url = f"https://civitai.com/api/v1/model-versions/by-hash/{sha256}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                model_id = data.get('modelId')
                version_id = data.get('id')
                civitai_url = f"https://civitai.com/models/{model_id}?modelVersionId={version_id}"
                return civitai_url
            else:
                return None
        except Exception as e:
            print(f"  Error searching Civitai: {e}")
            return None

    def get_civitai_url(self, lora_syntax, json_folder, lora_folder=""):
        """
        Parse LoRA syntax and return Civitai URLs.

        Args:
            lora_syntax: LoRA syntax string (e.g., "<lora:name:0.8>")
            json_folder: Folder containing JSON metadata
            lora_folder: (Optional) Folder containing LoRA files for SHA256 calculation

        Returns:
            Tuple of (civitai_url, archive_url)
        """
        try:
            print(f"\n{'='*60}")
            print(f"LoRA to Civitai URL")
            print(f"{'='*60}")
            if self.api_key:
                print(f"API Key: configured (.env)")
            else:
                print(f"API Key: not configured (rate limited)")
            print()

            # Parse LoRA syntax
            lora_names = self.parse_lora_syntax(lora_syntax)

            if not lora_names:
                return ("", "No LoRA syntax found in input")

            print(f"Found {len(lora_names)} LoRA(s): {', '.join(lora_names)}\n")

            civitai_urls = []
            archive_urls = []

            for lora_name in lora_names:
                print(f"Processing: {lora_name}")

                # Try to get SHA256 from JSON
                sha256 = None
                if json_folder:
                    sha256 = self.get_sha256_from_json(lora_name, json_folder)
                    if sha256:
                        print(f"  SHA256 from JSON: {sha256[:16]}...")

                # If not found and lora_folder provided, calculate from file
                if not sha256 and lora_folder:
                    sha256 = self.calculate_sha256_from_file(lora_name, lora_folder)
                    if sha256:
                        print(f"  SHA256 calculated: {sha256[:16]}...")

                if not sha256:
                    print(f"  ✗ SHA256 not found")
                    archive_urls.append(f"{lora_name}: SHA256 not found")
                    continue

                # Search Civitai
                civitai_url = self.search_civitai_by_hash(sha256)

                if civitai_url:
                    print(f"  ✓ Found: {civitai_url}")
                    civitai_urls.append(civitai_url)
                else:
                    archive_url = f"https://civarchive.com/sha256/{sha256}"
                    print(f"  △ Archive Fallback: {archive_url}")
                    archive_urls.append(archive_url)

                print()

            print(f"{'='*60}")
            print(f"Complete!")
            print(f"Found on Civitai: {len(civitai_urls)}")
            print(f"Archive/Not Found: {len(archive_urls)}")
            print(f"{'='*60}\n")

            civitai_output = '\n'.join(civitai_urls) if civitai_urls else ""
            archive_output = '\n'.join(archive_urls) if archive_urls else ""

            return (civitai_output, archive_output)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return ("", error_msg)


NODE_CLASS_MAPPINGS = {
    "LoraToCivitaiUrl": LoraToCivitaiUrl,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraToCivitaiUrl": "LoRA to Civitai URL",
}
