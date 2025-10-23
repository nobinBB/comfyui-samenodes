"""
Batch Image Processor Node for ComfyUI
Processes images from a folder one by one to minimize memory usage
"""

import os
import torch
import numpy as np
from pathlib import Path
from PIL import Image
import folder_paths


class BatchImageProcessor:
    """
    A node that processes images from a folder in batches of 1 to minimize memory usage.
    Supports subfolder inclusion, sorting, and optional upscaling.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Batch settings
                "folder_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "include_subfolders": ("BOOLEAN", {
                    "default": False
                }),
                "start_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "step": 1
                }),
                "sort_method": (["name", "date_modified", "size"], {
                    "default": "name"
                }),

                # Output settings
                "output_folder": ("STRING", {
                    "default": "output",
                    "multiline": False
                }),
                "filename_prefix": ("STRING", {
                    "default": "processed_",
                    "multiline": False
                }),
            },
            "optional": {
                # Processing model (for flexibility)
                "upscale_model": ("UPSCALE_MODEL",),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("status", "processed_count")
    FUNCTION = "batch_process"
    CATEGORY = "image/batch"

    def get_sorted_images(self, folder_path, include_subfolders, sort_method):
        """
        Get sorted list of image files from folder

        Args:
            folder_path: Path to folder containing images
            include_subfolders: Whether to include subfolders
            sort_method: Method to sort images ("name", "date_modified", "size")

        Returns:
            List of Path objects for image files
        """
        # Supported image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif'}

        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        # Collect image files
        if include_subfolders:
            image_files = [
                f for f in folder.rglob('*')
                if f.is_file() and f.suffix.lower() in image_extensions
            ]
        else:
            image_files = [
                f for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() in image_extensions
            ]

        # Sort images
        if sort_method == "name":
            image_files.sort(key=lambda x: x.name)
        elif sort_method == "date_modified":
            image_files.sort(key=lambda x: x.stat().st_mtime)
        elif sort_method == "size":
            image_files.sort(key=lambda x: x.stat().st_size)

        return image_files

    def load_image(self, image_path):
        """
        Load image from path and convert to ComfyUI format

        Args:
            image_path: Path to image file

        Returns:
            torch.Tensor in shape [1, H, W, C] with values in range [0, 1]
        """
        img = Image.open(image_path)

        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to numpy array
        img_np = np.array(img).astype(np.float32) / 255.0

        # Convert to torch tensor and add batch dimension
        img_tensor = torch.from_numpy(img_np)[None,]

        return img_tensor

    def save_image(self, image_tensor, output_folder, filename):
        """
        Save image tensor to file

        Args:
            image_tensor: torch.Tensor in shape [1, H, W, C] with values in range [0, 1]
            output_folder: Folder to save image
            filename: Name of output file

        Returns:
            Path to saved image
        """
        # Create output folder if it doesn't exist
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        # Remove batch dimension and convert to numpy
        img_np = image_tensor.squeeze(0).cpu().numpy()

        # Convert from [0, 1] to [0, 255]
        img_np = (img_np * 255).clip(0, 255).astype(np.uint8)

        # Convert to PIL Image and save
        img_pil = Image.fromarray(img_np)
        save_path = output_path / filename
        img_pil.save(save_path)

        return save_path

    def apply_upscale(self, image_tensor, upscale_model):
        """
        Apply upscale model to image

        Args:
            image_tensor: torch.Tensor in shape [1, H, W, C]
            upscale_model: Upscale model from ComfyUI

        Returns:
            Upscaled image tensor
        """
        # ComfyUI upscale models expect [B, H, W, C] format
        # The model's upscale method should handle this
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Move to device
        image_tensor = image_tensor.to(device)

        # Apply upscale
        # Note: Different upscale models may have different interfaces
        # This is a common pattern, but may need adjustment
        upscaled = upscale_model.upscale(image_tensor)

        return upscaled

    def batch_process(self, folder_path, include_subfolders, start_index,
                      sort_method, output_folder, filename_prefix,
                      upscale_model=None):
        """
        Process images from folder one by one

        Args:
            folder_path: Path to folder containing images
            include_subfolders: Whether to include subfolders
            start_index: Index to start processing from
            sort_method: Method to sort images
            output_folder: Folder to save processed images
            filename_prefix: Prefix for output filenames
            upscale_model: Optional upscale model to apply

        Returns:
            Tuple of (status_message, processed_count)
        """
        try:
            # Get sorted image list
            image_files = self.get_sorted_images(folder_path, include_subfolders, sort_method)
            total = len(image_files)

            if total == 0:
                return ("No images found in folder", 0)

            if start_index >= total:
                return (f"Start index {start_index} is beyond total images {total}", 0)

            processed_count = 0
            errors = []

            print(f"\n{'='*60}")
            print(f"Starting batch processing...")
            print(f"Total images: {total}")
            print(f"Starting from index: {start_index}")
            print(f"Output folder: {output_folder}")
            print(f"{'='*60}\n")

            # Process images one by one from start_index
            for i, img_path in enumerate(image_files[start_index:], start=start_index):
                try:
                    # Load image
                    print(f"[{i+1}/{total}] Loading: {img_path.name}")
                    image = self.load_image(img_path)

                    # Apply upscale if model provided
                    if upscale_model is not None:
                        print(f"[{i+1}/{total}] Upscaling...")
                        image = self.apply_upscale(image, upscale_model)

                    # Generate output filename
                    output_filename = f"{filename_prefix}{i:04d}.png"

                    # Save image
                    print(f"[{i+1}/{total}] Saving: {output_filename}")
                    output_path = self.save_image(image, output_folder, output_filename)

                    # Free memory
                    del image
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    processed_count += 1
                    print(f"[{i+1}/{total}] ✓ Completed\n")

                except Exception as e:
                    error_msg = f"Error processing {img_path.name}: {str(e)}"
                    print(f"[{i+1}/{total}] ✗ {error_msg}\n")
                    errors.append(error_msg)
                    continue

            # Generate status message
            print(f"\n{'='*60}")
            print(f"Batch processing completed!")
            print(f"Successfully processed: {processed_count}/{total-start_index}")
            if errors:
                print(f"Errors: {len(errors)}")
                for error in errors:
                    print(f"  - {error}")
            print(f"{'='*60}\n")

            status = f"Completed: {processed_count}/{total-start_index} images processed"
            if errors:
                status += f" ({len(errors)} errors)"

            return (status, processed_count)

        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            print(f"\n✗ {error_msg}\n")
            return (error_msg, 0)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "BatchImageProcessor": BatchImageProcessor,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchImageProcessor": "Batch Image Processor",
}
