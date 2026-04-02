"""
LoRA Tag Power Loader Extended for ComfyUI
Based on LoRA Tag Power Loader with added second_text input/output.
Original functionality preserved - only adds second_text field.

Tag Format:
    <lora:name:weight>              - Model weight (CLIP uses default_weight)
    <lora:name:high:low>            - Dual noise model weights (CLIP uses default_weight)
    <lora:name:high:low:clip>       - Full control: dual noise + explicit CLIP weight

Author: Extended from LoRA Tag Power Loader
License: MIT
"""

import re
import json
import folder_paths
import comfy.sd
import comfy.utils
from pathlib import Path
from inspect import cleandoc

# Try to import safetensors for metadata extraction
try:
    from safetensors import safe_open
    SAFETENSORS_AVAILABLE = True
except ImportError:
    SAFETENSORS_AVAILABLE = False
    print("[LoraTagPowerLoaderExtended] safetensors not available - trigger word extraction disabled")


class LoraTagPowerLoaderExtended:
    """
    Extended LoRA Tag Power Loader with second_text support.
    All original functionality preserved - only adds second_text input/output.
    """

    def __init__(self):
        self.loaded_loras = {}  # Cache for loaded LoRA files
        self.tag_pattern = r"<lora:([^>]+)>"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                    "tooltip": "Text containing LoRA tags like <lora:name:weight>. Tags are removed from output (or replaced with trigger words if auto_trigger is ON). Supports: <lora:name:weight>, <lora:name:high:low>, <lora:name:high:low:clip>."
                }),
                "second_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Additional text output - passed through unchanged."
                }),
                "model": ("MODEL", {
                    "tooltip": "The model to apply LoRAs to."
                }),
                "noise_mode": ([
                    "high_noise",
                    "low_noise",
                    "auto"
                ], {
                    "default": "auto",
                    "tooltip": "Which noise weights to use: high_noise for high noise pass, low_noise for low noise pass, auto averages both. For WanVideo dual loading, use two nodes with different modes."
                }),
            },
            "optional": {
                "clip": ("CLIP", {
                    "tooltip": "CLIP to apply LoRAs to. Optional - if not provided, only model LoRAs will be applied."
                }),
                "default_weight": ("FLOAT", {
                    "default": 1.0,
                    "min": -10.0,
                    "max": 10.0,
                    "step": 0.01,
                    "tooltip": "Default weight for CLIP and for tags without weights. Model weights are set explicitly in tags."
                }),
                "weight_multiplier": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.01,
                    "tooltip": "Global multiplier for ALL LoRA weights. 2.0 doubles all weights, 0.5 halves them. Applied after individual tag weights."
                }),
                "video_model_mode": ("BOOLEAN", {
                    "default": False,
                    "label_on": "WanVideo/Hunyuan",
                    "label_off": "Standard",
                    "tooltip": "Enable LoRA key standardization for WanVideo/Hunyuan models. Turn ON when using video models."
                }),
                "auto_trigger": ("BOOLEAN", {
                    "default": False,
                    "label_on": "Auto-inject triggers",
                    "label_off": "No triggers",
                    "tooltip": "Extract trigger words from LoRA metadata and insert them where the tag was. Supports Civitai, Kohya, AI Toolkit, SimpleTuner, OneTrainer. Prevents LoRA tags from appearing as artifacts in images."
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "text", "second_text", "lora_info", "trigger_words")
    OUTPUT_TOOLTIPS = (
        "The model with LoRAs applied",
        "The CLIP with LoRAs applied (if CLIP input was provided)",
        "The input text with LoRA tags removed (or replaced with trigger words if auto_trigger is ON)",
        "The second_text passed through unchanged",
        "Formatted list of loaded LoRAs with their weights, triggers, and any errors",
        "Comma-separated list of all trigger words extracted from loaded LoRAs"
    )
    FUNCTION = "load_loras_from_tags"
    CATEGORY = "Same Nodes/LoRA"
    DESCRIPTION = "LoRA Tag Power Loader with second_text support"

    def parse_lora_tag(self, tag_content, default_weight):
        """Parse LoRA tag with hybrid format."""
        parts = [p.strip() for p in tag_content.split(':')]

        if len(parts) < 1 or not parts[0]:
            return None

        result = {
            'name': parts[0],
            'high_noise': default_weight,
            'low_noise': default_weight,
            'clip': default_weight
        }

        try:
            if len(parts) == 2:
                weight = float(parts[1])
                result['high_noise'] = weight
                result['low_noise'] = weight
                result['clip'] = default_weight

            elif len(parts) == 3:
                result['high_noise'] = float(parts[1])
                result['low_noise'] = float(parts[2])
                result['clip'] = default_weight

            elif len(parts) >= 4:
                result['high_noise'] = float(parts[1])
                result['low_noise'] = float(parts[2])
                result['clip'] = float(parts[3])

        except (ValueError, IndexError) as e:
            print(f"[LoraTagPowerLoaderExtended] Error parsing tag '{tag_content}': {e}")
            return None

        return result

    def find_lora_file(self, name):
        """Find LoRA file by name with flexible matching."""
        lora_files = folder_paths.get_filename_list("loras")

        for lora_file in lora_files:
            if lora_file == name:
                return lora_file
            if Path(lora_file).stem == name:
                return lora_file

        for lora_file in lora_files:
            file_name = Path(lora_file).name
            if file_name.startswith(name) or lora_file.startswith(name):
                return lora_file

        name_lower = name.lower()
        for lora_file in lora_files:
            if Path(lora_file).stem.lower() == name_lower:
                return lora_file

        return None

    def extract_trigger_words(self, lora_path):
        """Extract trigger words from LoRA file metadata."""
        if not SAFETENSORS_AVAILABLE:
            return []

        if not lora_path or not lora_path.endswith('.safetensors'):
            return []

        triggers = []

        try:
            with safe_open(lora_path, framework="pt") as f:
                metadata = f.metadata()

            if not metadata:
                return []

            if 'modelspec.trigger_phrase' in metadata:
                phrase = metadata['modelspec.trigger_phrase'].strip()
                if phrase:
                    triggers.extend([t.strip() for t in phrase.split(',') if t.strip()])

            if 'trigger_word' in metadata:
                word = metadata['trigger_word'].strip()
                if word and word not in triggers:
                    triggers.append(word)

            if 'activation_text' in metadata:
                text = metadata['activation_text'].strip()
                if text and text not in triggers:
                    triggers.extend([t.strip() for t in text.split(',') if t.strip() and t.strip() not in triggers])

            if 'ss_tag_frequency' in metadata and not triggers:
                try:
                    tag_freq_str = metadata['ss_tag_frequency']
                    tag_freq = json.loads(tag_freq_str)

                    all_tags = []
                    for dataset_name, tags in tag_freq.items():
                        if isinstance(tags, dict):
                            for tag, count in tags.items():
                                skip_tags = {'1girl', '1boy', 'solo', 'simple background', 'white background',
                                           'looking at viewer', 'upper body', 'portrait', 'highres', 'absurdres'}
                                if tag.lower() not in skip_tags:
                                    all_tags.append((tag, count))

                    all_tags.sort(key=lambda x: x[1], reverse=True)
                    top_tags = [tag for tag, count in all_tags[:3]]
                    triggers.extend(top_tags)

                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    print(f"[LoraTagPowerLoaderExtended] Error parsing ss_tag_frequency: {e}")

            if 'ss_training_comment' in metadata and not triggers:
                comment = metadata['ss_training_comment'].strip()
                trigger_match = re.search(r'trigger\s*(?:word)?[:\s]+([^\n,]+)', comment, re.IGNORECASE)
                if trigger_match:
                    word = trigger_match.group(1).strip()
                    if word:
                        triggers.append(word)

        except Exception as e:
            print(f"[LoraTagPowerLoaderExtended] Error reading LoRA metadata from {lora_path}: {e}")

        return triggers

    def standardize_video_lora_keys(self, lora_data):
        """Standardize LoRA keys for WanVideo/Hunyuan models."""
        try:
            import sys
            import os

            wrapper_path = os.path.join(
                folder_paths.base_path,
                "custom_nodes",
                "ComfyUI-WanVideoWrapper"
            )

            if os.path.exists(wrapper_path) and wrapper_path not in sys.path:
                sys.path.insert(0, wrapper_path)

            from nodes_model_loading import standardize_lora_key_format
            return standardize_lora_key_format(lora_data)

        except ImportError:
            print("[LoraTagPowerLoaderExtended] WanVideoWrapper not found, using standard LoRA format")
            return lora_data
        except Exception as e:
            print(f"[LoraTagPowerLoaderExtended] Error standardizing keys: {e}")
            return lora_data

    def load_loras_from_tags(
        self,
        text,
        second_text,
        model,
        noise_mode,
        clip=None,
        default_weight=1.0,
        weight_multiplier=1.0,
        video_model_mode=False,
        auto_trigger=False
    ):
        """Main function: Parse text, extract LoRA tags, apply LoRAs."""

        matches = list(re.finditer(self.tag_pattern, text))
        lora_tags = [match.group(1) for match in matches]

        if not lora_tags:
            return (model, clip, text, second_text, "No LoRAs detected", "")

        model_lora = model
        clip_lora = clip
        lora_list = []
        seen_loras = set()
        all_trigger_words = []
        tag_replacements = {}

        print(f"\n[LoraTagPowerLoaderExtended] Found {len(lora_tags)} LoRA tag(s)")
        print(f"[LoraTagPowerLoaderExtended] Noise mode: {noise_mode}")
        print(f"[LoraTagPowerLoaderExtended] Weight multiplier: {weight_multiplier}x")
        print(f"[LoraTagPowerLoaderExtended] Video model mode: {video_model_mode}")
        print(f"[LoraTagPowerLoaderExtended] Auto-trigger: {auto_trigger}")

        for i, (match, tag_content) in enumerate(zip(matches, lora_tags), 1):
            lora_info = self.parse_lora_tag(tag_content, default_weight)
            tag_replacements[match.group(0)] = ""

            if lora_info and lora_info['name']:
                lora_name_lower = lora_info['name'].lower()
                if lora_name_lower in seen_loras:
                    msg = f"⊘ Tag {i}: Skipped duplicate '{lora_info['name']}' (already loaded)"
                    print(f"[LoraTagPowerLoaderExtended] {msg}")
                    lora_list.append(msg)
                    continue
                seen_loras.add(lora_name_lower)

            if not lora_info or not lora_info['name']:
                msg = f"❌ Tag {i}: Invalid format '<lora:{tag_content}>'"
                print(f"[LoraTagPowerLoaderExtended] {msg}")
                lora_list.append(msg)
                continue

            lora_file = self.find_lora_file(lora_info['name'])

            if not lora_file:
                msg = f"❌ Tag {i}: '{lora_info['name']}' not found"
                print(f"[LoraTagPowerLoaderExtended] {msg}")
                lora_list.append(msg)
                continue

            if noise_mode == "high_noise":
                model_strength = lora_info['high_noise']
                clip_strength = lora_info['clip']
                mode_label = "HIGH"
            elif noise_mode == "low_noise":
                model_strength = lora_info['low_noise']
                clip_strength = lora_info['clip']
                mode_label = "LOW"
            else:
                model_strength = (lora_info['high_noise'] + lora_info['low_noise']) / 2.0
                clip_strength = lora_info['clip']
                mode_label = "AUTO"

            model_strength = model_strength * weight_multiplier
            clip_strength = clip_strength * weight_multiplier

            if clip_lora is None:
                if clip_strength != 0:
                    print(f"[LoraTagPowerLoaderExtended] Warning: Tag {i} has clip strength but no CLIP input provided")
                clip_strength = 0

            lora_path = folder_paths.get_full_path("loras", lora_file)

            if lora_path not in self.loaded_loras:
                try:
                    lora_data = comfy.utils.load_torch_file(lora_path, safe_load=True)
                    self.loaded_loras[lora_path] = lora_data
                    print(f"[LoraTagPowerLoaderExtended] Loaded LoRA file: {lora_file}")
                except Exception as e:
                    msg = f"❌ Tag {i}: Error loading '{lora_file}': {e}"
                    print(f"[LoraTagPowerLoaderExtended] {msg}")
                    lora_list.append(msg)
                    continue
            else:
                lora_data = self.loaded_loras[lora_path]

            trigger_words = self.extract_trigger_words(lora_path)
            triggers_str = ", ".join(trigger_words) if trigger_words else ""

            if auto_trigger and trigger_words:
                tag_replacements[match.group(0)] = triggers_str
                all_trigger_words.extend(trigger_words)
                print(f"[LoraTagPowerLoaderExtended] Extracted triggers for {lora_info['name']}: {triggers_str}")
            elif trigger_words:
                all_trigger_words.extend(trigger_words)

            if video_model_mode:
                lora_data = self.standardize_video_lora_keys(lora_data)

            if model_strength != 0 or clip_strength != 0:
                try:
                    model_lora, clip_lora = comfy.sd.load_lora_for_models(
                        model_lora,
                        clip_lora,
                        lora_data,
                        model_strength,
                        clip_strength
                    )

                    lora_info_str = (
                        f"✓ {i}. {lora_info['name']} "
                        f"[{mode_label}] "
                        f"M:{model_strength:.2f} C:{clip_strength:.2f}"
                    )

                    if noise_mode == "auto":
                        lora_info_str += f" (H:{lora_info['high_noise']:.2f} L:{lora_info['low_noise']:.2f})"

                    if triggers_str:
                        lora_info_str += f" | Triggers: \"{triggers_str}\""

                    lora_list.append(lora_info_str)
                    print(f"[LoraTagPowerLoaderExtended] {lora_info_str}")

                except Exception as e:
                    msg = f"❌ Tag {i}: Error applying '{lora_file}': {e}"
                    print(f"[LoraTagPowerLoaderExtended] {msg}")
                    lora_list.append(msg)
                    continue
            else:
                msg = f"⊘ Tag {i}: Skipped '{lora_info['name']}' (zero strength)"
                print(f"[LoraTagPowerLoaderExtended] {msg}")
                lora_list.append(msg)

        cleaned_text = text
        for tag, replacement in tag_replacements.items():
            cleaned_text = cleaned_text.replace(tag, replacement, 1)

        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        lora_list_output = "\n".join(lora_list) if lora_list else "No LoRAs loaded"

        unique_triggers = list(dict.fromkeys(all_trigger_words))
        trigger_words_output = ", ".join(unique_triggers) if unique_triggers else ""

        print(f"[LoraTagPowerLoaderExtended] Processing complete\n")

        return (model_lora, clip_lora, cleaned_text, second_text, lora_list_output, trigger_words_output)


# ComfyUI Node Registration
NODE_CLASS_MAPPINGS = {
    "LoraTagPowerLoaderExtended": LoraTagPowerLoaderExtended,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraTagPowerLoaderExtended": "LoRA Tag Power Loader Extended",
}
