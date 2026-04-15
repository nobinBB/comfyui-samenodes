"""
SD Prompt Saver Optimized Node for ComfyUI
Saves images with A1111-compatible metadata and optimizes with oxipng

Based on: https://github.com/receyuki/comfyui-prompt-reader-node
License: MIT (original project)
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
import torch
import folder_paths


class SDPromptSaverOptimized:
    """
    Save images with A1111-compatible metadata and oxipng lossless compression.
    Based on SDPromptSaver from comfyui-prompt-reader-node.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "optional": {
                # File naming and path
                "filename": ("STRING", {
                    "default": "ComfyUI_%time_%seed_%counter",
                    "multiline": False
                }),
                "path": ("STRING", {
                    "default": "%date/",
                    "multiline": False
                }),
                "date_format": ("STRING", {
                    "default": "%Y-%m-%d",
                    "multiline": False
                }),
                "time_format": ("STRING", {
                    "default": "%H%M%S",
                    "multiline": False
                }),

                # Model and generation parameters
                "model_name": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "vae_name": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff
                }),
                "steps": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 10000
                }),
                "cfg": ("FLOAT", {
                    "default": 7.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.1
                }),
                "sampler_name": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "scheduler": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "width": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 48000
                }),
                "height": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 48000
                }),
                "positive": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                "negative": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                "lora_name": ("STRING", {
                    "default": "",
                    "multiline": False
                }),

                # Hash calculation
                "calculate_hash": ("BOOLEAN", {
                    "default": True
                }),
                "resource_hash": ("BOOLEAN", {
                    "default": True
                }),

                # Metadata file
                "save_metadata_file": ("BOOLEAN", {
                    "default": False
                }),

                # Oxipng optimization
                "optimization_level": ("INT", {
                    "default": 4,
                    "min": 0,
                    "max": 6,
                    "step": 1
                }),
                "use_zopfli": ("BOOLEAN", {
                    "default": False
                }),
                "preserve_metadata": ("BOOLEAN", {
                    "default": True
                }),
                "show_compression_log": ("BOOLEAN", {
                    "default": True
                }),
                "skip_optimization": ("BOOLEAN", {
                    "default": False
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("FILENAME", "FILE_PATH", "METADATA")
    FUNCTION = "save_images"
    CATEGORY = "SD Prompt Reader"
    OUTPUT_NODE = True

    @staticmethod
    def get_time(time_format):
        """Get current time formatted string"""
        return datetime.now().strftime(time_format)

    @staticmethod
    def get_counter(directory: Path):
        """Get next counter number based on existing files"""
        if not directory.exists():
            return 1

        img_files = list(directory.glob("*.png"))
        return len(img_files) + 1

    @staticmethod
    def get_path(name, variable_map):
        """Replace variables in path/filename template"""
        for variable, value in variable_map.items():
            name = name.replace(variable, str(value))
        return name

    @staticmethod
    def calculate_model_hash(file_path, hash_length=10):
        """Calculate SHA256 hash of model file"""
        try:
            if not os.path.exists(file_path):
                return None

            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)

            return sha256.hexdigest()[:hash_length]
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None

    def optimize_with_oxipng(self, file_path, optimization_level, use_zopfli,
                            preserve_metadata, show_compression_log):
        """
        Optimize PNG with oxipng

        Returns:
            Tuple of (success, original_size, optimized_size)
        """
        try:
            # Get original file size
            original_size = os.path.getsize(file_path)

            # Build oxipng command
            cmd = ["oxipng", "-o", str(optimization_level)]

            if use_zopfli:
                cmd.append("-Z")

            if not preserve_metadata:
                cmd.extend(["--strip", "safe"])

            cmd.append(str(file_path))

            # Run oxipng
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Get optimized file size
            optimized_size = os.path.getsize(file_path)

            if result.returncode != 0:
                print(f"[SDPromptSaverOptimized] oxipng warning: {result.stderr}")

            if show_compression_log:
                reduction = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
                print(f"[SDPromptSaverOptimized] optimized: {original_size:,} B → {optimized_size:,} B (-{reduction:.1f}%)")

            return True, original_size, optimized_size

        except FileNotFoundError:
            print("[SDPromptSaverOptimized] WARNING: oxipng not found. Please install oxipng for PNG optimization.")
            print("  - Windows: Download from https://github.com/shssoichiro/oxipng/releases")
            print("  - Mac: brew install oxipng")
            print("  - Linux: cargo install oxipng or use package manager")
            return False, 0, 0

        except subprocess.TimeoutExpired:
            print(f"[SDPromptSaverOptimized] oxipng timeout for {file_path}")
            return False, 0, 0

        except Exception as e:
            print(f"[SDPromptSaverOptimized] oxipng error: {e}")
            return False, 0, 0

    def save_images(self, images, filename="ComfyUI_%time_%seed_%counter",
                   path="%date/", date_format="%Y-%m-%d", time_format="%H%M%S",
                   model_name="", vae_name="", seed=0, steps=20, cfg=7.0,
                   sampler_name="", scheduler="", width=512, height=512,
                   positive="", negative="", lora_name="",
                   calculate_hash=True, resource_hash=True, save_metadata_file=False,
                   optimization_level=4, use_zopfli=False, preserve_metadata=True,
                   show_compression_log=True, skip_optimization=False,
                   prompt=None, extra_pnginfo=None):
        """
        Save images with A1111 metadata and oxipng optimization

        Returns:
            Tuple of (filename, file_path, metadata)
        """

        # Get output directory
        output_dir = folder_paths.get_output_directory()

        # Build variable map for template replacement
        variable_map = {
            "%date": self.get_time(date_format),
            "%time": self.get_time(time_format),
            "%seed": seed,
            "%steps": steps,
            "%cfg": cfg,
            "%width": width,
            "%height": height,
            "%model": Path(model_name).stem if model_name else "unknown",
            "%sampler": sampler_name if sampler_name else "unknown",
            "%scheduler": scheduler if scheduler else "normal",
        }

        # Process path template
        subfolder = self.get_path(path, variable_map)

        # Determine output folder (absolute or relative)
        if Path(subfolder).is_absolute():
            output_folder = Path(subfolder)
        else:
            output_folder = Path(output_dir) / subfolder

        # Create directory if not exists
        output_folder.mkdir(parents=True, exist_ok=True)

        # Calculate hashes if requested
        model_hash = ""
        if calculate_hash and model_name:
            model_paths = folder_paths.get_filename_list("checkpoints")
            for model_path in model_paths:
                if Path(model_path).name == model_name:
                    full_path = folder_paths.get_full_path("checkpoints", model_path)
                    hash_value = self.calculate_model_hash(full_path)
                    if hash_value:
                        model_hash = hash_value
                    break

        # Build A1111 format metadata string
        sampler_str = sampler_name if sampler_name else "unknown"
        scheduler_str = scheduler if scheduler else "normal"
        if scheduler_str != "normal":
            sampler_str = f"{sampler_str}_{scheduler_str}"

        model_hash_str = f"Model hash: {model_hash}, " if model_hash else ""
        vae_str = f"VAE: {Path(vae_name).stem}, " if vae_name else ""
        lora_str = f'Lora hashes: "{lora_name}", ' if lora_name else ""

        metadata_text = (
            f"{positive}\n"
            f"Negative prompt: {negative}\n"
            f"Steps: {steps}, "
            f"Sampler: {sampler_str}, "
            f"CFG scale: {cfg}, "
            f"Seed: {seed}, "
            f"Size: {width}x{height}, "
            f"{model_hash_str}"
            f"Model: {Path(model_name).stem if model_name else 'unknown'}, "
            f"{vae_str}"
            f"{lora_str}"
            f"Version: ComfyUI"
        )

        # Process each image
        results = []
        filenames = []
        file_paths = []

        for i, image_tensor in enumerate(images):
            # Convert tensor to PIL Image
            img_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array)

            # Get counter for this image
            counter = self.get_counter(output_folder) + i
            variable_map["%counter"] = f"{counter:05}"

            # Process filename template
            file_name = self.get_path(filename, variable_map)
            file_path = output_folder / f"{file_name}.png"

            # Ensure unique filename
            counter_offset = 0
            while file_path.exists():
                counter_offset += 1
                variable_map["%counter"] = f"{counter + counter_offset:05}"
                file_name = self.get_path(filename, variable_map)
                file_path = output_folder / f"{file_name}.png"

            # Prepare PNG metadata
            pnginfo = PngInfo()
            pnginfo.add_text("parameters", metadata_text)

            # Add ComfyUI workflow data
            if prompt is not None:
                pnginfo.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for key in extra_pnginfo:
                    pnginfo.add_text(key, json.dumps(extra_pnginfo[key]))

            # Save PNG with metadata
            img.save(str(file_path), pnginfo=pnginfo, compress_level=4)

            print(f"[SDPromptSaverOptimized] saved: {file_path}")

            # Optimize with oxipng
            if not skip_optimization:
                self.optimize_with_oxipng(
                    file_path,
                    optimization_level,
                    use_zopfli,
                    preserve_metadata,
                    show_compression_log
                )

            # Save metadata to text file if requested
            if save_metadata_file:
                metadata_file = file_path.with_suffix('.txt')
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    f.write(metadata_text)

            filenames.append(file_name + ".png")
            file_paths.append(str(file_path))
            results.append({
                "filename": file_name + ".png",
                "subfolder": str(subfolder) if not Path(subfolder).is_absolute() else "",
                "type": "output"
            })

        # Return results
        return {
            "ui": {"images": results},
            "result": (
                ", ".join(filenames),
                ", ".join(file_paths),
                metadata_text
            )
        }


NODE_CLASS_MAPPINGS = {
    "SDPromptSaverOptimized": SDPromptSaverOptimized,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SDPromptSaverOptimized": "SD Prompt Saver (Optimized)",
}
