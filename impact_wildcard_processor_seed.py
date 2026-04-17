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
        WILDCARDS_DIR = impact_pack_dir / "wildcards"
    else:
        WILDCARDS_AVAILABLE = False
        wildcards = None
        WILDCARDS_DIR = None
except ImportError:
    WILDCARDS_AVAILABLE = False
    wildcards = None
    WILDCARDS_DIR = None


def get_wildcard_list():
    """Get list of available wildcard files including subfolders"""
    if not WILDCARDS_DIR or not WILDCARDS_DIR.exists():
        return ["Select the Wildcard to add to the text"]

    wildcard_list = ["Select the Wildcard to add to the text"]
    try:
        # Recursively get all .txt, .yaml, .yml files
        for file in sorted(WILDCARDS_DIR.rglob("*.*")):
            if file.suffix in [".txt", ".yaml", ".yml"]:
                # Get relative path from wildcards dir
                rel_path = file.relative_to(WILDCARDS_DIR)
                # Convert to wildcard format: subfolder/color.txt -> __subfolder/color__
                wildcard_name = f"__{rel_path.with_suffix('')}__"
                wildcard_list.append(wildcard_name)
    except Exception as e:
        print(f"[ImpactWildcardProcessorSeed] Error loading wildcard list: {e}")

    return wildcard_list


class ImpactWildcardProcessorSeed:
    """
    Extended ImpactWildcardProcessor with Seed Step N functionality.
    Supports random, increment, and decrement seed modes.
    Uses result caching to ensure same output for divisor consecutive executions.
    """

    # Counter file path
    COUNTER_FILE = Path(__file__).parent / "wildcard_seed_counters.json"
    # Cache file path for storing wildcard results
    CACHE_FILE = Path(__file__).parent / "wildcard_seed_cache.json"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "wildcard_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Enter a prompt using wildcard syntax."}),
                "populated_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "The actual value passed during the execution of 'ImpactWildcardProcessor' is what is shown here. The behavior varies slightly depending on the mode. Wildcard syntax can also be used in 'populated_text'."}),
                "mode": (["populate", "fixed", "reproduce"], {"default": "populate", "tooltip":
                    "populate: Before running the workflow, it overwrites the existing value of 'populated_text' with the prompt processed from 'wildcard_text'. In this mode, 'populated_text' cannot be edited.\n"
                    "fixed: Ignores wildcard_text and keeps 'populated_text' as is. You can edit 'populated_text' in this mode.\n"
                    "reproduce: This mode operates as 'fixed' mode only once for reproduction, and then it switches to 'populate' mode."
                    }),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Determines the random seed to be used for wildcard processing."}),
                "Select to add Wildcard": (get_wildcard_list(),),
                "seed_mode": (["random", "increment", "decrement"], {"default": "random"}),
                "divisor": ("INT", {"default": 1, "min": 1, "max": 1000}),
                "increment_amount": ("INT", {"default": 1, "min": 1, "max": 10000}),
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

    def load_cache(self):
        """Load cached results from JSON file"""
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ImpactWildcardProcessorSeed] Error loading cache: {e}")
                return {}
        return {}

    def save_cache(self, cache):
        """Save cached results to JSON file"""
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error saving cache: {e}")

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

        # Increment count
        counters[counter_key] = count + 1

        # Save counters
        self.save_counters(counters)

        return seed

    def process_wildcard(self, wildcard_text, populated_text, mode, seed, seed_mode, divisor,
                        increment_amount, unique_id=None, **kwargs):
        """
        Process wildcard text with seed management and result caching

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
        if unique_id is None:
            unique_id = "default"

        counter_key = str(unique_id)

        # Get current count
        counters = self.load_counters()
        count = counters.get(counter_key, 0)

        # Calculate seed based on mode
        calculated_seed = self.calculate_seed(seed, divisor, increment_amount, seed_mode, unique_id)

        # Get updated count after calculate_seed
        counters = self.load_counters()
        new_count = counters.get(counter_key, 0)

        # Process based on mode
        if mode == "fixed" or mode == "reproduce":
            # Fixed/Reproduce mode: return populated_text as-is
            result = populated_text if populated_text else wildcard_text
        else:
            # Populate mode: use caching system
            cache = self.load_cache()
            cache_key = f"{counter_key}_result"

            # Check if we should process wildcard (divisor boundary)
            should_process = (count % divisor) == 0

            if should_process:
                # Process wildcard and cache result
                text_to_process = populated_text if populated_text else wildcard_text
                if WILDCARDS_AVAILABLE and wildcards:
                    try:
                        # Use Impact Pack's wildcard processor
                        result = wildcards.process(text_to_process, calculated_seed)
                    except Exception as e:
                        print(f"[ImpactWildcardProcessorSeed] Error processing wildcards: {e}")
                        result = text_to_process
                else:
                    # Fallback: simple wildcard processing
                    result = self.simple_wildcard_process(text_to_process, calculated_seed)

                # Cache the result
                cache[cache_key] = result
                self.save_cache(cache)
            else:
                # Use cached result
                if cache_key in cache:
                    result = cache[cache_key]
                else:
                    # No cache available, process anyway
                    text_to_process = populated_text if populated_text else wildcard_text
                    if WILDCARDS_AVAILABLE and wildcards:
                        result = wildcards.process(text_to_process, calculated_seed)
                    else:
                        result = self.simple_wildcard_process(text_to_process, calculated_seed)
                    cache[cache_key] = result
                    self.save_cache(cache)

        return {
            "ui": {
                "seed": [calculated_seed],
                "count": [new_count]
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
        Reset counter and clear cache for specific node instance
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
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error resetting counter: {e}")
            return False

        # Clear cache
        if cls.CACHE_FILE.exists():
            try:
                with open(cls.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
            except Exception:
                cache = {}
        else:
            cache = {}

        # Remove cached result for this node
        cache_key = f"{counter_key}_result"
        if cache_key in cache:
            del cache[cache_key]

        # Save cache
        try:
            with open(cls.CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error clearing cache: {e}")
            return False

        print(f"[ImpactWildcardProcessorSeed] Counter and cache reset for node {unique_id}")
        return True


NODE_CLASS_MAPPINGS = {
    "ImpactWildcardProcessorSeed": ImpactWildcardProcessorSeed,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImpactWildcardProcessorSeed": "Impact Wildcard Processor (Seed)",
}
