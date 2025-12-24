import json
import re
import os
from PIL import Image


class A1111PromptSplitter:
    """
    Batch-safe Positive/Negative prompt extractor for A1111-like 'parameters' metadata.

    Input : list of PNG file paths
    Output: (positive_prompt_per_image, negative_prompt_per_image) lists aligned with input order
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

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt_per_image", "negative_prompt_per_image")
    FUNCTION = "extract"
    CATEGORY = "SameNodes/prompt"

    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True, True)

    RE_NEG_LABEL = re.compile(r"\bNegative prompt:\s*", re.IGNORECASE)
    RE_CUT_KEYS = re.compile(
        r"\n\s*(Steps:|Sampler:|Schedule type:|CFG scale:|Seed:|Size:|Model hash:|Model:|VAE:|Clip skip:|Denoising strength:)\s*",
        re.IGNORECASE
    )

    def extract(self, file_path, debug=False):
        paths = self._flatten_paths(file_path)

        if debug:
            print(f"[A1111PromptSplitter] flattened paths = {len(paths)}")
            for i, p in enumerate(paths):
                print(f"  [{i}] {p}")

        out_pos = []
        out_neg = []

        for fp in paths:
            fp = ("" if fp is None else str(fp)).strip().strip('"').strip("'")
            if not fp or not os.path.exists(fp):
                out_pos.append("")
                out_neg.append("")
                continue

            meta = self._read_png_metadata(fp, debug=debug)
            if meta is None:
                out_pos.append("")
                out_neg.append("")
                continue

            pos, neg = self._extract_posneg_from_meta(meta)
            out_pos.append(pos)
            out_neg.append(neg)

            if debug:
                print(f"[A1111PromptSplitter] {os.path.basename(fp)} pos={len(pos)} chars neg={len(neg)} chars")

        return (out_pos, out_neg)

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
        """
        Priority: parameters -> prompt -> workflow
        """
        try:
            with Image.open(filepath) as img:
                info = img.info or {}
                if debug:
                    print(f"[A1111PromptSplitter] {os.path.basename(filepath)} keys={list(info.keys())}")

                if info.get("parameters"):
                    return info["parameters"]
                if info.get("prompt"):
                    return info["prompt"]
                if info.get("workflow"):
                    return info["workflow"]
        except Exception as e:
            print(f"[A1111PromptSplitter] Error reading {filepath}: {e}")
        return None

    def _extract_posneg_from_meta(self, meta):
        # parameters直（文字列）
        if isinstance(meta, str):
            return self._parse_a1111_parameters(meta)

        # prompt/workflow（dict/list）の場合は "Negative prompt:" を含む文字列を探す
        params_str = self._find_parameters_like_string(meta)
        if params_str:
            return self._parse_a1111_parameters(params_str)

        return ("", "")

    def _find_parameters_like_string(self, obj):
        found = None

        def walk(x):
            nonlocal found
            if found is not None:
                return
            if isinstance(x, dict):
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
            elif isinstance(x, str):
                if self.RE_NEG_LABEL.search(x):
                    found = x

        walk(obj)
        return found

    def _parse_a1111_parameters(self, s):
        """
        A1111-like parameters:
          <positive...>
          Negative prompt: <negative...>
          Steps: ... (settings follow)
        """
        if not isinstance(s, str):
            return ("", "")

        text = s.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return ("", "")

        m = self.RE_NEG_LABEL.search(text)
        if not m:
            # Negative prompt: が無い場合は全部positive扱い
            return (text.strip(), "")

        pos = text[:m.start()].strip()
        neg_plus = text[m.end():].strip()

        # negative側の後ろに設定行が続く場合はカット
        cut = self.RE_CUT_KEYS.search("\n" + neg_plus)
        if cut:
            neg = neg_plus[:cut.start()].strip()
        else:
            neg = neg_plus.strip()

        return (pos, neg)


NODE_CLASS_MAPPINGS = {
    "A1111PromptSplitter": A1111PromptSplitter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "A1111PromptSplitter": "A1111 Prompt Splitter (Pos/Neg)"
}
