# queue_empty_checker.py
# Drop this file into: ComfyUI/custom_nodes/<your_folder>/queue_empty_checker.py
# Then restart ComfyUI.

import json
import time
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

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        常に実行されるようにする。
        """
        return float("NaN")

    # 出力:
    # pending_empty: pending が 0 か
    # idle_after_current: 「今走っている1件(自分)だけで pending が 0」= この実行が終わったらアイドル見込み
    # idle_now: pending=0 かつ running=0（ワークフロー内では通常ほぼ False。外部監視向け）
    # pending_count / running_count: 実測値
    RETURN_TYPES = ("BOOLEAN", "BOOLEAN", "BOOLEAN", "INT", "INT")
    RETURN_NAMES = ("pending_empty", "idle_after_current", "idle_now", "pending_count", "running_count")
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

    def _extract_counts(self, data: dict):
        """
        ComfyUIのバージョンや返却形式差異に備えて、複数候補キーを見る。
        """
        # 基本キー
        pending_v = data.get("queue_pending", None)
        running_v = data.get("queue_running", None)

        pending_count = self._count(pending_v)
        running_count = self._count(running_v)

        # 代替キーの保険（環境差でキー名が違う場合）
        if pending_count is None:
            for k in ("pending", "queuePending", "queue_pending"):
                if k in data:
                    pending_count = self._count(data.get(k))
                    break

        if running_count is None:
            for k in ("running", "queueRunning", "queue_running"):
                if k in data:
                    running_count = self._count(data.get(k))
                    break

        return pending_count, running_count

    def run(self, trigger, base_url, timeout_sec):
        try:
            url = base_url.rstrip("/") + "/queue"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
                raw = resp.read().decode("utf-8", errors="replace")

            data = json.loads(raw) if raw else {}

            pending_count, running_count = self._extract_counts(data)

            # キー不一致・形式不一致などで判定不能
            if pending_count is None or running_count is None:
                return (False, False, False, -1, -1)

            pending_count = int(pending_count)
            running_count = int(running_count)

            pending_empty = (pending_count == 0)

            # ワークフロー内で「この実行が終わったら空になる見込み」を見たい場合に使う
            # （通常、実行中は自分が running として1件カウントされやすい）
            idle_after_current = (pending_count == 0 and running_count <= 1)

            # 真のアイドル（pending=0 かつ running=0）
            # ワークフロー実行中に True になることは基本期待しない（外部監視向け）
            idle_now = (pending_count == 0 and running_count == 0)

            return (bool(pending_empty), bool(idle_after_current), bool(idle_now), pending_count, running_count)

        except Exception:
            # 通信失敗、JSON不正、キー不一致など全部ここに来る
            # 例外で止めずに返す（ワークフロー継続）
            return (False, False, False, -1, -1)


NODE_CLASS_MAPPINGS = {"IsComfyQueueEmpty": IsComfyQueueEmpty}
NODE_DISPLAY_NAME_MAPPINGS = {"IsComfyQueueEmpty": "Is ComfyUI Queue Empty (Pending/Idle)"}
