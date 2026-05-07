import re
from typing import List


class TipoNaturalLanguageBanCompensator:
    """
    Applies regex-based ban filtering to natural-language prompts and compensates
    removed content by filling with safe details. If erotic keywords are present,
    compensation prefers stronger sensual-quality descriptors while keeping banned
    patterns excluded.
    """

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("filtered_text", "removed_chunks", "before_chunk_count", "after_chunk_count")
    FUNCTION = "process"
    CATEGORY = "SameNodes/prompt"

    EROTIC_HINT_RE = re.compile(
        r"\b(nsfw|nude|naked|sexy|erotic|lewd|sensual|lingerie|bedroom|boobs?|breasts?|ass|thighs?)\b",
        re.IGNORECASE,
    )

    SAFE_FILLERS = [
        "cinematic composition",
        "high detail background",
        "dramatic but clean lighting",
        "rich color contrast",
        "atmospheric depth",
        "careful fabric texture",
        "balanced body pose",
        "sharp focus on subject",
    ]

    EROTIC_FILLERS = [
        "tasteful sensual mood",
        "seductive camera framing",
        "soft intimate lighting",
        "refined erotic atmosphere",
        "alluring pose emphasis",
        "high-detail skin shading",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "dynamicPrompts": False}),
                "ban_patterns": ("STRING", {"multiline": True, "default": ".*hair.*"}),
                "target_min_chunks": ("INT", {"default": 12, "min": 1, "max": 256}),
                "separator": ("STRING", {"default": ", "}),
            }
        }

    def _compile_patterns(self, ban_patterns: str) -> List[re.Pattern]:
        patterns = []
        for line in ban_patterns.splitlines():
            raw = line.strip()
            if not raw:
                continue
            patterns.append(re.compile(raw, re.IGNORECASE))
        return patterns

    def _split_chunks(self, text: str) -> List[str]:
        chunks = [c.strip() for c in re.split(r"[,\n;.]+", text) if c.strip()]
        return chunks

    def process(self, text: str, ban_patterns: str, target_min_chunks: int, separator: str):
        patterns = self._compile_patterns(ban_patterns)
        chunks = self._split_chunks(text)
        before_count = len(chunks)

        kept, removed = [], []
        for ch in chunks:
            if any(p.search(ch) for p in patterns):
                removed.append(ch)
            else:
                kept.append(ch)

        erotic_mode = bool(self.EROTIC_HINT_RE.search(text))
        pool = self.EROTIC_FILLERS + self.SAFE_FILLERS if erotic_mode else self.SAFE_FILLERS

        seen = {k.lower() for k in kept}
        need = max(target_min_chunks - len(kept), 0)

        for filler in pool:
            if need <= 0:
                break
            if filler.lower() in seen:
                continue
            if any(p.search(filler) for p in patterns):
                continue
            kept.append(filler)
            seen.add(filler.lower())
            need -= 1

        # If still short, create deterministic variants.
        idx = 1
        while need > 0:
            variant = f"enhanced scene detail {idx}"
            idx += 1
            if any(p.search(variant) for p in patterns):
                continue
            kept.append(variant)
            need -= 1

        filtered_text = separator.join(kept)
        removed_chunks = separator.join(removed)
        return (filtered_text, removed_chunks, before_count, len(kept))


NODE_CLASS_MAPPINGS = {
    "TipoNaturalLanguageBanCompensator": TipoNaturalLanguageBanCompensator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TipoNaturalLanguageBanCompensator": "TIPO NL Ban + Compensator",
}
