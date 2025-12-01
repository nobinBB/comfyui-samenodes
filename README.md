# ComfyUI Same Nodes

A collection of custom nodes for ComfyUI that enhance workflow capabilities with utilities for string conversion, batch processing, LoRA management, and automated downloads.

## Overview

This custom node pack provides essential tools for ComfyUI users:

- **Float to String**: Precise float-to-string conversion with decimal control
- **Batch Image Processor**: Efficient batch image operations
- **LoRA Wildcard Generator**: Automated YAML wildcard generation from Civitai metadata
- **Civitai Bulk Downloader**: Batch download LoRA models from Civitai with API authentication

These nodes are designed to streamline your ComfyUI workflow, especially when working with LoRA models, wildcards, and bulk operations.

---

## Installation

### Step 1: Clone the Repository

Navigate to your ComfyUI's `custom_nodes` folder and clone this repository:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/nobinBB/comfyui-samenodes.git
```

### Step 2: Install Dependencies

Install the required Python packages:

```bash
cd comfyui-samenodes
pip install -r requirements.txt
```

### Step 3: Configure Environment (For Civitai Bulk Downloader)

If you plan to use the Civitai Bulk Downloader node:

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Civitai API key (see [Civitai Bulk Downloader Setup](#civitai-bulk-downloader-setup) below)

### Step 4: Restart ComfyUI

Restart ComfyUI to load the new nodes.

---

## Nodes Documentation

### 1. Float to String

Converts float values to string format with configurable decimal places.

#### Inputs

- **value** (FLOAT): The float value to convert
- **decimal_places** (INT): Number of decimal places to display (0-10)
- **use_decimal_places** (BOOLEAN): Whether to apply decimal place formatting

#### Outputs

- **string** (STRING): The converted string value

#### Usage Examples

| Input Value | Decimal Places | Use Decimal Places | Output |
|-------------|----------------|-------------------|---------|
| 3.14159 | 2 | True | "3.14" |
| 3.14159 | 4 | True | "3.1416" |
| 3.14159 | - | False | "3.14159" |
| 42.0 | 0 | True | "42" |

#### Use Cases

- Converting KSampler cfg values to strings for file naming
- Formatting denoise values for display
- Creating readable parameter labels in workflows

---

### 2. Batch Image Processor

Process multiple images with various batch operations.

#### Description

Handles batch image processing tasks efficiently within ComfyUI workflows.

---

### 3. LoRA Wildcard Generator

Automatically generates YAML wildcard files from Civitai JSON metadata files, creating organized LoRA prompt templates.

#### Inputs

- **json_folder** (STRING): Path to folder containing Civitai `.json` metadata files
- **wildcard_name** (STRING): Name for the wildcard (used as filename and top-level YAML key)
- **output_folder** (STRING): Path to output folder for generated YAML file

#### Outputs

- **status** (STRING): Status message with generation details
- **entry_count** (INT): Number of LoRA entries generated

#### Features

- ✅ Extracts `trainedWords` from Civitai JSON metadata
- ✅ Generates LoRA syntax with weight variations: `{0.4|0.5|0.6|0.7|0.8}`
- ✅ Creates `all-<wildcard_name>` entry for random LoRA selection
- ✅ Automatically removes `.metadata` suffix from filenames
- ✅ Outputs unquoted YAML for proper wildcard expansion
- ✅ Compatible with Impact Wildcards and similar extensions

#### Generated YAML Format

```yaml
koma:
  all-koma:
  - >-
    {__2koma_V3__|__3angles_fingering__|__comic_style_cumshot__}
  2koma_V3:
  - <lora:2koma_V3:{0.4|0.5|0.6|0.7|0.8}>{2koma, two views}
  3angles_fingering:
  - <lora:3angles_fingering:{0.4|0.5|0.6|0.7|0.8}>{3angles_fingering, 1girl, lying, cross-section, fingering}
  comic_style_cumshot:
  - <lora:comic_style_cumshot:{0.4|0.5|0.6|0.7|0.8}>{comic, cumshot, cum}
```

#### Usage Example

1. Download LoRA models from Civitai (they come with `.json` metadata files)
2. Place all `.json` files in a folder (e.g., `/models/lora/metadata/`)
3. In ComfyUI, add the LoRA Wildcard Generator node
4. Set parameters:
   - `json_folder`: `/models/lora/metadata/`
   - `wildcard_name`: `my_loras`
   - `output_folder`: `/wildcards/`
5. Execute the workflow
6. Generated file: `/wildcards/my_loras.yaml`

#### Wildcard Usage in Prompts

After generation, use in your prompts:

- Random LoRA: `__my_loras/all-my_loras__`
- Specific LoRA: `__my_loras/2koma_V3__`

---

### 4. Civitai Bulk Downloader

Batch download LoRA models from Civitai using URLs listed in a text file, with API authentication and automatic retry.

#### Inputs

- **txt_file_path** (STRING): Path to text file containing Civitai download URLs (one per line)
- **output_file_path** (STRING): Output directory for downloaded LoRA files
- **max_retries** (INT): Maximum retry attempts per file (default: 3, range: 1-10)

#### Outputs

- **status** (STRING): Detailed status with success/failure logs for each file
- **summary** (STRING): Summary of download results (e.g., "Success: 15/20, Failed: 5/20")

#### Features

- ✅ Reads URLs from text file (one URL per line)
- ✅ Civitai API authentication via `.env` configuration
- ✅ Automatic retry with exponential backoff (2s, 4s, 8s, 16s...)
- ✅ Progress tracking for large files (updates every 10MB)
- ✅ Detailed logging of successes and failures
- ✅ Extracts proper filenames from Content-Disposition headers
- ✅ Standalone execution (OUTPUT_NODE enabled)

---

#### Civitai Bulk Downloader Setup

**Step 1: Get Your Civitai API Key**

1. Go to [Civitai](https://civitai.com/) and log in
2. Navigate to your account settings:
   - Click your profile icon → **Account Settings**
   - Or go directly to: https://civitai.com/user/account
3. Scroll to **API Keys** section
4. Click **Add API Key** (or copy existing key)
5. Copy the generated API key (it looks like: `a1b2c3d4e5f6g7h8i9j0...`)

**Step 2: Configure the .env File**

1. In the `comfyui-samenodes` folder, locate `.env.example`

2. Copy it to create `.env`:
   ```bash
   cp .env.example .env
   ```

3. Open `.env` in a text editor:
   ```bash
   # On Windows
   notepad .env

   # On macOS
   open -e .env

   # On Linux
   nano .env
   ```

4. Replace `your_api_key_here` with your actual API key:
   ```
   CIVITAI_API_KEY=a1b2c3d4e5f6g7h8i9j0your_actual_key_here
   ```

5. Save the file

**Step 3: Create URL List File**

Create a text file (e.g., `lora_urls.txt`) with Civitai download URLs:

```
https://civitai.com/api/download/models/1542418
https://civitai.com/api/download/models/1673776
https://civitai.com/api/download/models/1679497
https://civitai.com/api/download/models/1686801
```

**How to get download URLs:**
1. Go to a LoRA model page on Civitai
2. Click the **Download** button
3. Right-click the download link and select **Copy Link Address**
4. Paste into your text file
5. Repeat for all models you want to download

**Step 4: Use the Node in ComfyUI**

1. Add the **Civitai Bulk Downloader** node to your workflow
2. Set parameters:
   - **txt_file_path**: `/path/to/lora_urls.txt`
   - **output_file_path**: `/models/lora/` (or your preferred LoRA folder)
   - **max_retries**: `3` (or adjust as needed)
3. Execute the workflow (Queue Prompt)

**Step 5: Monitor Progress**

Check the console output for:
- Download progress (updated every 10MB)
- Success/failure status for each file
- Final summary with counts

#### Example Console Output

```
============================================================
Civitai Bulk Downloader
============================================================

Reading URLs from: /home/user/lora_urls.txt
Found 4 URLs to download

Output directory: /models/lora/

[1/4] Processing: https://civitai.com/api/download/models/1542418
  Attempt 1/3...
    Progress: 25.0% (50MB / 200MB)
    Progress: 50.0% (100MB / 200MB)
    Progress: 75.0% (150MB / 200MB)
  ✓ Downloaded: awesome_lora_v1.safetensors (200MB)

[2/4] Processing: https://civitai.com/api/download/models/1673776
  Attempt 1/3...
  ✓ Downloaded: cool_style_lora.safetensors (150MB)

...

============================================================
Download Complete!
============================================================
Total: 4 files
Success: 4
Failed: 0
============================================================
```

#### Troubleshooting

**Error: "Civitai API key not configured"**
- Make sure you renamed `.env.example` to `.env`
- Check that `CIVITAI_API_KEY` is set in `.env`
- Restart ComfyUI after editing `.env`

**Error: "Text file not found"**
- Verify the `txt_file_path` is correct
- Use absolute paths (e.g., `C:/Users/YourName/lora_urls.txt` on Windows)

**Downloads failing repeatedly:**
- Check your internet connection
- Verify your API key is valid
- Increase `max_retries` parameter
- Some models may require NSFW access enabled on your Civitai account

**Security Notes:**
- ⚠️ Never commit the `.env` file to git (it's in `.gitignore` by default)
- ⚠️ Never share your API key publicly
- ⚠️ The API key grants access to your Civitai account

---

## Project Structure

```
comfyui-samenodes/
├── __init__.py                      # Node initialization and registration
├── float_to_string.py               # Float to String node implementation
├── batch_processor.py               # Batch Image Processor node implementation
├── lora_wildcard_generator.py       # LoRA Wildcard Generator node implementation
├── civitai_bulk_downloader.py       # Civitai Bulk Downloader node implementation
├── .env.example                     # Environment variables template for Civitai API
├── .env                             # Your actual environment variables (not in git)
├── .gitignore                       # Git ignore rules (.env excluded)
├── requirements.txt                 # Python dependencies
├── README.md                        # This documentation file
└── wildcards/                       # Example wildcards folder
    └── clothing.yaml                # Example clothing wildcard
```

---

## Requirements

### System Requirements

- **Python**: 3.8 or higher
- **ComfyUI**: Latest version recommended

### Python Dependencies

The following packages are installed via `requirements.txt`:

- **requests** (≥2.31.0): HTTP library for Civitai downloads
- **python-dotenv** (≥1.0.0): Environment variable management for API keys
- **pyyaml** (≥6.0): YAML file processing for wildcard generation

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.

**Useful Links:**
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Civitai](https://civitai.com/)
- [Civitai API Documentation](https://github.com/civitai/civitai/wiki/REST-API-Reference)
