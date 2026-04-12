"""
SeedStepN Node for ComfyUI
Increments seed by divisor steps with persistent counter per node instance
"""

import os
import json
from pathlib import Path


class SeedStepN:
    """
    A node that increments seed based on divisor steps.
    Each node instance maintains independent count state.
    """

    # Counter file path
    COUNTER_FILE = Path(__file__).parent / "seed_step_counters.json"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff
                }),
                "divisor": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000
                }),
                "increment_amount": ("INT", {
                    "default": 1,
                    "min": -10000,
                    "max": 10000
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seed",)
    FUNCTION = "calculate_seed"
    CATEGORY = "utils/seed"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Return NaN to bypass cache and ensure execution every time
        return float('nan')

    def load_counters(self):
        """Load counter state from JSON file"""
        if self.COUNTER_FILE.exists():
            try:
                with open(self.COUNTER_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading counters: {e}")
                return {}
        return {}

    def save_counters(self, counters):
        """Save counter state to JSON file"""
        try:
            with open(self.COUNTER_FILE, 'w') as f:
                json.dump(counters, f, indent=2)
        except Exception as e:
            print(f"Error saving counters: {e}")

    def calculate_seed(self, base_seed, divisor, increment_amount, unique_id=None):
        """
        Calculate seed based on counter and parameters

        Args:
            base_seed: Base seed value
            divisor: How many executions before incrementing seed
            increment_amount: Amount to increment seed
            unique_id: Unique identifier for this node instance

        Returns:
            Tuple of (seed,)
        """
        # Use unique_id as key for counter
        if unique_id is None:
            unique_id = "default"

        counter_key = str(unique_id)

        # Load counters
        counters = self.load_counters()

        # Get current count for this node instance
        count = counters.get(counter_key, 0)

        # Calculate seed
        # seed = base_seed + (count // divisor) * increment_amount
        seed_increment = (count // divisor) * increment_amount
        seed = base_seed + seed_increment

        # Print debug info
        print(f"\n{'='*60}")
        print(f"SeedStepN (ID: {unique_id})")
        print(f"{'='*60}")
        print(f"Base seed: {base_seed}")
        print(f"Divisor: {divisor}")
        print(f"Increment amount: {increment_amount}")
        print(f"Current count: {count}")
        print(f"Calculated seed: {seed}")
        print(f"Next count will be: {count + 1}")
        next_seed = base_seed + ((count + 1) // divisor) * increment_amount
        print(f"Next seed will be: {next_seed}")
        print(f"{'='*60}\n")

        # Increment count
        counters[counter_key] = count + 1

        # Save counters
        self.save_counters(counters)

        return (seed,)

    @classmethod
    def reset_counter(cls, unique_id):
        """
        Reset counter for specific node instance
        This is called from frontend via API
        """
        counter_key = str(unique_id)

        # Load counters
        if cls.COUNTER_FILE.exists():
            try:
                with open(cls.COUNTER_FILE, 'r') as f:
                    counters = json.load(f)
            except Exception:
                counters = {}
        else:
            counters = {}

        # Reset counter
        counters[counter_key] = 0

        # Save counters
        try:
            with open(cls.COUNTER_FILE, 'w') as f:
                json.dump(counters, f, indent=2)
            print(f"Counter reset for node {unique_id}")
            return True
        except Exception as e:
            print(f"Error resetting counter: {e}")
            return False


NODE_CLASS_MAPPINGS = {
    "SeedStepN": SeedStepN,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SeedStepN": "Seed Step N",
}
