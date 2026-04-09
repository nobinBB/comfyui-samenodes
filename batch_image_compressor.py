"""
Batch Image Compressor Node for ComfyUI
Compresses images in a folder with configurable compression modes
"""

import os
from pathlib import Path
from PIL import Image


class BatchImageCompressor:
    """
    A node that compresses images in a folder.
    Supports PNG (lossless/quantize) and JPEG optimization.
    """

    @classmethod
    def INPUT_TYPES(cls):
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
                "png_mode": (["Lossless", "Quantize (60-80% reduction)"], {
                    "default": "Quantize (60-80% reduction)"
                }),
                "jpeg_quality": ("INT", {
                    "default": 85,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "summary")
    FUNCTION = "compress_images"
    CATEGORY = "image/batch"
    OUTPUT_NODE = True

    def get_file_size(self, file_path):
        """Get file size in bytes"""
        return os.path.getsize(file_path)

    def format_size(self, size_bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def compress_png(self, image, output_path, mode):
        """
        Compress PNG image

        Args:
            image: PIL Image object
            output_path: Output file path
            mode: Compression mode (Lossless or Quantize)
        """
        if mode == "Quantize (60-80% reduction)":
            # Convert to palette mode (256 colors) for significant size reduction
            if image.mode in ('RGBA', 'LA'):
                # Handle transparency
                alpha = image.split()[-1]
                image = image.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
                # Add back alpha channel
                image.putalpha(alpha)
            else:
                # No transparency
                image = image.convert('P', palette=Image.ADAPTIVE, colors=256)

            image.save(output_path, "PNG", optimize=True, compress_level=9)
        else:
            # Lossless compression
            image.save(output_path, "PNG", optimize=True, compress_level=9)

    def compress_jpeg(self, image, output_path, quality):
        """
        Compress JPEG image

        Args:
            image: PIL Image object
            output_path: Output file path
            quality: JPEG quality (1-100)
        """
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image

        image.save(output_path, "JPEG", quality=quality, optimize=True)

    def compress_images(self, input_folder, output_folder, png_mode, jpeg_quality):
        """
        Compress all images in input folder

        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            png_mode: PNG compression mode
            jpeg_quality: JPEG quality setting

        Returns:
            Tuple of (status, summary)
        """
        try:
            input_path = Path(input_folder)
            output_path = Path(output_folder)

            if not input_path.exists() or not input_path.is_dir():
                return ("", f"Error: Input folder does not exist: {input_folder}")

            # Create output folder if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)

            # Find all image files
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
            image_files = []
            for ext in image_extensions:
                image_files.extend(input_path.rglob(f'*{ext}'))
                image_files.extend(input_path.rglob(f'*{ext.upper()}'))

            if not image_files:
                return ("", f"No image files found in: {input_folder}")

            print(f"\n{'='*60}")
            print(f"Batch Image Compressor")
            print(f"Input folder: {input_folder}")
            print(f"Output folder: {output_folder}")
            print(f"Found {len(image_files)} images")
            print(f"PNG mode: {png_mode}")
            print(f"JPEG quality: {jpeg_quality}")
            print(f"{'='*60}\n")

            status_lines = []
            total_original_size = 0
            total_compressed_size = 0
            success_count = 0
            error_count = 0

            for i, img_file in enumerate(image_files, 1):
                try:
                    # Get relative path to preserve folder structure
                    rel_path = img_file.relative_to(input_path)
                    output_file = output_path / rel_path
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                    # Get original size
                    original_size = self.get_file_size(img_file)
                    total_original_size += original_size

                    # Open and compress image
                    with Image.open(img_file) as image:
                        ext = img_file.suffix.lower()

                        if ext == '.png':
                            self.compress_png(image, str(output_file), png_mode)
                        elif ext in ['.jpg', '.jpeg']:
                            self.compress_jpeg(image, str(output_file), jpeg_quality)
                        else:
                            # Other formats: save with optimization
                            image.save(str(output_file), optimize=True)

                    # Get compressed size
                    compressed_size = self.get_file_size(output_file)
                    total_compressed_size += compressed_size

                    # Calculate reduction
                    reduction = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0

                    status_line = (
                        f"[{i}/{len(image_files)}] {img_file.name}: "
                        f"{self.format_size(original_size)} → {self.format_size(compressed_size)} "
                        f"({reduction:.1f}% reduced)"
                    )
                    status_lines.append(status_line)
                    print(f"✓ {status_line}")
                    success_count += 1

                except Exception as e:
                    error_line = f"[{i}/{len(image_files)}] {img_file.name}: Error - {e}"
                    status_lines.append(f"✗ {error_line}")
                    print(f"✗ {error_line}")
                    error_count += 1

            # Calculate overall statistics
            total_reduction = (
                ((total_original_size - total_compressed_size) / total_original_size * 100)
                if total_original_size > 0 else 0
            )

            print(f"\n{'='*60}")
            print(f"Compression Complete!")
            print(f"Processed: {success_count}/{len(image_files)} images")
            print(f"Original size: {self.format_size(total_original_size)}")
            print(f"Compressed size: {self.format_size(total_compressed_size)}")
            print(f"Total reduction: {total_reduction:.1f}%")
            if error_count > 0:
                print(f"Errors: {error_count}")
            print(f"{'='*60}\n")

            status_output = '\n'.join(status_lines)
            summary_output = (
                f"Processed: {success_count}/{len(image_files)} images\n"
                f"Original: {self.format_size(total_original_size)}\n"
                f"Compressed: {self.format_size(total_compressed_size)}\n"
                f"Reduction: {total_reduction:.1f}%\n"
                f"Errors: {error_count}"
            )

            return (status_output, summary_output)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return ("", error_msg)


NODE_CLASS_MAPPINGS = {
    "BatchImageCompressor": BatchImageCompressor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchImageCompressor": "Batch Image Compressor",
}
