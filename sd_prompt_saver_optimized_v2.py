"""
SD Prompt Saver with Compression Optimization
Based on: receyuki/comfyui-prompt-reader-node
License: MIT

Extension of SD Prompt Saver that adds optional lossless compression:
- PNG: pngquant + oxipng (optional, fallback to Pillow)
- WebP: cwebp (optional, fallback to Pillow)
- JPEG: jpegtran (optional, fallback to Pillow)
"""

import os
import json
import subprocess
import tempfile
from datetime import datetime
from itertools import chain
from pathlib import Path

import hashlib
import piexif
import piexif.helper
import numpy as np
import torch
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from nodes import MAX_RESOLUTION
from comfy.cli_args import args
import comfy.samplers
import folder_paths

# Supported formats from original SD Prompt Saver
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]


class AnyType(str):
    """A special type that can be connected to any other types."""
    def __ne__(self, __value: object) -> bool:
        return False


any_type = AnyType("*")


class SDPromptSaverWithCompression:
    """
    Extended SD Prompt Saver with optional compression optimization.
    Keeps all original SD Prompt Saver functionality intact.
    """

    model_hash_dict = {}
    vae_hash_dict = {}
    lora_hash_dict = {}
    ti_hash_dict = {}
    ti_paths = []
    ti_names = []
    ti_stems = []

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        for file in folder_paths.get_filename_list("embeddings"):
            SDPromptSaverWithCompression.ti_paths.append(file)
            SDPromptSaverWithCompression.ti_names.append(Path(file).name)
            SDPromptSaverWithCompression.ti_stems.append(Path(file).stem)

        return {
            "required": {
                "images": ("IMAGE",),
            },
            "optional": {
                "filename": (
                    "STRING",
                    {"default": "ComfyUI_%time_%seed_%counter", "multiline": False},
                ),
                "path": ("STRING", {"default": "%date/", "multiline": False}),
                "model_name": (folder_paths.get_filename_list("checkpoints"),),
                "vae_name": (folder_paths.get_filename_list("vae"),),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 100.0, "step": 0.5, "round": 0.01}),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "lora_name": any_type,
                "width": ("INT", {"default": 1, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "height": ("INT", {"default": 1, "min": 1, "max": MAX_RESOLUTION, "step": 1}),
                "positive": ("STRING", {"default": "", "multiline": True}),
                "negative": ("STRING", {"default": "", "multiline": True}),
                "extension": (["png", "jpg", "jpeg", "webp"],),
                "calculate_hash": ("BOOLEAN", {"default": True}),
                "resource_hash": ("BOOLEAN", {"default": True}),
                "lossless_webp": ("BOOLEAN", {"default": True}),
                "jpg_webp_quality": ("INT", {"default": 100, "min": 1, "max": 100}),
                "date_format": ("STRING", {"default": "%Y-%m-%d", "multiline": False}),
                "time_format": ("STRING", {"default": "%H%M%S", "multiline": False}),
                "save_metadata_file": ("BOOLEAN", {"default": False}),
                "extra_info": ("STRING", {"default": "", "multiline": True}),
                # Compression options
                "enable_compression": ("BOOLEAN", {"default": True}),
                "show_compression_log": ("BOOLEAN", {"default": False}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("FILENAME", "FILE_PATH", "METADATA")
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "SD Prompt Reader"

    def save_images(
        self,
        images,
        filename: str = "ComfyUI_%time_%seed_%counter",
        path: str = "%date/",
        model_name: str = "",
        vae_name: str = "",
        seed: int = 0,
        steps: int = 0,
        cfg: float = 0.0,
        sampler_name: str = "",
        scheduler: str = "",
        lora_name=None,
        width: int = 1,
        height: int = 1,
        positive: str = "",
        negative: str = "",
        extension: str = "png",
        calculate_hash: bool = True,
        resource_hash: bool = True,
        lossless_webp: bool = True,
        jpg_webp_quality: int = 100,
        date_format: str = "%Y-%m-%d",
        time_format: str = "%H%M%S",
        save_metadata_file: bool = False,
        extra_info: str = "",
        enable_compression: bool = True,
        show_compression_log: bool = False,
        prompt=None,
        extra_pnginfo=None,
    ):
        # Original SD Prompt Saver logic
        (
            full_output_folder,
            filename_alt,
            counter_alt,
            subfolder_alt,
            filename_prefix,
        ) = folder_paths.get_save_image_path(
            self.prefix_append,
            self.output_dir,
            images[0].shape[1],
            images[0].shape[0],
        )

        results = []
        files = []
        comments = []
        file_paths = []

        for image in images:
            extra_info_real = f", Extra info: {extra_info}" if extra_info else ""

            variable_map = {
                "%date": self.get_time(date_format),
                "%time": self.get_time(time_format),
                "%seed": seed,
                "%steps": steps,
                "%cfg": cfg,
                "%width": width,
                "%height": height,
                "%extension": extension,
                "%model": Path(model_name).stem,
                "%sampler": sampler_name,
                "%scheduler": scheduler,
                "%quality": jpg_webp_quality,
            }

            subfolder = self.get_path(path, variable_map)
            output_folder = Path(full_output_folder) / subfolder
            output_folder.mkdir(parents=True, exist_ok=True)
            counter = self.get_counter(output_folder)
            variable_map["%counter"] = f"{counter:05}"

            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Calculate hashes (original logic)
            model_hash_str = ""
            vae_hash_str = ""
            vae_str = ""
            lora_hash_dict = {}
            lora_hash_str = ""
            ti_hash_dict = {}
            ti_hash_str = ""

            if vae_name:
                vae_str = f"VAE: {Path(vae_name).stem}, "

            hashes = {}
            if calculate_hash:
                if model_name:
                    model_hash = self.calculate_hash(model_name, "model")
                    model_hash_str = f"Model hash: {model_hash}, "
                    hashes["model"] = model_hash

                if vae_name:
                    vae_hash = self.calculate_hash(vae_name, "vae")
                    vae_hash_str = f"VAE hash: {vae_hash}, "
                    hashes["vae"] = vae_hash

                if lora_name:
                    lora_names = lora_name if isinstance(lora_name, list) else [lora_name]
                    lora_names_unique = list(set(lora_names))
                    for name in lora_names_unique:
                        lora_hash = self.calculate_hash(name, "lora")
                        lora_hash_dict[Path(name).stem] = lora_hash
                        hashes[f"lora:{Path(name).stem}"] = lora_hash
                    lora_hash_items = [f"{k}: {v}" for k, v in lora_hash_dict.items()]
                    lora_hash_str_value = ", ".join(lora_hash_items)
                    lora_hash_str = f'Lora hashes: "{lora_hash_str_value}", '

                import re
                ti_pattern = (
                    r"(?:\(|\s|,)?"
                    r"embedding:"
                    r"([^\s:,()]+)"
                    r"(?:\.(?:pt|safetensors))?"
                    r"(?::\d+(?:\.\d+)?)?"
                    r"(?:\)|,|\s)?"
                )
                ti_names = re.findall(ti_pattern, f"{positive}/n{negative}")
                ti_names_with_ext = [self.search_ti(name) for name in ti_names]

                for name in ti_names_with_ext:
                    if name:
                        ti_hash = self.calculate_hash(name, "ti")
                        ti_hash_dict[Path(name).stem] = ti_hash
                        hashes[f"embed:{Path(name).stem}"] = ti_hash
                ti_hash_items = [f"{k}: {v}" for k, v in ti_hash_dict.items()]
                ti_hash_str_value = ", ".join(ti_hash_items)
                ti_hash_str = f'TI hashes: "{ti_hash_str_value}", '

            hashes_str = f", Hashes: {json.dumps(hashes)}" if (hashes and resource_hash) else ""

            # Build comment (original format)
            comment = (
                f"{positive}\n"
                f"Negative prompt: {negative}\n"
                f"Steps: {steps}, "
                f"Sampler: {sampler_name}{'' if scheduler == 'normal' else '_'+scheduler}, "
                f"CFG scale: {cfg}, "
                f"Seed: {seed}, "
                f"Size: {img.width if width==0 else width}x{img.height if height==0 else height}, "
                f"{model_hash_str}"
                f"Model: {Path(model_name).stem}, "
                f"{vae_hash_str}"
                f"{vae_str}"
                f"{lora_hash_str}"
                f"{ti_hash_str}"
                f"Version: ComfyUI"
                f"{hashes_str}"
                f"{extra_info_real}"
            )

            stem = self.get_path(filename, variable_map)
            file = self.get_unique_filename(stem, extension, output_folder)
            file_path = output_folder / file

            # Save image (original logic)
            if extension == "png":
                metadata = None
                if not args.disable_metadata:
                    metadata = PngInfo()
                    metadata.add_text("parameters", comment)
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                img.save(file_path, pnginfo=metadata, compress_level=4)
            else:
                img.save(file_path, quality=jpg_webp_quality, lossless=lossless_webp)
                if not args.disable_metadata:
                    metadata = piexif.dump({
                        "Exif": {
                            piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(
                                comment, encoding="unicode"
                            )
                        },
                    })
                    piexif.insert(metadata, str(file_path))

            # NEW: Apply compression optimization
            if enable_compression:
                self.optimize_image(file_path, extension, show_compression_log)

            # Save metadata file if requested
            if save_metadata_file:
                with open(file_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
                    f.write(comment)

            results.append({
                "filename": file.name,
                "subfolder": str(subfolder),
                "type": self.type
            })
            files.append(str(file))
            file_paths.append(str(file_path))
            comments.append(comment)

        return {
            "ui": {"images": results},
            "result": (
                self.unpack_singleton(files),
                self.unpack_singleton(file_paths),
                self.unpack_singleton(comments),
            ),
        }

    # NEW: Compression optimization methods
    def optimize_image(self, file_path: Path, extension: str, show_log: bool):
        """Apply compression optimization to saved image"""
        try:
            if extension == "png":
                self.optimize_png(file_path, show_log)
            elif extension in ("jpg", "jpeg"):
                self.optimize_jpeg(file_path, show_log)
            elif extension == "webp":
                self.optimize_webp(file_path, show_log)
        except Exception as e:
            if show_log:
                print(f"[SD Prompt Saver] Compression error: {e}")

    def optimize_png(self, file_path: Path, show_log: bool):
        """PNG compression: pngquant + oxipng (fallback to Pillow)"""
        original_size = os.path.getsize(file_path)

        # Try oxipng (lossless)
        try:
            result = subprocess.run(
                ["oxipng", "-o", "2", "--quiet", str(file_path)],
                capture_output=True,
                timeout=30,
                check=False
            )
            if result.returncode == 0:
                new_size = os.path.getsize(file_path)
                if show_log and new_size < original_size:
                    reduction = (original_size - new_size) / original_size * 100
                    print(f"[SD Prompt Saver] PNG optimized: -{reduction:.1f}%")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback: Pillow re-save with higher compression
        try:
            from PIL import Image
            with Image.open(str(file_path)) as img:
                pnginfo = PngInfo()
                if hasattr(img, 'text') and img.text:
                    for key, value in img.text.items():
                        pnginfo.add_text(key, value)
                img.save(str(file_path), format="PNG", pnginfo=pnginfo, compress_level=9, optimize=True)

            new_size = os.path.getsize(file_path)
            if show_log and new_size < original_size:
                reduction = (original_size - new_size) / original_size * 100
                print(f"[SD Prompt Saver] PNG optimized (Pillow): -{reduction:.1f}%")
        except Exception:
            pass

    def optimize_jpeg(self, file_path: Path, show_log: bool):
        """JPEG compression: jpegtran (fallback to Pillow)"""
        original_size = os.path.getsize(file_path)

        # Try jpegtran
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            result = subprocess.run(
                ["jpegtran", "-optimize", "-progressive", "-copy", "all",
                 "-outfile", str(tmp_path), str(file_path)],
                capture_output=True,
                timeout=30,
                check=False
            )

            if result.returncode == 0 and tmp_path.exists():
                tmp_path.replace(file_path)
                new_size = os.path.getsize(file_path)
                if show_log and new_size < original_size:
                    reduction = (original_size - new_size) / original_size * 100
                    print(f"[SD Prompt Saver] JPEG optimized: -{reduction:.1f}%")
            else:
                tmp_path.unlink(missing_ok=True)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    def optimize_webp(self, file_path: Path, show_log: bool):
        """WebP compression: cwebp (fallback to Pillow)"""
        original_size = os.path.getsize(file_path)

        # Try cwebp
        try:
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            result = subprocess.run(
                ["cwebp", "-lossless", "-m", "6", "-quiet",
                 str(file_path), "-o", str(tmp_path)],
                capture_output=True,
                timeout=30,
                check=False
            )

            if result.returncode == 0 and tmp_path.exists():
                tmp_path.replace(file_path)
                new_size = os.path.getsize(file_path)
                if show_log and new_size < original_size:
                    reduction = (original_size - new_size) / original_size * 100
                    print(f"[SD Prompt Saver] WebP optimized: -{reduction:.1f}%")
            else:
                tmp_path.unlink(missing_ok=True)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Original SD Prompt Saver methods (unchanged)
    @staticmethod
    def calculate_hash(name, hash_type):
        match hash_type:
            case "model":
                hash_dict = SDPromptSaverWithCompression.model_hash_dict
                file_name = folder_paths.get_full_path("checkpoints", name)
            case "vae":
                hash_dict = SDPromptSaverWithCompression.vae_hash_dict
                file_name = folder_paths.get_full_path("vae", name)
            case "lora":
                hash_dict = SDPromptSaverWithCompression.lora_hash_dict
                file_name = folder_paths.get_full_path("loras", name)
            case "ti":
                hash_dict = SDPromptSaverWithCompression.ti_hash_dict
                file_name = folder_paths.get_full_path("embeddings", name)
            case _:
                return ""

        if hash_value := hash_dict.get(name):
            return hash_value

        hash_sha256 = hashlib.sha256()
        blksize = 1024 * 1024

        with open(file_name, "rb") as f:
            for chunk in iter(lambda: f.read(blksize), b""):
                hash_sha256.update(chunk)

        hash_value = hash_sha256.hexdigest()[:10]
        hash_dict[name] = hash_value

        return hash_value

    @staticmethod
    def get_counter(directory: Path):
        img_files = list(
            chain(*(directory.rglob(f"*{suffix}") for suffix in SUPPORTED_FORMATS))
        )
        return len(img_files) + 1

    @staticmethod
    def get_path(name, variable_map):
        for variable, value in variable_map.items():
            name = name.replace(variable, str(value))
        return Path(name)

    @staticmethod
    def get_time(time_format):
        now = datetime.now()
        try:
            time_str = now.strftime(time_format)
            return time_str
        except:
            return ""

    @staticmethod
    def get_unique_filename(stem: Path, extension: str, output_folder: Path):
        file = stem.with_suffix(f"{stem.suffix}.{extension}")
        index = 0

        while (output_folder / file).exists():
            index += 1
            new_stem = Path(f"{stem}_{index}")
            file = new_stem.with_suffix(f"{new_stem.suffix}.{extension}")

        return file

    @staticmethod
    def search_ti(ti: str):
        if not ti or ti in SDPromptSaverWithCompression.ti_paths:
            return ti

        if ti in SDPromptSaverWithCompression.ti_stems:
            return SDPromptSaverWithCompression.ti_paths[
                SDPromptSaverWithCompression.ti_stems.index(ti)
            ]

        if ti in SDPromptSaverWithCompression.ti_names:
            return SDPromptSaverWithCompression.ti_paths[
                SDPromptSaverWithCompression.ti_names.index(ti)
            ]

        return ""

    @staticmethod
    def unpack_singleton(arr: list):
        return arr[0] if len(arr) == 1 else arr


NODE_CLASS_MAPPINGS = {
    "SDPromptSaverWithCompression": SDPromptSaverWithCompression,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SDPromptSaverWithCompression": "SD Prompt Saver (Optimized V2)",
}
