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

        # Get wildcards directory
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
    """Get list of available wildcard files"""
    if not WILDCARDS_DIR or not WILDCARDS_DIR.exists():
        return ["Select the Wildcard to add to the text"]

    wildcard_list = ["Select the Wildcard to add to the text"]
    try:
        for file in sorted(WILDCARDS_DIR.glob("*.txt")):
            # Convert filename to wildcard format: color.txt -> __color__
            wildcard_name = f"__{file.stem}__"
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
                "wildcard_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                    "tooltip": "Enter a prompt using wildcard syntax."
                }),
                "populated_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                    "tooltip": "The processed result is displayed here. In populate mode, this is read-only. In fixed mode, you can edit this directly."
                }),
                "mode": (["populate", "fixed", "reproduce"], {
                    "default": "populate",
                    "tooltip": "populate: Process wildcard_text and update populated_text\nfixed: Use populated_text as-is\nreproduce: Fixed mode once, then switch to populate"
                }),
                "seed_mode": (["random", "increment", "decrement"], {
                    "default": "random",
                    "tooltip": "random: Random seed every divisor steps\nincrement: Increase seed every divisor steps\ndecrement: Decrease seed every divisor steps"
                }),
                "base_seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Base seed value for wildcard processing."
                }),
                "divisor": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 1000,
                    "tooltip": "Number of executions before changing seed."
                }),
                "increment_amount": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10000,
                    "tooltip": "Amount to increment/decrement seed (not used in random mode)."
                }),
                "Select to add Wildcard": (get_wildcard_list(),),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed text",)
    FUNCTION = "process_wildcard"
    CATEGORY = "ImpactPack/Prompt"
    OUTPUT_NODE = True

    DESCRIPTION = (
        "Extended ImpactWildcardProcessor with Seed Step N functionality.\n\n"
        "Processes wildcard syntax with configurable seed behavior:\n"
        "- random mode: New random seed every divisor steps\n"
        "- increment mode: Increase seed every divisor steps\n"
        "- decrement mode: Decrease seed every divisor steps\n\n"
        "With divisor=4, the same wildcard result repeats 4 times before re-rolling."
    )

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

    def process_wildcard(self, wildcard_text, populated_text, mode, seed_mode, base_seed, divisor,
                        increment_amount, unique_id=None, **kwargs):
        """
        Process wildcard text with seed management and result caching

        Args:
            wildcard_text: Text containing wildcards (input prompt)
            populated_text: Processed result or fixed text
            mode: "populate", "fixed", or "reproduce"
            seed_mode: "random", "increment", or "decrement"
            base_seed: Base seed value
            divisor: How many executions before changing seed
            increment_amount: Amount to increment/decrement
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
        seed = self.calculate_seed(base_seed, divisor, increment_amount, seed_mode, unique_id)

        # Get updated count after calculate_seed
        counters = self.load_counters()
        new_count = counters.get(counter_key, 0)

        # Process based on mode
        if mode == "fixed" or mode == "reproduce":
            # Fixed/Reproduce mode: use populated_text as-is
            result = populated_text
        else:
            # Populate mode: use caching system
            cache = self.load_cache()
            cache_key = f"{counter_key}_result"

            # Check if we should process wildcard (divisor boundary)
            should_process = (count % divisor) == 0

            if should_process:
                # Process wildcard and cache result
                # Note: In Impact Pack, populated_text is used for processing
                # UI automatically updates populated_text from wildcard_text in populate mode
                text_to_process = populated_text if populated_text else wildcard_text

                if WILDCARDS_AVAILABLE and wildcards:
                    try:
                        # Use Impact Pack's wildcard processor
                        result = wildcards.process(text_to_process, seed)
                    except Exception as e:
                        print(f"[ImpactWildcardProcessorSeed] Error processing wildcards: {e}")
                        result = text_to_process
                else:
                    # Fallback: simple wildcard processing
                    result = self.simple_wildcard_process(text_to_process, seed)

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
                        result = wildcards.process(text_to_process, seed)
                    else:
                        result = self.simple_wildcard_process(text_to_process, seed)
                    cache[cache_key] = result
                    self.save_cache(cache)

        return {
            "ui": {
                "seed": [seed],
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
