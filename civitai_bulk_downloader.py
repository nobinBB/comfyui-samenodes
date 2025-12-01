"""
Civitai Bulk Downloader Node for ComfyUI
Downloads LoRA models from Civitai URLs listed in a text file
"""

import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv


class CivitaiBulkDownloader:
    """
    A node that downloads LoRA models from Civitai URLs in bulk.
    Reads URLs from a text file and downloads them with retry logic.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Text file containing URLs
                "txt_file_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                # Output folder for downloaded files
                "output_file_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                # Maximum retry attempts
                "max_retries": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 10,
                    "step": 1
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "summary")
    FUNCTION = "download_bulk"
    CATEGORY = "utils/download"
    OUTPUT_NODE = True

    def __init__(self):
        # Load environment variables from .env file
        env_path = Path(__file__).parent / ".env"
        load_dotenv(dotenv_path=env_path)
        self.api_key = os.getenv("CIVITAI_API_KEY")

    def read_urls_from_file(self, file_path):
        """
        Read URLs from text file.

        Args:
            file_path: Path to text file containing URLs

        Returns:
            List of URLs
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            return urls
        except Exception as e:
            raise Exception(f"Failed to read URLs from file: {str(e)}")

    def download_file(self, url, output_path, max_retries):
        """
        Download a single file from URL with retry logic.

        Args:
            url: Download URL
            output_path: Directory to save the file
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (success: bool, filename: str, message: str)
        """
        headers = {}
        if self.api_key and self.api_key != "your_api_key_here":
            headers["Authorization"] = f"Bearer {self.api_key}"

        for attempt in range(1, max_retries + 1):
            try:
                print(f"  Attempt {attempt}/{max_retries}...")

                # Send GET request
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                # Get filename from Content-Disposition header
                filename = None
                if 'Content-Disposition' in response.headers:
                    content_disposition = response.headers['Content-Disposition']
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[1].strip('"')

                # Fallback: extract from URL or use generic name
                if not filename:
                    model_id = url.split('/')[-1]
                    filename = f"model_{model_id}.safetensors"

                # Full file path
                file_path = Path(output_path) / filename

                # Download file
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Progress indicator (every 10MB)
                            if downloaded_size % (10 * 1024 * 1024) < 8192:
                                if total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    print(f"    Progress: {progress:.1f}% ({downloaded_size // (1024*1024)}MB / {total_size // (1024*1024)}MB)")

                print(f"  ✓ Downloaded: {filename} ({downloaded_size // (1024*1024)}MB)")
                return (True, filename, "Success")

            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                print(f"  ✗ Attempt {attempt} failed: {error_msg}")

                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"    Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    return (False, None, f"Failed after {max_retries} attempts: {error_msg}")

            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ Unexpected error: {error_msg}")
                return (False, None, f"Unexpected error: {error_msg}")

        return (False, None, f"Failed after {max_retries} attempts")

    def download_bulk(self, txt_file_path, output_file_path, max_retries):
        """
        Download multiple files from URLs listed in text file.

        Args:
            txt_file_path: Path to text file containing URLs
            output_file_path: Directory to save downloaded files
            max_retries: Maximum retry attempts per file

        Returns:
            Tuple of (status_message, summary)
        """
        try:
            print(f"\n{'='*60}")
            print(f"Civitai Bulk Downloader")
            print(f"{'='*60}\n")

            # Check API key
            if not self.api_key or self.api_key == "your_api_key_here":
                error_msg = (
                    "ERROR: Civitai API key not configured!\n\n"
                    "Please follow these steps:\n"
                    "1. Rename '.env.example' to '.env' in the node folder\n"
                    "2. Get your API key from: https://civitai.com/user/account\n"
                    "3. Add your API key to the .env file\n"
                    "4. Restart ComfyUI"
                )
                print(error_msg)
                return (error_msg, "Configuration Error: No API key")

            # Validate txt file path
            txt_path = Path(txt_file_path)
            if not txt_path.exists():
                return (f"Error: Text file not found: {txt_file_path}", "File Not Found")

            if not txt_path.is_file():
                return (f"Error: Path is not a file: {txt_file_path}", "Invalid Path")

            # Read URLs
            print(f"Reading URLs from: {txt_file_path}")
            urls = self.read_urls_from_file(txt_file_path)

            if not urls:
                return ("No URLs found in text file", "No URLs")

            print(f"Found {len(urls)} URLs to download\n")

            # Create output directory
            output_path = Path(output_file_path)
            output_path.mkdir(parents=True, exist_ok=True)
            print(f"Output directory: {output_file_path}\n")

            # Download each file
            results = []
            success_count = 0
            fail_count = 0

            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] Processing: {url}")

                success, filename, message = self.download_file(url, output_path, max_retries)

                results.append({
                    'url': url,
                    'success': success,
                    'filename': filename,
                    'message': message
                })

                if success:
                    success_count += 1
                else:
                    fail_count += 1

                print()  # Blank line between downloads

            # Generate summary
            print(f"{'='*60}")
            print(f"Download Complete!")
            print(f"{'='*60}")
            print(f"Total: {len(urls)} files")
            print(f"Success: {success_count}")
            print(f"Failed: {fail_count}")
            print(f"{'='*60}\n")

            # Generate detailed status message
            status_lines = [
                f"Downloaded {success_count}/{len(urls)} files successfully",
                f"\nSuccessful downloads:"
            ]

            for result in results:
                if result['success']:
                    status_lines.append(f"  ✓ {result['filename']}")

            if fail_count > 0:
                status_lines.append(f"\nFailed downloads:")
                for result in results:
                    if not result['success']:
                        status_lines.append(f"  ✗ {result['url']}")
                        status_lines.append(f"    Reason: {result['message']}")

            status_message = "\n".join(status_lines)

            # Generate summary
            summary = f"Success: {success_count}/{len(urls)}, Failed: {fail_count}/{len(urls)}"

            return (status_message, summary)

        except Exception as e:
            error_msg = f"Error during bulk download: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return (error_msg, "Error")


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "CivitaiBulkDownloader": CivitaiBulkDownloader,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitaiBulkDownloader": "Civitai Bulk Downloader",
}
