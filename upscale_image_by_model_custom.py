"""
Upscale Image By (Using Model) Custom
Batch-compatible version of Upscale Image By node
Supports subdirectories processing from Batch Load Images (Mikey)
"""

import torch
import comfy.utils


class UpscaleImageByUsingModelCustom:
    """
    Custom upscale node that handles batch images from Batch Load Images (Mikey).
    Processes each image in the batch individually and returns as batch.
    """

    upscale_methods = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "upscale_model": ("UPSCALE_MODEL",),
                "images": ("IMAGE",),
                "upscale_by": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.1,
                    "max": 8.0,
                    "step": 0.1
                }),
                "rescale_method": (cls.upscale_methods,),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "upscale_batch"
    CATEGORY = "image/upscaling"

    def upscale_single_image(self, upscale_model, image, upscale_by, rescale_method):
        """
        Upscale a single image using the model and rescale if needed.

        Args:
            upscale_model: The upscaling model
            image: Single image tensor [H, W, C]
            upscale_by: Target upscale factor
            rescale_method: Method for rescaling

        Returns:
            Upscaled image tensor
        """
        # Add batch dimension for processing [1, H, W, C]
        image = image.unsqueeze(0)

        # Get original dimensions
        samples = image.movedim(-1, 1)  # [1, C, H, W]
        orig_height = samples.shape[2]
        orig_width = samples.shape[3]

        # Calculate target dimensions
        target_height = int(orig_height * upscale_by)
        target_width = int(orig_width * upscale_by)

        # Apply upscale model
        upscaled = upscale_model.upscale(samples)

        # Get upscaled dimensions
        upscaled_height = upscaled.shape[2]
        upscaled_width = upscaled.shape[3]

        # Rescale if upscaled dimensions exceed target
        if upscaled_height > target_height or upscaled_width > target_width:
            upscaled = comfy.utils.common_upscale(
                upscaled,
                target_width,
                target_height,
                rescale_method,
                "disabled"
            )

        # Convert back to image format [1, H, W, C]
        upscaled = upscaled.movedim(1, -1)

        # Remove batch dimension [H, W, C]
        return upscaled.squeeze(0)

    def upscale_batch(self, upscale_model, images, upscale_by, rescale_method):
        """
        Upscale a batch of images.

        Args:
            upscale_model: The upscaling model
            images: Batch of images tensor [B, H, W, C]
            upscale_by: Target upscale factor
            rescale_method: Method for rescaling

        Returns:
            Tuple of (upscaled_images_batch,)
        """
        # Check if images is a batch
        if len(images.shape) != 4:
            raise ValueError(f"Expected 4D tensor [B, H, W, C], got shape {images.shape}")

        batch_size = images.shape[0]
        upscaled_images = []

        print(f"\n{'='*60}")
        print(f"Upscaling batch of {batch_size} images...")
        print(f"Upscale factor: {upscale_by}x")
        print(f"Rescale method: {rescale_method}")
        print(f"{'='*60}\n")

        # Process each image in the batch
        for i in range(batch_size):
            image = images[i]
            print(f"Processing image {i+1}/{batch_size}...")
            print(f"  Original size: {image.shape[1]}x{image.shape[0]}")

            upscaled = self.upscale_single_image(
                upscale_model,
                image,
                upscale_by,
                rescale_method
            )

            print(f"  Upscaled size: {upscaled.shape[1]}x{upscaled.shape[0]}")
            upscaled_images.append(upscaled)

        # Stack back into batch [B, H, W, C]
        result = torch.stack(upscaled_images, dim=0)

        print(f"\n{'='*60}")
        print(f"Batch upscaling complete!")
        print(f"Output batch shape: {result.shape}")
        print(f"{'='*60}\n")

        return (result,)


# Node class mappings
NODE_CLASS_MAPPINGS = {
    "UpscaleImageByUsingModelCustom": UpscaleImageByUsingModelCustom,
}

# Human-readable names
NODE_DISPLAY_NAME_MAPPINGS = {
    "UpscaleImageByUsingModelCustom": "Upscale Image By (Using Model) custom",
}
