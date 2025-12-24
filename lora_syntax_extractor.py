import json
import re
import os
from collections import OrderedDict
from PIL import Image

class LoRASyntaxExtractor:
    """
    Per-image LoRA tag extractor (batch-safe).
    Input: list of file paths
    Output: list of lora syntax strings aligned with input order
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("lora_syntax_per_image", "lora_count_per_image")
    FUNCTION = "extract"
    CATEGORY = "SameNodes/utils"

    INPUT_IS_LIST = True
    # ★ここが重要：出力をリストにする
    OUTPUT_IS_LIST = (True, True)

    TAG_A1111 = re.compile(r"<\s*lora:([^:>]+):([0-9]*\.?[0-9]+)(?::[^>]+)?>", re.IGNORECASE)
    TAG_SIMPLE = re.compile(r"<\s*([^:<>\s]+):([0-9]*\.?[0-9]+)\s*>")

    def extract(self, file_path, debug=False):
        paths = self._flatten_paths(file_path)

        if debug:
            print(f"[LoRASyntaxExtractor] flattened paths = {len(paths)}")
            for i, p in enumerate(paths):
                print(f"  [{i}] {p}")

        out_syntax = []
        out_count = []

        for fp in paths:
            fp = ("" if fp is None else str(fp)).strip().strip('"').strip("'")
            if not fp or not os.path.exists(fp):
                out_syntax.append("")
                out_count.append(0)
                continue

            meta = self._read_png_metadata(fp, debug=debug)
            if meta is None:
                out_syntax.append("")
                out_count.append(0)
                continue

            data = self._safe_json_load(meta)
            if data is None:
                out_syntax.append("")
                out_count.append(0)
                continue

            tags = self._scan_lora_tags_in_json(data)
            tags = self._dedup_within_one_image(tags)

            # その画像1枚ぶんだけのLoRA構文を作る
            lines = []
            for t in tags:
                name = self._clean_name(t["name"])
                w = self._to_float(t["model_weight"])
                # あなたの形式: <name:0.6>
                lines.append(f"<{name}:{w}>")

            out_syntax.append("\n".join(lines))
            out_count.append(len(lines))

            if debug:
                print(f"[LoRASyntaxExtractor] {os.path.basename(fp)} -> {len(lines)} loras")

        return (out_syntax, out_count)

    # ---------- helpers ----------
    def _flatten_paths(self, file_path):
        out = []
        def walk(x):
            if x is None:
                return
            if isinstance(x, (list, tuple)):
                for y in x:
                    walk(y)
                return
            if isinstance(x, str):
                s = x.strip()
                if "\n" in s:
                    for line in s.splitlines():
                        walk(line)
                else:
                    out.append(s)
                return
            out.append(str(x))
        walk(file_path)
        return [p for p in out if p and str(p).strip()]

    def _read_png_metadata(self, filepath, debug=False):
        try:
            with Image.open(filepath) as img:
                info = img.info or {}
                if debug:
                    print(f"[LoRASyntaxExtractor] {os.path.basename(filepath)} keys={list(info.keys())}")
                if info.get("prompt"):
                    return info["prompt"]
                if info.get("workflow"):
                    return info["workflow"]
                if info.get("parameters"):
                    return info["parameters"]
        except Exception as e:
            print(f"[LoRASyntaxExtractor] Error reading {filepath}: {e}")
        return None

    def _safe_json_load(self, x):
        if isinstance(x, (dict, list)):
            return x
        if not isinstance(x, str):
            return None
        s = x.strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except:
            return {"_raw_text": s}

    def _scan_lora_tags_in_json(self, obj):
        results = []
        def walk(x):
            if isinstance(x, dict):
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
            elif isinstance(x, str):
                s = x
                for m in self.TAG_A1111.finditer(s):
                    results.append({"name": m.group(1).strip(), "model_weight": m.group(2)})
                for m in self.TAG_SIMPLE.finditer(s):
                    nm = m.group(1).strip()
                    if nm.lower().startswith("lora:"):
                        continue
                    results.append({"name": nm, "model_weight": m.group(2)})
        walk(obj)
        return results

    def _dedup_within_one_image(self, tags):
        seen = OrderedDict()
        for t in tags or []:
            name = self._clean_name(t.get("name", ""))
            w = self._to_float(t.get("model_weight", 1.0))
            key = (name.lower(), w)
            if key not in seen:
                seen[key] = {"name": name, "model_weight": w}
        return list(seen.values())

    def _clean_name(self, name):
        name = str(name).replace("\\", "/").split("/")[-1]
        name = re.sub(r"\.(safetensors|ckpt|pt)$", "", name, flags=re.IGNORECASE)
        return name.strip()

    def _to_float(self, v):
        try:
            return round(float(v), 2)
        except:
            return 1.0


NODE_CLASS_MAPPINGS = {"LoRASyntaxExtractor": LoRASyntaxExtractor}
NODE_DISPLAY_NAME_MAPPINGS = {"LoRASyntaxExtractor": "LoRA Syntax Extractor"}
