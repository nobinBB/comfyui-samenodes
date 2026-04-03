"""
Civitai LoRA Searcher Node for ComfyUI
Searches Civitai API by SHA256 hash to find LoRA model URLs.
Falls back to CivitAI Archive URL if not found on Civitai.
"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv


class CivitaiLoraSearcher:
    """
    A node that searches Civitai for LoRA models by SHA256 hash.
    Reads SHA256 from JSON metadata files in a folder.
    Falls back to CivitAI Archive URL if not found on Civitai.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("civitai_urls", "archive_urls", "info", "status")
    FUNCTION = "search_loras"
    CATEGORY = "utils/civitai"
    OUTPUT_NODE = True

    def __init__(self):
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path)
        self.api_key = os.getenv('CIVITAI_API_KEY', '')

    def search_by_hash(self, sha256):
        """
        Search Civitai API by SHA256 hash.

        Returns:
            dict with found status and URL/info if found
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
                return {
                    'found': True,
                    'civitai_url': civitai_url,
                    'model_id': model_id,
                    'version_id': version_id,
                    'name': data.get('model', {}).get('name', ''),
                    'version_name': data.get('name', ''),
                }
            else:
                return {'found': False}
        except Exception as e:
            print(f"  Error searching Civitai: {e}")
            return {'found': False}

    def search_loras(self, json_folder):
        """
        Search Civitai for all LoRAs found in the JSON metadata folder.

        Args:
            json_folder: Folder containing Civitai JSON metadata files

        Returns:
            Tuple of (civitai_urls, archive_urls, info, status)
        """
        try:
            folder = Path(json_folder)
            if not folder.exists():
                return ("", "", "", f"Error: Folder does not exist: {json_folder}")
            if not folder.is_dir():
                return ("", "", "", f"Error: Path is not a directory: {json_folder}")

            json_files = sorted(folder.glob('*.json'))
            if not json_files:
                return ("", "", "", f"No JSON files found in: {json_folder}")

            print(f"\n{'='*60}")
            print(f"Civitai LoRA Searcher")
            print(f"JSON folder: {json_folder}")
            print(f"Found {len(json_files)} JSON files")
            if self.api_key:
                print(f"API Key: configured")
            else:
                print(f"API Key: not configured (unauthenticated requests)")
            print(f"{'='*60}\n")

            civitai_urls = []
            archive_urls = []
            info_list = []
            status_lines = []

            found_count = 0
            archive_count = 0
            error_count = 0

            for i, json_file in enumerate(json_files, 1):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    lora_name = data.get('file_name', json_file.stem)
                    sha256 = data.get('sha256', '')

                    print(f"[{i}/{len(json_files)}] {lora_name}")

                    if not sha256:
                        status_lines.append(f"✗ {lora_name}: SHA256 not found in JSON")
                        print(f"  ✗ No SHA256 hash found")
                        error_count += 1
                        continue

                    result = self.search_by_hash(sha256)

                    if result['found']:
                        civitai_url = result['civitai_url']
                        civitai_urls.append(f"{lora_name}: {civitai_url}")
                        info_list.append({
                            'lora_name': lora_name,
                            'status': 'Found',
                            'source': 'civitai',
                            'civitai_url': civitai_url,
                            'model_id': result['model_id'],
                            'version_id': result['version_id'],
                            'name': result['name'],
                            'version_name': result['version_name'],
                            'sha256': sha256,
                        })
                        status_lines.append(f"✓ {lora_name}: Found  {civitai_url}")
                        print(f"  ✓ Found: {civitai_url}")
                        found_count += 1
                    else:
                        archive_url = f"https://civarchive.com/sha256/{sha256}"
                        archive_urls.append(f"{lora_name}: {archive_url}")
                        info_list.append({
                            'lora_name': lora_name,
                            'status': 'Archive Fallback',
                            'source': 'archive',
                            'archive_url': archive_url,
                            'sha256': sha256,
                        })
                        status_lines.append(f"△ {lora_name}: Archive Fallback  {archive_url}")
                        print(f"  △ Not found on Civitai → Archive: {archive_url}")
                        archive_count += 1

                    # Avoid rate limiting
                    time.sleep(0.3)

                except Exception as e:
                    status_lines.append(f"✗ {json_file.name}: Error - {e}")
                    print(f"  ✗ Error: {e}")
                    error_count += 1

            print(f"\n{'='*60}")
            print(f"Search Complete!")
            print(f"Found on Civitai: {found_count}")
            print(f"Archive Fallback: {archive_count}")
            if error_count > 0:
                print(f"Errors: {error_count}")
            print(f"{'='*60}\n")

            civitai_output = '\n'.join(civitai_urls)
            archive_output = '\n'.join(archive_urls)
            info_output = json.dumps(info_list, ensure_ascii=False, indent=2)
            status_output = (
                f"Found: {found_count} / Archive: {archive_count} / Errors: {error_count}\n"
                + '\n'.join(status_lines)
            )

            return (civitai_output, archive_output, info_output, status_output)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return ("", "", "", error_msg)


NODE_CLASS_MAPPINGS = {
    "CivitaiLoraSearcher": CivitaiLoraSearcher,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitaiLoraSearcher": "Civitai LoRA Searcher",
}
