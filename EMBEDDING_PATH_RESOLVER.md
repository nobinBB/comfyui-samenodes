# Embedding Path Resolver

## Overview

The **Embedding Path Resolver** node automatically resolves short embedding names to their full relative paths in ComfyUI.

This allows you to organize embeddings in subfolders while using short, simple names in your prompts.

## Purpose

- **Problem**: You want to organize embeddings in subfolders (e.g., `pose/`, `face/`, `style/`) but don't want to write full paths in prompts
- **Solution**: Write `embedding:sit_front` in your prompt, and this node automatically resolves it to `embedding:pose/sit_front.pt`

## Features

- 📁 Searches `models/embeddings` recursively for matching files
- 🔄 Automatically resolves `embedding:name` to `embedding:subpath/filename.ext`
- 🎯 Matches based on filename (without extension)
- 💾 Caches results for performance
- 🔒 Only touches `embedding:` patterns, leaves everything else unchanged
- ⚡ First-match priority for duplicate names

## Supported File Types

- `.pt`
- `.safetensors`
- `.bin`
- `.ckpt`
- `.pth`

## Usage

### Input Example
```
1girl, embedding:sit_front, embedding:smug_face, masterpiece
```

### Output Example
```
1girl, embedding:pose/sit_front.pt, embedding:face/smug_face.pt, masterpiece
```

### Workflow

1. Add the **Embedding Path Resolver** node to your workflow
2. Connect your text input (containing `embedding:name` patterns)
3. Connect the output to CLIP Text Encode or other text nodes
4. The node will automatically resolve paths

## How It Works

1. **Scans** `models/embeddings` folder recursively
2. **Builds** a map of `basename → relative_path`
3. **Matches** `embedding:name` patterns in your text
4. **Replaces** with `embedding:subpath/filename.ext`
5. **Returns** the resolved text

## Folder Structure Example

```
models/embeddings/
├── pose/
│   ├── sit_front.pt
│   └── stand_back.safetensors
├── face/
│   ├── smug_face.pt
│   └── angry_face.safetensors
└── style/
    └── anime_style.pt
```

With this structure:
- `embedding:sit_front` → `embedding:pose/sit_front.pt`
- `embedding:smug_face` → `embedding:face/smug_face.pt`
- `embedding:anime_style` → `embedding:style/anime_style.pt`

## Notes

- ✅ Only resolves short names (no path separators)
- ✅ Leaves full paths unchanged (e.g., `embedding:pose/sit_front.pt` stays as-is)
- ✅ If not found, keeps original text
- ✅ LoRA and other patterns are untouched
- ✅ Cache refreshes when embeddings folder is modified

## Category

`utils/text`

## Node Name

**Embedding Path Resolver**
