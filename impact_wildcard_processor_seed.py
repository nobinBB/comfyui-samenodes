"""
Impact Wildcard Processor with Seed Step N
Extended version of ImpactWildcardProcessor with seed management features
"""

import json
import random
import hashlib
from pathlib import Path

try:
    import sys

    current_dir = Path(__file__).parent
    custom_nodes_dir = current_dir.parent
    impact_pack_dir = custom_nodes_dir / "ComfyUI-Impact-Pack"

    if impact_pack_dir.exists():
        impact_modules = impact_pack_dir / "modules"
        if str(impact_modules) not in sys.path:
            sys.path.insert(0, str(impact_modules))

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


UINT64_MAX = 0xffffffffffffffff


def get_wildcard_list():
    try:
        if WILDCARDS_AVAILABLE and wildcards and hasattr(wildcards, "get_wildcard_list"):
            wildcard_list = wildcards.get_wildcard_list()
            if wildcard_list:
                return ["Select the Wildcard to add to the text"] + wildcard_list

        return ["Select the Wildcard to add to the text"]
    except Exception as e:
        print(f"[ImpactWildcardProcessorSeed] Error loading wildcard list: {e}")
        return ["Select the Wildcard to add to the text"]


class ImpactWildcardProcessorSeed:
    COUNTER_FILE = Path(__file__).parent / "wildcard_seed_counters.json"
    CACHE_FILE = Path(__file__).parent / "wildcard_seed_cache.json"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "wildcard_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "Enter a prompt using wildcard syntax.",
                    },
                ),
                "populated_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "Processed text is shown here. In fixed/reproduce mode this value is used as output.",
                    },
                ),
                "mode": (
                    ["populate", "fixed", "reproduce"],
                    {
                        "default": "populate",
                        "tooltip": (
                            "populate: process wildcard_text.\n"
                            "fixed: output populated_text without changing count.\n"
                            "reproduce: output populated_text once; frontend may switch back to populate."
                        ),
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": UINT64_MAX,
                        "tooltip": "Base seed for wildcard processing.",
                    },
                ),
                "seed_mode": (
                    ["random", "increment", "decrement"],
                    {
                        "default": "increment",
                        "tooltip": "How seed changes every divisor runs.",
                    },
                ),
                "divisor": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 1000,
                        "tooltip": "Number of populate runs to reuse the same wildcard result.",
                    },
                ),
                "increment_amount": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 10000,
                        "tooltip": "Seed step amount for increment/decrement mode.",
                    },
                ),
            },
            "optional": {
                "Select to add Wildcard": (
                    get_wildcard_list(),
                    {"default": "Select the Wildcard to add to the text"},
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed text",)
    FUNCTION = "process_wildcard"
    CATEGORY = "ImpactPack/Prompt"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def load_counters(self):
        if self.COUNTER_FILE.exists():
            try:
                with open(self.COUNTER_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ImpactWildcardProcessorSeed] Error loading counters: {e}")
                return {}
        return {}

    def save_counters(self, counters):
        try:
            with open(self.COUNTER_FILE, "w", encoding="utf-8") as f:
                json.dump(counters, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error saving counters: {e}")

    def load_cache(self):
        if self.CACHE_FILE.exists():
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ImpactWildcardProcessorSeed] Error loading cache: {e}")
                return {}
        return {}

    def save_cache(self, cache):
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error saving cache: {e}")

    def normalize_int(self, value, default=1, min_value=None, max_value=None):
        try:
            if isinstance(value, (list, tuple)):
                value = value[0] if value else default

            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    value = default

            value = int(float(value))
        except Exception:
            value = default

        if min_value is not None:
            value = max(min_value, value)

        if max_value is not None:
            value = min(max_value, value)

        return value

    def make_signature(
        self,
        wildcard_text,
        seed,
        seed_mode,
        divisor,
        increment_amount,
    ):
        payload = {
            "wildcard_text": wildcard_text,
            "seed": seed,
            "seed_mode": seed_mode,
            "divisor": divisor,
            "increment_amount": increment_amount,
        }

        raw = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()
        
    def calculate_seed_from_count(self, seed, divisor, increment_amount, seed_mode, count):
        seed_step = count // divisor

        if seed_mode == "random":
            rng = random.Random((seed + seed_step) & UINT64_MAX)
            return rng.randint(0, UINT64_MAX)

        if seed_mode == "increment":
            return (seed + (seed_step * increment_amount)) & UINT64_MAX

        if seed_mode == "decrement":
            return (seed - (seed_step * increment_amount)) & UINT64_MAX

        return seed & UINT64_MAX

    def process_text(self, text_to_process, calculated_seed):
        if WILDCARDS_AVAILABLE and wildcards:
            try:
                return wildcards.process(text_to_process, calculated_seed)
            except Exception as e:
                print(f"[ImpactWildcardProcessorSeed] Error processing wildcards: {e}")
                return text_to_process

        return self.simple_wildcard_process(text_to_process, calculated_seed)

    def process_wildcard(
        self,
        wildcard_text,
        populated_text,
        mode,
        seed,
        seed_mode,
        divisor,
        increment_amount,
        unique_id=None,
        **kwargs,
    ):
        if unique_id is None:
            unique_id = "default"

        counter_key = str(unique_id)

        seed = self.normalize_int(seed, default=0, min_value=0, max_value=UINT64_MAX)
        divisor = self.normalize_int(divisor, default=1, min_value=1, max_value=1000)
        increment_amount = self.normalize_int(
            increment_amount,
            default=1,
            min_value=1,
            max_value=10000,
        )

        counters = self.load_counters()
        cache = self.load_cache()

        counter_data = counters.get(counter_key, 0)

        if isinstance(counter_data, dict):
            count = self.normalize_int(counter_data.get("count", 0), default=0, min_value=0)
            old_signature = counter_data.get("signature")
        else:
            count = self.normalize_int(counter_data, default=0, min_value=0)
            old_signature = None

        signature = self.make_signature(
            wildcard_text,
            seed,
            seed_mode,
            divisor,
            increment_amount,
        )

        if old_signature != signature:
            count = 0
            if counter_key in cache:
                del cache[counter_key]
            old_cache_key = f"{counter_key}_result"
            if old_cache_key in cache:
                del cache[old_cache_key]
            print(f"[ImpactWildcardProcessorSeed] settings changed. reset count/cache for node {counter_key}")

        calculated_seed = self.calculate_seed_from_count(
            seed,
            divisor,
            increment_amount,
            seed_mode,
            count,
        )

        if mode == "fixed" or mode == "reproduce":
            result = populated_text
            new_count = count
            print(
                f"[ImpactWildcardProcessorSeed] node={counter_key} mode={mode} "
                f"count={count} divisor={divisor} seed={calculated_seed} action=fixed"
            )
        else:
            group_index = count // divisor
            cache_data = cache.get(counter_key, {})

            if not isinstance(cache_data, dict):
                cache_data = {}

            should_process = (
                cache_data.get("signature") != signature
                or cache_data.get("group_index") != group_index
                or "result" not in cache_data
            )

            if should_process:
                result = self.process_text(wildcard_text, calculated_seed)
                cache[counter_key] = {
                    "signature": signature,
                    "group_index": group_index,
                    "result": result,
                    "seed": calculated_seed,
                }
                action = "reroll"
            else:
                result = cache_data["result"]
                action = "cache"

            new_count = count + 1

            print(
                f"[ImpactWildcardProcessorSeed] node={counter_key} "
                f"count_before={count} count_after={new_count} "
                f"divisor={divisor} group={group_index} "
                f"seed={calculated_seed} action={action} result={result}"
            )

        counters[counter_key] = {
            "count": new_count,
            "signature": signature,
        }

        old_cache_key = f"{counter_key}_result"
        if old_cache_key in cache:
            del cache[old_cache_key]

        self.save_counters(counters)
        self.save_cache(cache)

        return {
            "ui": {
                "seed": [calculated_seed],
                "count": [new_count],
                "populated_text": [result],
            },
            "result": (result,),
        }

    def simple_wildcard_process(self, text, seed):
        import re

        rng = random.Random(seed)

        def replace_wildcard(match):
            options = match.group(1).split("|")
            return rng.choice(options)

        max_iterations = 100
        iteration = 0

        while "{" in text and "|" in text and iteration < max_iterations:
            text = re.sub(r"\{([^{}]+)\}", replace_wildcard, text)
            iteration += 1

        return text

    @classmethod
    def reset_counter(cls, unique_id):
        counter_key = str(unique_id)

        if cls.COUNTER_FILE.exists():
            try:
                with open(cls.COUNTER_FILE, "r", encoding="utf-8") as f:
                    counters = json.load(f)
            except Exception:
                counters = {}
        else:
            counters = {}

        counters[counter_key] = {
            "count": 0,
            "signature": None,
        }

        try:
            with open(cls.COUNTER_FILE, "w", encoding="utf-8") as f:
                json.dump(counters, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ImpactWildcardProcessorSeed] Error resetting counter: {e}")
            return False

        if cls.CACHE_FILE.exists():
            try:
                with open(cls.CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                cache = {}
        else:
            cache = {}

        if counter_key in cache:
            del cache[counter_key]

        old_cache_key = f"{counter_key}_result"
        if old_cache_key in cache:
            del cache[old_cache_key]

        try:
            with open(cls.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
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