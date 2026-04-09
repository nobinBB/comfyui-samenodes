"""
Images to PDF Node for ComfyUI
Converts multiple images to a single PDF file
"""

import os
from pathlib import Path
from PIL import Image
from datetime import datetime


class ImagesToPdf:
    """
    A node that converts images in a folder to a PDF file.
    Supports subfolder inclusion, sorting, and quality settings.
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
                "include_subfolders": ("BOOLEAN", {
                    "default": False
                }),
                "sort_by_filename": ("BOOLEAN", {
                    "default": True
                }),
                "quality": (["高画質(大きい)", "標準", "低画質(小さい)"], {
                    "default": "高画質(大きい)"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "pdf_path")
    FUNCTION = "convert_to_pdf"
    CATEGORY = "image/pdf"
    OUTPUT_NODE = True

    def get_quality_settings(self, quality):
        """
        Get quality settings based on quality selection

        Returns:
            dict with quality and optimize settings
        """
        if quality == "高画質(大きい)":
            return {"quality": 95, "optimize": False}
        elif quality == "標準":
            return {"quality": 85, "optimize": True}
        else:  # 低画質(小さい)
            return {"quality": 75, "optimize": True}

    def convert_to_pdf(self, input_folder, output_folder, include_subfolders, sort_by_filename, quality):
        """
        Convert images in folder to PDF

        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            include_subfolders: Include images in subfolders
            sort_by_filename: Sort images by filename
            quality: Quality setting

        Returns:
            Tuple of (status, pdf_path)
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

            if include_subfolders:
                # Search recursively
                for ext in image_extensions:
                    image_files.extend(input_path.rglob(f'*{ext}'))
                    image_files.extend(input_path.rglob(f'*{ext.upper()}'))
            else:
                # Search only in current folder
                for ext in image_extensions:
                    image_files.extend(input_path.glob(f'*{ext}'))
                    image_files.extend(input_path.glob(f'*{ext.upper()}'))

            if not image_files:
                return ("", f"No image files found in: {input_folder}")

            # Sort by filename if requested
            if sort_by_filename:
                image_files = sorted(image_files, key=lambda x: x.name)

            print(f"\n{'='*60}")
            print(f"Images to PDF Converter")
            print(f"Input folder: {input_folder}")
            print(f"Output folder: {output_folder}")
            print(f"Found {len(image_files)} images")
            print(f"Include subfolders: {include_subfolders}")
            print(f"Sort by filename: {sort_by_filename}")
            print(f"Quality: {quality}")
            print(f"{'='*60}\n")

            # Get quality settings
            quality_settings = self.get_quality_settings(quality)

            # Load and convert images
            images = []
            image_list = []

            for i, img_file in enumerate(image_files, 1):
                try:
                    print(f"[{i}/{len(image_files)}] Loading: {img_file.name}")
                    img = Image.open(img_file)

                    # Convert to RGB if necessary (PDF doesn't support RGBA)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode in ('RGBA', 'LA'):
                            rgb_img.paste(img, mask=img.split()[-1])
                        else:
                            rgb_img.paste(img)
                        img = rgb_img

                    image_list.append(img)

                except Exception as e:
                    print(f"  ✗ Error loading {img_file.name}: {e}")
                    continue

            if not image_list:
                return ("", "Error: No images could be loaded")

            # Generate PDF filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"images_{timestamp}.pdf"
            pdf_path = output_path / pdf_filename

            # Save as PDF
            print(f"\nGenerating PDF: {pdf_filename}")
            first_image = image_list[0]
            other_images = image_list[1:] if len(image_list) > 1 else []

            first_image.save(
                str(pdf_path),
                "PDF",
                save_all=True,
                append_images=other_images,
                quality=quality_settings["quality"],
                optimize=quality_settings["optimize"]
            )

            # Get PDF file size
            pdf_size = os.path.getsize(pdf_path)
            pdf_size_mb = pdf_size / (1024 * 1024)

            print(f"\n{'='*60}")
            print(f"✓ PDF created successfully!")
            print(f"Output: {pdf_path}")
            print(f"Pages: {len(image_list)}")
            print(f"File size: {pdf_size_mb:.2f} MB")
            print(f"{'='*60}\n")

            status = (
                f"✓ PDF created successfully\n"
                f"Pages: {len(image_list)}\n"
                f"File size: {pdf_size_mb:.2f} MB\n"
                f"Output: {pdf_filename}"
            )

            return (status, str(pdf_path))

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return (error_msg, "")


NODE_CLASS_MAPPINGS = {
    "ImagesToPdf": ImagesToPdf,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImagesToPdf": "Images to PDF",
}
