import re
import threading
from collections import OrderedDict

import impact.wildcards

try:
    from server import PromptServer
except Exception:
    PromptServer = None


_TRACE_LOCK = threading.Lock()

WILDCARD_TITLE_RE = re.compile(
    r"(?:(?P<count>\d+)#)?__(?P<title>[\w.\-+/*\\]+?)__",
    re.IGNORECASE,
)


def _to_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return "\n".join(str(v) for v in value)

    return str(value)


def _unique_keep_order(items):
    return list(OrderedDict.fromkeys(items))


def _normalize_title(title):
    try:
        return impact.wildcards.wildcard_normalize(str(title))
    except Exception:
        return str(title).replace("\\", "/").replace(" ", "-").lower()


def _extract_titles_from_text(text):
    titles = []

    for match in WILDCARD_TITLE_RE.finditer(_to_text(text)):
        title = match.group("title")
        title = _normalize_title(title)
        if title.strip():
            titles.append(title)

    return _unique_keep_order(titles)

def _clean_wildcard_title(title):
    title = str(title).replace("\\", "/").strip()

    # */大好きホールド → 大好きホールド
    if title.startswith("*/"):
        title = title[2:]

    # gentlmen-entanglement-package/大好きホールド → 大好きホールド
    if "/" in title:
        title = title.split("/")[-1]

    return title.strip()


def _final_selected_titles(used_titles, source_text):
    cleaned_used = []

    for title in used_titles:
        cleaned = _clean_wildcard_title(title)

        if cleaned:
            cleaned_used.append(cleaned)

    cleaned_used = _unique_keep_order(cleaned_used)

    source_titles = _extract_titles_from_text(source_text)
    source_titles = [_clean_wildcard_title(x) for x in source_titles]
    source_titles = _unique_keep_order([x for x in source_titles if x])

    # 元入力に直接書いてある親wildcardを除外
    if len(cleaned_used) > 1:
        cleaned_used = [x for x in cleaned_used if x not in source_titles]

    # オールランダム系の親名は不要
    cleaned_used = [
        x for x in cleaned_used
        if "オールランダム" not in x
        and "allrandom" not in x.lower()
        and "all_random" not in x.lower()
    ]

    return _unique_keep_order(cleaned_used)

def _process_with_trace(text, seed):
    used_titles = []

    original_get_wildcard_value = impact.wildcards.get_wildcard_value

    def wrapped_get_wildcard_value(key):
        used_titles.append(_normalize_title(key))
        return original_get_wildcard_value(key)

    with _TRACE_LOCK:
        impact.wildcards.get_wildcard_value = wrapped_get_wildcard_value

        try:
            processed_text = impact.wildcards.process(text=text, seed=seed)
        finally:
            impact.wildcards.get_wildcard_value = original_get_wildcard_value

    if not used_titles:
        used_titles = _extract_titles_from_text(text)

    return processed_text, _unique_keep_order(used_titles)


class ImpactWildcardProcessorTitle:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "wildcard_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": False,
                        "default": "",
                        "tooltip": "Enter a prompt using wildcard syntax.",
                    },
                ),
                "populated_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": False,
                        "default": "",
                        "tooltip": "The populated prompt. In fixed/reproduce mode, this text is used.",
                    },
                ),
                "mode": (
                    ["populate", "fixed", "reproduce", "randomize"],
                    {
                        "default": "populate",
                        "tooltip": "populate: process wildcard_text. fixed/reproduce: process populated_text. randomize is accepted only to repair old broken saved nodes.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Determines the random seed to be used for wildcard processing.",
                    },
                ),
                "Select to add Wildcard": (
                    ["Select the Wildcard to add to the text"],
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("processed text", "wildcard titles")

    FUNCTION = "doit"
    CATEGORY = "ImpactPack/Prompt"

    def doit(
        self,
        wildcard_text,
        populated_text,
        mode,
        seed,
        unique_id=None,
        **kwargs,
    ):
        wildcard_text = _to_text(wildcard_text)
        populated_text = _to_text(populated_text)

        if mode not in ("populate", "fixed", "reproduce"):
            mode = "populate"

        if mode == "populate":
            source_text = wildcard_text
        else:
            source_text = populated_text

        if not source_text.strip():
            source_text = wildcard_text

        processed_text, used_titles = _process_with_trace(source_text, seed)

        selected_titles = _final_selected_titles(used_titles, source_text)
        wildcard_titles = "\n".join(selected_titles)

        if PromptServer is not None and unique_id is not None:
            try:
                PromptServer.instance.send_sync(
                    "samenodes-impact-wildcard-title-populated",
                    {
                        "node_id": unique_id,
                        "value": processed_text,
                    },
                )
            except Exception as e:
                print(f"[ImpactWildcardProcessorTitle] populated_text update failed: {e}")

        return processed_text, wildcard_titles


NODE_CLASS_MAPPINGS = {
    "ImpactWildcardProcessorTitle": ImpactWildcardProcessorTitle,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImpactWildcardProcessorTitle": "Impact Wildcard Processor Title",
}