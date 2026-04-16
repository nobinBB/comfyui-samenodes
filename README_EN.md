# ComfyUI Same Nodes

**Languages / 言語 / 语言 / 언어:**  
🇯🇵 [日本語](README.md) | 🇺🇸 [English](README_EN.md) | 🇨🇳 [简体中文](README_CN.md) | 🇰🇷 [한국어](README_KR.md)

---

A collection of custom nodes for ComfyUI providing essential utilities for string conversion, batch processing, LoRA management, and automatic downloads to enhance your workflow.

## Overview

This custom node pack provides essential tools for ComfyUI users:

### Text Processing
- **Float to String**: Precise float-to-string conversion with decimal control
- **Text Split 3**: Split text into 3 outputs (supports `<!...!>` and `<#...#>` delimiters)
- **Repeat Text Lines**: Repeat text specified number of times

### Image & Prompt Processing
- **Batch Image Processor**: Efficient batch image processing
- **Batch Image Compressor**: Bulk image compression (PNG: 60-80% reduction, JPEG optimization)
- **Image Format Converter**: Bulk image format conversion (PNG/JPEG/WebP/BMP/TIFF)
- **Images to PDF**: Convert multiple images to single PDF
- **Extract Prompt from Image**: Extract prompts from image metadata (ComfyUI format)
- **A1111 Prompt Splitter**: Extract positive/negative prompts from A1111/SD WebUI images
- **SD Prompt Saver (Optimized)**: A1111-compatible metadata + lossless compression (PNG/WebP/JPEG, 20-50% reduction)

### LoRA Management
- **LoRA Wildcard Generator**: Auto-generate YAML wildcards from Civitai metadata
- **Civitai LoRA Searcher**: Search Civitai API by SHA256 (bulk JSON folder processing)
- **LoRA to Civitai URL**: Get Civitai URL from LoRA syntax

### Embedding Management
- **Embedding Wildcard Generator**: Auto-generate YAML wildcards from Embedding files
- **Embedding Path Resolver**: Auto-resolve `embedding:name` to `embedding:path/name`

### Utilities
- **Get ComfyUI Input Path**: Get ComfyUI input directory path
- **Seed Step N**: Increment seed every N steps (persistent counter, independent instances)

---

## Installation

### Step 1: Clone Repository

Navigate to ComfyUI's `custom_nodes` folder and clone this repository:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/nobinBB/comfyui-samenodes.git
```

### Step 2: Install Dependencies

Install required Python packages:

```bash
cd comfyui-samenodes
pip install -r requirements.txt
```

### Step 3: Restart ComfyUI

Restart ComfyUI to load the new nodes.

---

## Featured Node: SD Prompt Saver (Optimized)

### Hybrid Compression (External Tools + Pillow Fallback)

**Works with external tools for maximum compression, falls back to Pillow if tools are not installed.**

| Format | External Tools (High Compression) | Pillow Fallback | Compression Rate |
|--------|----------------------------------|-----------------|------------------|
| PNG | **pngquant 85-95 + oxipng** | compress_level=9 | **35-50%** → 10-25% |
| WebP | cwebp -lossless | lossless mode | 20-40% → 5-20% |
| JPEG | jpegtran | optimize + progressive | 3-15% → 5-15% |

**PNG 2-Stage Compression:**
1. pngquant (quality 85-95): Visually lossless, 30-40% reduction
2. oxipng (-o 6): Lossless additional optimization, 5-10% more reduction
3. **Total: 35-50% reduction, 95% visual quality maintained**

### Installation of External Tools (Optional)

#### **Recommended Method: Local `tools` Folder**

1. **Create tools folder:**
   ```
   ComfyUI/custom_nodes/comfyui-samenodes/tools/
   ```

2. **Download and place binaries:**
   - **pngquant**: https://pngquant.org/
   - **oxipng**: https://github.com/shssoichiro/oxipng/releases
   - **cwebp**: https://developers.google.com/speed/webp/download
   - **jpegtran**: https://jpegclub.org/jpegtran/

3. **Folder structure:**
   ```
   tools/
   ├── pngquant.exe    # Windows
   ├── oxipng.exe      # Windows
   ├── cwebp.exe       # Windows
   └── jpegtran.exe    # Windows
   ```

4. **Restart ComfyUI**

**Note:** The node prioritizes `./tools/` folder → system PATH. No admin rights or system PATH setup required.

#### **Alternative: System Installation**

**Mac:**
```bash
brew install pngquant oxipng webp jpeg-turbo
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install pngquant oxipng webp libjpeg-turbo-progs
```

**Linux (Fedora):**
```bash
sudo dnf install pngquant oxipng libwebp-tools libjpeg-turbo-utils
```

### Compression Example

**With external tools (PNG → pngquant + oxipng):**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (pngquant 85-95): 2,453,120 B → 1,471,872 B (-40.0%)
[SDPromptSaverOptimized] PNG (oxipng): 1,471,872 B → 1,324,685 B (-10.0%)
[SDPromptSaverOptimized] PNG Total (pngquant+oxipng): 2,453,120 B → 1,324,685 B (-46.0%)
============================================================
```

**Without external tools (PNG → Pillow):**
```
[SDPromptSaverOptimized] saved: D:/output/2026-04-15/ComfyUI_153022_1234567_0001.png
[SDPromptSaverOptimized] PNG (Pillow): 2,453,120 B → 2,103,552 B (-14.2%)
```

---

## Requirements

### System Requirements
- **Python**: 3.8 or higher
- **ComfyUI**: Latest version recommended

### Python Dependencies

Installed via `requirements.txt`:
- **requests** (≥2.31.0): HTTP library for Civitai downloads
- **python-dotenv** (≥1.0.0): Environment variable management for API keys
- **pyyaml** (≥6.0): YAML file processing for wildcard generation
- **Pillow** (≥9.0.0): Image processing and metadata extraction
- **piexif** (≥1.1.3): EXIF metadata for JPEG/WebP

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## License

MIT License

Copyright (c) 2024 nobinBB

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

### Derived & Modified Components Attribution

This project includes components based on the following open-source projects:

#### 1. SD Prompt Saver (Optimized)
- **Original Project:** [receyuki/comfyui-prompt-reader-node](https://github.com/receyuki/comfyui-prompt-reader-node)
- **Original Copyright:** Copyright (c) 2023 receyuki
- **Modifications Copyright:** Copyright (c) 2024 nobinBB
- **License:** MIT License
- **File:** `sd_prompt_saver_optimized.py`
- **Key Changes:**
  - PNG/WebP/JPEG full format support
  - Hybrid compression (pngquant 85-95 + oxipng, cwebp, jpegtran)
  - Local tools folder support
  - 35-50% compression rate (PNG)

#### 2. LoRA Tag Power Loader Extended
- **Original Project:** LoRA Tag Power Loader
- **Modifications Copyright:** Copyright (c) 2024 nobinBB
- **License:** MIT License
- **File:** `lora_tag_power_loader_extended.py`
- **Key Changes:**
  - Added second_text input/output
  - Original functionality fully preserved

#### 3. Text Split 3
- **Concept Origin:** NegativeWildcardsProcessor
- **Implementation Copyright:** Copyright (c) 2024 nobinBB
- **License:** MIT License
- **File:** `text_split_3.py`
- **Description:** Original implementation inspired by NegativeWildcardsProcessor concept

---

### Other Components

All other nodes (Float to String, Batch Image Compressor, LoRA Wildcard Generator, etc.) are completely original implementations by nobinBB.

```
Copyright (c) 2024 nobinBB
License: MIT
```

---

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.

**Useful Links:**
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Civitai](https://civitai.com/)
