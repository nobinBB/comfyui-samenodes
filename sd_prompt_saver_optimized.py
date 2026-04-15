"""
SD Prompt Saver Optimized Node for ComfyUI
Saves images with A1111-compatible metadata and lossless compression

Based on: https://github.com/receyuki/comfyui-prompt-reader-node
License: MIT (original project)

Supported formats and compression tools:
  PNG  -> oxipng (lossless, 20-45% reduction)
  WebP -> lossless WebP via cwebp or Pillow (20-40% reduction)
  JPEG -> jpegtran or jpegoptim (lossless optimization, 3-15% reduction)
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
                "optimization_level": ("INT", {
                    "default": 4,
                    "min": 0,
                    "max": 6,
                    "step": 1
                }),
                "use_zopfli": ("BOOLEAN", {
                    "default": False,
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
        pnginfo = PngInfo()
        pnginfo.add_text("parameters", metadata_text)
        if prompt is not None:
            pnginfo.add_text("prompt", json.dumps(prompt))
        if extra_pnginfo is not None:
            for key in extra_pnginfo:
                pnginfo.add_text(key, json.dumps(extra_pnginfo[key]))
        img.save(str(file_path), pnginfo=pnginfo, compress_level=4)

    def save_webp(self, img: Image.Image, file_path: Path, metadata_text: str,
                  prompt, extra_pnginfo):
        exif_bytes = self._make_exif_bytes(metadata_text)
        save_kwargs = {
            "format": "WEBP",
            "lossless": True,
            "method": 6,
            "quality": 100,
        }
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        img.save(str(file_path), **save_kwargs)

    def save_jpeg(self, img: Image.Image, file_path: Path, metadata_text: str,
                  prompt, extra_pnginfo):
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
        save_kwargs = {"format": "JPEG", "quality": 95, "optimize": True}
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        img.save(str(file_path), **save_kwargs)

    # ------------------------------------------------------------------
    # Lossless compression
    # ------------------------------------------------------------------

    def _log_size(self, label: str, original: int, optimized: int, show: bool):
        if not show:
            return
        if original > 0:
            reduction = (original - optimized) / original * 100
            print(f"[SDPromptSaverOptimized] {label}: {original:,} B → {optimized:,} B (-{reduction:.1f}%)")

    def optimize_png(self, file_path: Path, optimization_level: int,
                     use_zopfli: bool, preserve_metadata: bool,
                     show_log: bool) -> bool:
        """oxipng – lossless PNG compression (20-45%)"""
        try:
            original = os.path.getsize(file_path)
            cmd = ["oxipng", "-o", str(optimization_level)]
            if use_zopfli:
                cmd.append("-Z")
            if not preserve_metadata:
                cmd.extend(["--strip", "safe"])
            cmd.append(str(file_path))
            result = subprocess.run(cmd, check=False, capture_output=True,
                                    text=True, timeout=300)
            if result.returncode != 0 and result.stderr:
                print(f"[SDPromptSaverOptimized] oxipng warning: {result.stderr.strip()}")
            self._log_size("PNG (oxipng)", original, os.path.getsize(file_path), show_log)
            return True
        except FileNotFoundError:
            print("[SDPromptSaverOptimized] WARNING: oxipng not found.")
            print("  Windows: https://github.com/shssoichiro/oxipng/releases")
            print("  Mac:     brew install oxipng")
            print("  Linux:   cargo install oxipng")
            return False
        except Exception as e:
            print(f"[SDPromptSaverOptimized] oxipng error: {e}")
            return False

    def optimize_webp(self, file_path: Path, optimization_level: int,
                      preserve_metadata: bool, show_log: bool) -> bool:
        """
        cwebp lossless compression – lossless recompress WebP.
        Falls back to Pillow lossless re-save if cwebp is unavailable.
        optimization_level 0-6 maps to cwebp -z 0-9.
        """
        original = os.path.getsize(file_path)

        # cwebp path
        try:
            z_level = min(int(optimization_level * 1.5), 9)  # scale 0-6 → 0-9
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            cmd = ["cwebp", "-lossless", "-m", "6", "-z", str(z_level),
                   str(file_path), "-o", str(tmp_path)]
            if not preserve_metadata:
                cmd += ["-metadata", "none"]
            else:
                cmd += ["-metadata", "all"]

            result = subprocess.run(cmd, check=False, capture_output=True,
                                    text=True, timeout=300)
            if result.returncode == 0 and tmp_path.exists():
                tmp_size = tmp_path.stat().st_size
                if tmp_size < original:
                    tmp_path.replace(file_path)
                    self._log_size("WebP (cwebp)", original, tmp_size, show_log)
                    return True
                else:
                    tmp_path.unlink(missing_ok=True)
                    if show_log:
                        print(f"[SDPromptSaverOptimized] WebP: already optimal, skipping")
                    return True
            else:
                tmp_path.unlink(missing_ok=True)
                if result.stderr:
                    print(f"[SDPromptSaverOptimized] cwebp warning: {result.stderr.strip()}")

        except FileNotFoundError:
            print("[SDPromptSaverOptimized] INFO: cwebp not found, using Pillow lossless re-save.")
            print("  Windows: https://developers.google.com/speed/webp/download")
            print("  Mac:     brew install webp")
            print("  Linux:   apt install webp  or  dnf install libwebp-tools")

        except Exception as e:
            print(f"[SDPromptSaverOptimized] cwebp error: {e}")

        # Pillow fallback – lossless re-save (always safe, same pixel data)
        try:
            with Image.open(str(file_path)) as img:
                img.save(str(file_path), format="WEBP", lossless=True,
                         method=6, quality=100)
            new_size = os.path.getsize(file_path)
            self._log_size("WebP (Pillow lossless)", original, new_size, show_log)
            return True
        except Exception as e:
            print(f"[SDPromptSaverOptimized] WebP Pillow fallback error: {e}")
            return False

    def optimize_jpeg(self, file_path: Path, preserve_metadata: bool,
                      show_log: bool) -> bool:
        """
        jpegtran lossless JPEG optimization (Huffman re-encoding, 3-15%).
        Falls back to jpegoptim if jpegtran is not found.
        JPEG pixels are never modified – truly lossless.
        """
        original = os.path.getsize(file_path)

        # jpegtran
        try:
            copy_flag = "all" if preserve_metadata else "none"
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            cmd = ["jpegtran", "-optimize", "-progressive",
                   "-copy", copy_flag, "-outfile", str(tmp_path), str(file_path)]
            result = subprocess.run(cmd, check=False, capture_output=True,
                                    text=True, timeout=120)
            if result.returncode == 0 and tmp_path.exists():
                tmp_size = tmp_path.stat().st_size
                if tmp_size < original:
                    tmp_path.replace(file_path)
                    self._log_size("JPEG (jpegtran)", original, tmp_size, show_log)
                    return True
                else:
                    tmp_path.unlink(missing_ok=True)
                    if show_log:
                        print(f"[SDPromptSaverOptimized] JPEG: already optimal")
                    return True
            else:
                tmp_path.unlink(missing_ok=True)

        except FileNotFoundError:
            pass  # try jpegoptim next

        except Exception as e:
            print(f"[SDPromptSaverOptimized] jpegtran error: {e}")

        # jpegoptim fallback
        try:
            strip_flag = "--strip-none" if preserve_metadata else "--strip-all"
            cmd2 = ["jpegoptim", strip_flag, str(file_path)]
            subprocess.run(cmd2, check=False, capture_output=True, text=True, timeout=120)
            self._log_size("JPEG (jpegoptim)", original, os.path.getsize(file_path), show_log)
            return True

        except FileNotFoundError:
            print("[SDPromptSaverOptimized] WARNING: jpegtran / jpegoptim not found.")
            print("  Windows: https://jpegclub.org/jpegtran/")
            print("  Mac:     brew install jpeg-turbo  (includes jpegtran)")
            print("  Linux:   apt install libjpeg-turbo-progs  or  dnf install libjpeg*")
            return False

        except Exception as e:
            print(f"[SDPromptSaverOptimized] jpegoptim error: {e}")
            return False

    def optimize_image(self, file_path: Path, extension: str,
                       optimization_level: int, use_zopfli: bool,
                       preserve_metadata: bool, show_log: bool):
        """Dispatch to format-specific optimizer."""
        ext = extension.lower().lstrip(".")
        if ext == "png":
            self.optimize_png(file_path, optimization_level, use_zopfli,
                              preserve_metadata, show_log)
        elif ext == "webp":
            self.optimize_webp(file_path, optimization_level, preserve_metadata, show_log)
        elif ext in ("jpg", "jpeg"):
            self.optimize_jpeg(file_path, preserve_metadata, show_log)

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
                    optimization_level=4, use_zopfli=False, preserve_metadata=True,
                    show_compression_log=True, skip_optimization=False,
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
                self.save_jpeg(img, file_path, metadata_text, prompt, extra_pnginfo)

            print(f"[SDPromptSaverOptimized] saved: {file_path}")

            # Lossless optimization
            if not skip_optimization:
                self.optimize_image(file_path, save_suffix, optimization_level,
                                    use_zopfli, preserve_metadata, show_compression_log)

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
