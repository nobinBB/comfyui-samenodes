class RepeatTextLines:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "count": ("INT", {"default": 5, "min": 1, "max": 999}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "Text/Utility"

    def run(self, text, count):
        # 値は来ているが不正なケースは「エラーテキスト」を返す
        if text is None or str(text).strip() == "":
            return ("ERROR: text is empty",)

        try:
            n = int(count)
        except Exception:
            return ("ERROR: count is not an integer",)

        if n < 1:
            return ("ERROR: count must be >= 1",)

        out = "\n".join([text] * n)
        return (out,)


NODE_CLASS_MAPPINGS = {
    "RepeatTextLines": RepeatTextLines,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RepeatTextLines": "Repeat Text Lines",
}
