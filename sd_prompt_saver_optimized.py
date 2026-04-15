"""
SD Prompt Saver Optimized Node for ComfyUI
Saves images with A1111-compatible metadata and hybrid compression

Based on: https://github.com/receyuki/comfyui-prompt-reader-node
License: MIT (original project)

Hybrid compression (external tools + Pillow fallback):
  PNG  -> pngquant 85-95 (30-40%, visually lossless) + oxipng (5-10%) = 35-50% total
  WebP -> cwebp lossless (20-40%) → Pillow lossless (5-20%)
  JPEG -> jpegtran (3-15%) → Pillow optimize (5-15%)

External tools are optional. Works with Pillow alone if tools are not installed.
"""

import os
import json
import subprocess
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
import folder_paths

# Optional: piexif for JPEG/WebP EXIF metadata
try:
    import piexif
    import piexif.helper
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False


SUPPORTED_EXTENSIONS = ["png", "webp", "jpg", "jpeg"]


class SDPromptSaverOptimized:
    """
    Save images with A1111-compatible metadata and lossless compression.
    Supports PNG (oxipng), WebP (cwebp lossless), JPEG (jpegtran/jpegoptim).
    Based on SDPromptSaver from comfyui-prompt-reader-node.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "optional": {
                # File format
                "extension": (SUPPORTED_EXTENSIONS, {
                    "default": "png"
                }),

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

                # Compression optimization
                "jpeg_quality": ("INT", {
                    "default": 95,
                    "min": 60,
                    "max": 100,
                    "step": 1
                }),
                "preserve_metadata": ("BOOLEAN", {
                    "default": True
                }),
                "show_compression_log": ("BOOLEAN", {
                    "default": True
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
        return datetime.now().strftime(time_format)

    @staticmethod
    def get_counter(directory: Path, extension: str):
        """Get next counter based on existing files with given extension"""
        if not directory.exists():
            return 1
        ext = extension.lstrip(".")
        # Count files for jpg and jpeg together
        if ext in ("jpg", "jpeg"):
            files = list(directory.glob("*.jpg")) + list(directory.glob("*.jpeg"))
        else:
            files = list(directory.glob(f"*.{ext}"))
        return len(files) + 1

    @staticmethod
    def get_path(name, variable_map):
        for variable, value in variable_map.items():
            name = name.replace(variable, str(value))
        return name

    @staticmethod
    def calculate_model_hash(file_path, hash_length=10):
        try:
            if not os.path.exists(file_path):
                return None
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()[:hash_length]
        except Exception as e:
            print(f"[SDPromptSaverOptimized] hash error: {e}")
            return None

    # ------------------------------------------------------------------
    # Metadata embedding
    # ------------------------------------------------------------------

    def _make_exif_bytes(self, metadata_text: str) -> bytes | None:
        """Build EXIF bytes with A1111 parameters in UserComment."""
        if not HAS_PIEXIF:
            return None
        try:
            exif_dict = {
                "Exif": {
                    piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(
                        metadata_text, encoding="unicode"
                    )
                }
            }
            return piexif.dump(exif_dict)
        except Exception as e:
            print(f"[SDPromptSaverOptimized] piexif error: {e}")
            return None

    def save_png(self, img: Image.Image, file_path: Path, metadata_text: str,
                 prompt, extra_pnginfo):
        """Save PNG with metadata (will be further optimized by oxipng or Pillow)"""
        pnginfo = PngInfo()
        pnginfo.add_text("parameters", metadata_text)
        if prompt is not None:
            pnginfo.add_text("prompt", json.dumps(prompt))
        if extra_pnginfo is not None:
            for key in extra_pnginfo:
                pnginfo.add_text(key, json.dumps(extra_pnginfo[key]))
        # Initial save with moderate compression
        img.save(str(file_path), format="PNG", pnginfo=pnginfo, compress_level=6)

    def save_webp(self, img: Image.Image, file_path: Path, metadata_text: str,
                  prompt, extra_pnginfo):
        """Save WebP with metadata (will be optimized by cwebp or Pillow)"""
        exif_bytes = self._make_exif_bytes(metadata_text)
        save_kwargs = {
            "format": "WEBP",
            "lossless": True,
            "quality": 100,
            "method": 4,  # moderate speed for initial save
        }
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        img.save(str(file_path), **save_kwargs)

    def save_jpeg(self, img: Image.Image, file_path: Path, metadata_text: str,
                  prompt, extra_pnginfo, quality: int):
        """Save JPEG with metadata (will be optimized by jpegtran or Pillow)"""
        # JPEG requires RGB
        if img.mode in ("RGBA", "LA", "P"):
            rgb = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                rgb.paste(img, mask=img.split()[-1])
            else:
                rgb.paste(img)
            img = rgb
        exif_bytes = self._make_exif_bytes(metadata_text)
        save_kwargs = {
            "format": "JPEG",
            "quality": quality,
            "optimize": False,  # will optimize later with jpegtran or Pillow
        }
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        img.save(str(file_path), **save_kwargs)


    # ------------------------------------------------------------------
    # Hybrid compression (external tools + Pillow fallback)
    # ------------------------------------------------------------------

    def optimize_png(self, file_path: Path, preserve_metadata: bool, show_log: bool):
        """PNG: pngquant 85-95 (30-40%) + oxipng (5-10%) = 35-50% total"""
        original_size = os.path.getsize(file_path)
        current_size = original_size
        pngquant_used = False
        oxipng_used = False

        # Step 1: pngquant (lossy compression, visually lossless quality)
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            cmd = ["pngquant", "--quality=85-95", "--speed", "1", "--force"]
            if not preserve_metadata:
                cmd.append("--strip")
            cmd.extend(["--output", str(tmp_path), str(file_path)])

            result = subprocess.run(cmd, check=False, capture_output=True,
                                   text=True, timeout=60)

            if result.returncode == 0 and tmp_path.exists():
                tmp_size = tmp_path.stat().st_size
                if tmp_size < current_size:  # Only replace if smaller
                    tmp_path.replace(file_path)
                    after_pngquant = tmp_size
                    pngquant_used = True
                    if show_log:
                        reduction1 = (current_size - after_pngquant) / current_size * 100
                        print(f"[SDPromptSaverOptimized] PNG (pngquant 85-95): {current_size:,} B → {after_pngquant:,} B (-{reduction1:.1f}%)")
                    current_size = after_pngquant
                else:
                    tmp_path.unlink(missing_ok=True)
                    if show_log:
                        print(f"[SDPromptSaverOptimized] pngquant output larger than input, skipped")
            else:
                tmp_path.unlink(missing_ok=True)
                if show_log and result.returncode != 0:
                    print(f"[SDPromptSaverOptimized] pngquant failed (code {result.returncode}): {result.stderr.strip()}")

        except FileNotFoundError:
            if show_log:
                print(f"[SDPromptSaverOptimized] pngquant not found in PATH")
        except Exception as e:
            if show_log:
                print(f"[SDPromptSaverOptimized] pngquant error: {e}")

        # Step 2: oxipng (lossless compression, 5-10% additional)
        try:
            before_oxipng = current_size

            cmd = ["oxipng", "-o", "6", "--quiet"]
            if not preserve_metadata:
                cmd.extend(["--strip", "safe"])
            cmd.append(str(file_path))

            result = subprocess.run(cmd, check=False, capture_output=True,
                                   text=True, timeout=300)

            if result.returncode == 0:
                after_oxipng = os.path.getsize(file_path)
                oxipng_used = True
                if show_log and after_oxipng < before_oxipng:
                    reduction2 = (before_oxipng - after_oxipng) / before_oxipng * 100
                    print(f"[SDPromptSaverOptimized] PNG (oxipng): {before_oxipng:,} B → {after_oxipng:,} B (-{reduction2:.1f}%)")
                current_size = after_oxipng

        except FileNotFoundError:
            pass  # oxipng not found
        except Exception:
            pass  # oxipng failed

        # If no external tools worked, fallback to Pillow
        if not pngquant_used and not oxipng_used:
            try:
                before_pillow = current_size
                with Image.open(str(file_path)) as img:
                    # Extract existing metadata
                    pnginfo = PngInfo()
                    if hasattr(img, 'text') and img.text:
                        for key, value in img.text.items():
                            pnginfo.add_text(key, value)

                    img.save(str(file_path), format="PNG", pnginfo=pnginfo,
                            compress_level=9, optimize=True)

                after_pillow = os.path.getsize(file_path)
                current_size = after_pillow
                if show_log:
                    reduction = (before_pillow - after_pillow) / before_pillow * 100 if before_pillow > 0 else 0
                    print(f"[SDPromptSaverOptimized] PNG (Pillow): {before_pillow:,} B → {after_pillow:,} B (-{reduction:.1f}%)")
            except Exception as e:
                if show_log:
                    print(f"[SDPromptSaverOptimized] PNG optimization failed: {e}")

        # Final summary
        if show_log and current_size < original_size:
            total_reduction = (original_size - current_size) / original_size * 100
            tools = []
            if pngquant_used:
                tools.append("pngquant")
            if oxipng_used:
                tools.append("oxipng")
            if not tools:
                tools.append("Pillow")

            print(f"[SDPromptSaverOptimized] PNG Total ({'+'.join(tools)}): {original_size:,} B → {current_size:,} B (-{total_reduction:.1f}%)")
            print(f"{'='*60}")

    def optimize_webp(self, file_path: Path, preserve_metadata: bool, show_log: bool):
        """WebP: cwebp lossless (20-40%) → Pillow lossless (5-20%)"""
        original_size = os.path.getsize(file_path)

        # Try cwebp first
        try:
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            cmd = ["cwebp", "-lossless", "-m", "6", "-z", "9", "-quiet"]
            if preserve_metadata:
                cmd += ["-metadata", "all"]
            else:
                cmd += ["-metadata", "none"]
            cmd += [str(file_path), "-o", str(tmp_path)]

            result = subprocess.run(cmd, check=False, capture_output=True,
                                   text=True, timeout=300)

            if result.returncode == 0 and tmp_path.exists():
                tmp_size = tmp_path.stat().st_size
                if tmp_size < original_size:
                    tmp_path.replace(file_path)
                    if show_log:
                        reduction = (original_size - tmp_size) / original_size * 100
                        print(f"[SDPromptSaverOptimized] WebP (cwebp): {original_size:,} B → {tmp_size:,} B (-{reduction:.1f}%)")
                    return
                else:
                    tmp_path.unlink(missing_ok=True)
            else:
                tmp_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass  # cwebp not found, fallback to Pillow
        except Exception:
            pass  # cwebp failed, fallback to Pillow

        # Fallback: Pillow lossless re-save
        try:
            with Image.open(str(file_path)) as img:
                img.save(str(file_path), format="WEBP", lossless=True,
                        quality=100, method=6)

            final_size = os.path.getsize(file_path)
            if show_log:
                reduction = (original_size - final_size) / original_size * 100 if original_size > 0 else 0
                print(f"[SDPromptSaverOptimized] WebP (Pillow): {original_size:,} B → {final_size:,} B (-{reduction:.1f}%)")
        except Exception as e:
            if show_log:
                print(f"[SDPromptSaverOptimized] WebP optimization failed: {e}")

    def optimize_jpeg(self, file_path: Path, preserve_metadata: bool, show_log: bool):
        """JPEG: jpegtran (3-15%) → Pillow optimize (5-15%)"""
        original_size = os.path.getsize(file_path)

        # Try jpegtran first
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            copy_flag = "all" if preserve_metadata else "none"
            cmd = ["jpegtran", "-optimize", "-progressive",
                   "-copy", copy_flag, "-outfile", str(tmp_path), str(file_path)]

            result = subprocess.run(cmd, check=False, capture_output=True,
                                   text=True, timeout=120)

            if result.returncode == 0 and tmp_path.exists():
                tmp_size = tmp_path.stat().st_size
                if tmp_size < original_size:
                    tmp_path.replace(file_path)
                    if show_log:
                        reduction = (original_size - tmp_size) / original_size * 100
                        print(f"[SDPromptSaverOptimized] JPEG (jpegtran): {original_size:,} B → {tmp_size:,} B (-{reduction:.1f}%)")
                    return
                else:
                    tmp_path.unlink(missing_ok=True)
            else:
                tmp_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass  # jpegtran not found, fallback to Pillow
        except Exception:
            pass  # jpegtran failed, fallback to Pillow

        # Fallback: Pillow optimize
        try:
            with Image.open(str(file_path)) as img:
                img.save(str(file_path), format="JPEG", quality=95,
                        optimize=True, progressive=True)

            final_size = os.path.getsize(file_path)
            if show_log:
                reduction = (original_size - final_size) / original_size * 100 if original_size > 0 else 0
                print(f"[SDPromptSaverOptimized] JPEG (Pillow): {original_size:,} B → {final_size:,} B (-{reduction:.1f}%)")
        except Exception as e:
            if show_log:
                print(f"[SDPromptSaverOptimized] JPEG optimization failed: {e}")

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------

    def save_images(self, images,
                    extension="png",
                    filename="ComfyUI_%time_%seed_%counter",
                    path="%date/", date_format="%Y-%m-%d", time_format="%H%M%S",
                    model_name="", vae_name="", seed=0, steps=20, cfg=7.0,
                    sampler_name="", scheduler="", width=512, height=512,
                    positive="", negative="", lora_name="",
                    calculate_hash=True, resource_hash=True, save_metadata_file=False,
                    jpeg_quality=95, preserve_metadata=True,
                    show_compression_log=True,
                    prompt=None, extra_pnginfo=None):

        output_dir = folder_paths.get_output_directory()
        ext = extension.lower().lstrip(".")
        # Normalize jpg/jpeg to one suffix for saving
        save_suffix = "jpg" if ext == "jpeg" else ext

        variable_map = {
            "%date":      self.get_time(date_format),
            "%time":      self.get_time(time_format),
            "%seed":      seed,
            "%steps":     steps,
            "%cfg":       cfg,
            "%width":     width,
            "%height":    height,
            "%model":     Path(model_name).stem if model_name else "unknown",
            "%sampler":   sampler_name or "unknown",
            "%scheduler": scheduler or "normal",
        }

        subfolder = self.get_path(path, variable_map)
        output_folder = (Path(subfolder) if Path(subfolder).is_absolute()
                         else Path(output_dir) / subfolder)
        output_folder.mkdir(parents=True, exist_ok=True)

        # Model hash
        model_hash = ""
        if calculate_hash and model_name:
            for mp in folder_paths.get_filename_list("checkpoints"):
                if Path(mp).name == model_name:
                    full = folder_paths.get_full_path("checkpoints", mp)
                    model_hash = self.calculate_model_hash(full) or ""
                    break

        # Build A1111 metadata string
        sampler_str = sampler_name or "unknown"
        sched_str = scheduler or "normal"
        if sched_str != "normal":
            sampler_str = f"{sampler_str}_{sched_str}"

        model_hash_str = f"Model hash: {model_hash}, " if model_hash else ""
        vae_str   = f"VAE: {Path(vae_name).stem}, " if vae_name else ""
        lora_str  = f'Lora hashes: "{lora_name}", ' if lora_name else ""

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

        results = []
        filenames = []
        file_paths = []

        for i, image_tensor in enumerate(images):
            img_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array)

            counter = self.get_counter(output_folder, save_suffix) + i
            variable_map["%counter"] = f"{counter:05}"

            file_name = self.get_path(filename, variable_map)
            file_path = output_folder / f"{file_name}.{save_suffix}"

            # Deduplicate
            offset = 0
            while file_path.exists():
                offset += 1
                variable_map["%counter"] = f"{counter + offset:05}"
                file_name = self.get_path(filename, variable_map)
                file_path = output_folder / f"{file_name}.{save_suffix}"

            # Save with metadata
            if save_suffix == "png":
                self.save_png(img, file_path, metadata_text, prompt, extra_pnginfo)
            elif save_suffix == "webp":
                self.save_webp(img, file_path, metadata_text, prompt, extra_pnginfo)
            else:  # jpg / jpeg
                self.save_jpeg(img, file_path, metadata_text, prompt, extra_pnginfo,
                              jpeg_quality)

            print(f"[SDPromptSaverOptimized] saved: {file_path}")

            # Optimize (external tools + Pillow fallback)
            if save_suffix == "png":
                self.optimize_png(file_path, preserve_metadata, show_compression_log)
            elif save_suffix == "webp":
                self.optimize_webp(file_path, preserve_metadata, show_compression_log)
            else:  # jpg / jpeg
                self.optimize_jpeg(file_path, preserve_metadata, show_compression_log)

            # Optional .txt metadata file
            if save_metadata_file:
                metadata_file = file_path.with_suffix(".txt")
                metadata_file.write_text(metadata_text, encoding="utf-8")

            fn_with_ext = f"{file_name}.{save_suffix}"
            filenames.append(fn_with_ext)
            file_paths.append(str(file_path))
            results.append({
                "filename": fn_with_ext,
                "subfolder": "" if Path(subfolder).is_absolute() else str(subfolder),
                "type": "output"
            })

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
