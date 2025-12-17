import json
import urllib.request


class IsComfyQueueEmpty:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 何でも刺せるトリガー（値は使わない）
                "trigger": ("*", {}),
                "base_url": ("STRING", {"default": "http://127.0.0.1:8188"}),
                "timeout_sec": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, input_types):
        # wildcard(*) を通すためのバリデーションスキップ
        return True

    RETURN_TYPES = ("BOOLEAN", "INT", "INT")
    RETURN_NAMES = ("is_empty", "pending_count", "running_count")
    FUNCTION = "run"
    CATEGORY = "Utils/Queue"

    def _count(self, v):
        # /queue の値が list でも int でも扱えるようにする
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, (list, tuple)):
            return len(v)
        # 想定外型は None 扱い
        return None

    def run(self, trigger, base_url, timeout_sec):
        try:
            url = base_url.rstrip("/") + "/queue"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
                raw = resp.read().decode("utf-8", errors="replace")

            data = json.loads(raw) if raw else {}

            # 基本キー
            pending_v = data.get("queue_pending", None)
            running_v = data.get("queue_running", None)

            pending_count = self._count(pending_v)
            running_count = self._count(running_v)

            # もしキーが違う/形式が違う場合の保険（無ければ失敗扱い）
            if pending_count is None or running_count is None:
                # 失敗時はクラッシュせずに「判定不能」として返す
                return (False, -1, -1)

            is_empty = (pending_count == 0)
            return (is_empty, int(pending_count), int(running_count))

        except Exception:
            # 通信失敗、JSON不正、キー不一致など全部ここに来る
            # 例外で止めずに返す（ワークフロー継続）
            return (False, -1, -1)


NODE_CLASS_MAPPINGS = {"IsComfyQueueEmpty": IsComfyQueueEmpty}
NODE_DISPLAY_NAME_MAPPINGS = {"IsComfyQueueEmpty": "Is ComfyUI Queue Empty"}
