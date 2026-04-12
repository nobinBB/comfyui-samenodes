"""
Image Format Converter Node for ComfyUI
Converts image files from one format to another
"""

import os
from pathlib import Path
from PIL import Image


class ImageFormatConverter:
    """
    A node that converts image files from one format to another.
    Prevents converting to the same format (error if source == target).
    """

    @classmethod
    def INPUT_TYPES(cls):
        extensions = [".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"]
        return {
            "required": {
                "input_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "output_folder": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "source_extension": (extensions, {
                    "default": ".png"
                }),
                "target_extension": (extensions, {
                    "default": ".jpg"
                }),
            },
            "optional": {
                "quality": ("INT", {
                    "default": 85,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "include_subfolders": ("BOOLEAN", {
                    "default": False
                }),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("status", "file_count")
    FUNCTION = "convert_format"
    CATEGORY = "image/format"
    OUTPUT_NODE = True

    def convert_image(self, image, target_ext, quality):
        """
        Convert image to target format

        Args:
            image: PIL Image object
            target_ext: Target extension (e.g., ".jpg")
            quality: Quality setting (for JPEG/WebP)

        Returns:
            PIL Image object
        """
        target_format = target_ext.upper().replace('.', '')

        # Handle JPEG
        if target_format in ['JPG', 'JPEG']:
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    rgb_image.paste(image, mask=image.split()[-1])
                else:
                    rgb_image.paste(image)
                image = rgb_image
            return image, {'format': 'JPEG', 'quality': quality, 'optimize': True}

        # Handle WebP
        elif target_format == 'WEBP':
            return image, {'format': 'WEBP', 'quality': quality, 'method': 6}

        # Handle PNG
        elif target_format == 'PNG':
            return image, {'format': 'PNG', 'optimize': True, 'compress_level': 9}

        # Handle BMP
        elif target_format == 'BMP':
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1])
                image = rgb_image
            return image, {'format': 'BMP'}

        # Handle TIFF
        elif target_format == 'TIFF':
            return image, {'format': 'TIFF', 'compression': 'tiff_lzw'}

        else:
            return image, {'format': target_format}

    def convert_format(self, input_folder, output_folder, source_extension, target_extension, quality=85, include_subfolders=False):
        """
        Convert images from source extension to target extension

        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            source_extension: Source file extension
            target_extension: Target file extension
            quality: Quality setting (for JPEG/WebP)
            include_subfolders: Include subfolders

        Returns:
            Tuple of (status, file_count)
        """
        try:
            # Check if source and target extensions are the same
            if source_extension.lower() == target_extension.lower():
                error_msg = f"Error: Source and target extensions are the same ({source_extension}). Cannot convert to the same format."
                print(f"\n✗ {error_msg}\n")
                return (error_msg, 0)

            input_path = Path(input_folder)
            output_path = Path(output_folder)

            if not input_path.exists() or not input_path.is_dir():
                return (f"Error: Input folder does not exist: {input_folder}", 0)

            # Create output folder if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)

            # Find all files with source extension
            if include_subfolders:
                image_files = list(input_path.rglob(f'*{source_extension}'))
                image_files.extend(input_path.rglob(f'*{source_extension.upper()}'))
            else:
                image_files = list(input_path.glob(f'*{source_extension}'))
                image_files.extend(input_path.glob(f'*{source_extension.upper()}'))

            # Remove duplicates
            image_files = list(set(image_files))

            if not image_files:
                return (f"No files with extension {source_extension} found in: {input_folder}", 0)

            print(f"\n{'='*60}")
            print(f"Image Format Converter")
            print(f"Input folder: {input_folder}")
            print(f"Output folder: {output_folder}")
            print(f"Found {len(image_files)} files with {source_extension}")
            print(f"Converting: {source_extension} → {target_extension}")
            print(f"Quality: {quality}")
            print(f"Include subfolders: {include_subfolders}")
            print(f"{'='*60}\n")

            status_lines = []
            success_count = 0
            error_count = 0

            for i, img_file in enumerate(image_files, 1):
                try:
                    # Get relative path to preserve folder structure
                    if include_subfolders:
                        rel_path = img_file.relative_to(input_path)
                        output_file = output_path / rel_path.parent / f"{rel_path.stem}{target_extension}"
                    else:
                        output_file = output_path / f"{img_file.stem}{target_extension}"

                    output_file.parent.mkdir(parents=True, exist_ok=True)

                    # Open and convert image
                    with Image.open(img_file) as image:
                        converted_image, save_params = self.convert_image(image, target_extension, quality)
                        converted_image.save(str(output_file), **save_params)

                    # Get file sizes
                    original_size = os.path.getsize(img_file)
                    converted_size = os.path.getsize(output_file)
                    size_change = ((converted_size - original_size) / original_size * 100) if original_size > 0 else 0

                    status_line = (
                        f"[{i}/{len(image_files)}] {img_file.name} → {output_file.name} "
                        f"({size_change:+.1f}%)"
                    )
                    status_lines.append(status_line)
                    print(f"✓ {status_line}")
                    success_count += 1

                except Exception as e:
                    error_line = f"[{i}/{len(image_files)}] {img_file.name}: Error - {e}"
                    status_lines.append(f"✗ {error_line}")
                    print(f"✗ {error_line}")
                    error_count += 1

            print(f"\n{'='*60}")
            print(f"Conversion Complete!")
            print(f"Converted: {success_count}/{len(image_files)} files")
            if error_count > 0:
                print(f"Errors: {error_count}")
            print(f"{'='*60}\n")

            status_output = '\n'.join(status_lines)
            summary = f"Converted: {success_count}/{len(image_files)} files ({source_extension} → {target_extension})"
            if error_count > 0:
                summary += f"\nErrors: {error_count}"

            return (status_output + "\n\n" + summary, success_count)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return (error_msg, 0)


NODE_CLASS_MAPPINGS = {
    "ImageFormatConverter": ImageFormatConverter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageFormatConverter": "Image Format Converter",
}
