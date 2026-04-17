"""
Impact Wildcard Processor with Seed Step N
Extended version of ImpactWildcardProcessor with seed management features
"""

import os
import json
import random
from pathlib import Path

# Try to import Impact Pack's wildcard module
try:
    import sys
    import importlib.util

    # Find ComfyUI's custom_nodes directory
    current_dir = Path(__file__).parent
    custom_nodes_dir = current_dir.parent
    impact_pack_dir = custom_nodes_dir / "ComfyUI-Impact-Pack"

    if impact_pack_dir.exists():
        # Add Impact Pack to Python path
        impact_modules = impact_pack_dir / "modules"
        if str(impact_modules) not in sys.path:
            sys.path.insert(0, str(impact_modules))

        # Import wildcards module
        import impact.wildcards as wildcards
        WILDCARDS_AVAILABLE = True
    else:
        WILDCARDS_AVAILABLE = False
        wildcards = None
except ImportError:
    WILDCARDS_AVAILABLE = False
    wildcards = None


class ImpactWildcardProcessorSeed:
    """
    Extended ImpactWildcardProcessor with Seed Step N functionality.
    Supports random, increment, and decrement seed modes.
    """

    # Counter file path
    COUNTER_FILE = Path(__file__).parent / "wildcard_seed_counters.json"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "wildcard_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": True
                }),
                "mode": (["populate", "fixed"],),
                "seed_mode": (["random", "increment", "decrement"],),
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
                    "min": 1,
                    "max": 10000
                }),
            },
            "optional": {
                "populated": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "forceInput": False
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process_wildcard"
    CATEGORY = "ImpactPack/Wildcard"
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
                print(f"[ImpactWildcardProcessorSeed] Error loading counters: {e}")
                return {}
        return {}

    def save_counters(self, counters):
        """Save counter state to JSON file"""
        try:
            with open(self.COUNTER_FILE, 'w') as f:
                json.dump(counters, f, indent=2)
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error saving counters: {e}")

    def calculate_seed(self, base_seed, divisor, increment_amount, seed_mode, unique_id):
        """
        Calculate seed based on mode and counter

        Args:
            base_seed: Base seed value
            divisor: How many executions before changing seed
            increment_amount: Amount to increment/decrement seed
            seed_mode: "random", "increment", or "decrement"
            unique_id: Unique identifier for this node instance

        Returns:
            Calculated seed value
        """
        if unique_id is None:
            unique_id = "default"

        counter_key = str(unique_id)

        # Load counters
        counters = self.load_counters()

        # Get current count for this node instance
        count = counters.get(counter_key, 0)

        # Calculate seed based on mode
        if seed_mode == "random":
            # Random mode: change seed every divisor steps
            # Same seed is used for divisor consecutive executions
            seed_step = count // divisor
            random.seed(base_seed + seed_step)
            seed = random.randint(0, 0xffffffffffffffff)
        elif seed_mode == "increment":
            # Increment mode: increase seed every divisor steps
            seed_increment = (count // divisor) * increment_amount
            seed = base_seed + seed_increment
        elif seed_mode == "decrement":
            # Decrement mode: decrease seed every divisor steps
            seed_decrement = (count // divisor) * increment_amount
            seed = base_seed - seed_decrement
        else:
            seed = base_seed

        # Print debug info
        print(f"\n{'='*60}")
        print(f"ImpactWildcardProcessorSeed (ID: {unique_id})")
        print(f"{'='*60}")
        print(f"Seed mode: {seed_mode}")
        print(f"Base seed: {base_seed}")
        print(f"Divisor: {divisor}")
        print(f"Increment amount: {increment_amount}")
        print(f"Current count: {count}")
        print(f"Calculated seed: {seed}")
        print(f"Next count will be: {count + 1}")
        print(f"{'='*60}\n")

        # Increment count
        counters[counter_key] = count + 1

        # Save counters
        self.save_counters(counters)

        return seed

    def process_wildcard(self, wildcard_text, mode, seed_mode, base_seed, divisor,
                        increment_amount, populated="", unique_id=None):
        """
        Process wildcard text with seed management

        Args:
            wildcard_text: Text containing wildcards
            mode: "populate" or "fixed"
            seed_mode: "random", "increment", or "decrement"
            base_seed: Base seed value
            divisor: How many executions before changing seed
            increment_amount: Amount to increment/decrement
            populated: Pre-populated text (for fixed mode)
            unique_id: Unique identifier for this node instance

        Returns:
            Tuple of (processed_text,)
        """
        # Calculate seed based on mode
        seed = self.calculate_seed(base_seed, divisor, increment_amount, seed_mode, unique_id)

        # Process based on mode
        if mode == "fixed":
            # Fixed mode: return populated text as-is
            result = populated if populated else wildcard_text
        else:
            # Populate mode: process wildcards
            if WILDCARDS_AVAILABLE and wildcards:
                try:
                    # Use Impact Pack's wildcard processor
                    result = wildcards.process(wildcard_text, seed)
                except Exception as e:
                    print(f"[ImpactWildcardProcessorSeed] Error processing wildcards: {e}")
                    result = wildcard_text
            else:
                # Fallback: simple wildcard processing
                result = self.simple_wildcard_process(wildcard_text, seed)

        return {
            "ui": {
                "seed": [seed],
                "count": [self.load_counters().get(str(unique_id) if unique_id else "default", 0)]
            },
            "result": (result,)
        }

    def simple_wildcard_process(self, text, seed):
        """
        Simple wildcard processing fallback (when Impact Pack not available)
        Supports basic {option1|option2|option3} syntax
        """
        import re

        random.seed(seed)

        # Process {a|b|c} style wildcards
        def replace_wildcard(match):
            options = match.group(1).split('|')
            return random.choice(options)

        # Keep processing until no more wildcards
        max_iterations = 100
        iteration = 0
        while '{' in text and '|' in text and iteration < max_iterations:
            # Find and replace innermost wildcards first
            text = re.sub(r'\{([^{}]+)\}', replace_wildcard, text)
            iteration += 1

        return text

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
            print(f"[ImpactWildcardProcessorSeed] Counter reset for node {unique_id}")
            return True
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error resetting counter: {e}")
            return False


NODE_CLASS_MAPPINGS = {
    "ImpactWildcardProcessorSeed": ImpactWildcardProcessorSeed,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImpactWildcardProcessorSeed": "Impact Wildcard Processor (Seed)",
}
