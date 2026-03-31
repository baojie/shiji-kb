"""Local model adapter — OpenAI-compatible endpoint."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib import error, request

try:
    import yaml
except ImportError:
    yaml = None

CONFIG_PATH = Path(__file__).resolve().with_name("config.yaml")
PROJECT_ROOT = CONFIG_PATH.parent.parent
LOG_PATH = PROJECT_ROOT / "logs" / "model_calls.jsonl"

JSON_SUFFIX = "\n请只输出JSON，不要解释："


def load_config(config_path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    if yaml is None:
        raise RuntimeError("pyyaml required. pip install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class LocalModel:
    def __init__(self, config: dict[str, Any]):
        cfg = config.get("local_model", config)
        self.endpoint: str = cfg["endpoint"]
        self.model_name: str = cfg["model_name"]
        self.max_tokens: int = int(cfg.get("max_tokens", 512))
        self.temperature: float = float(cfg.get("temperature", 0.1))
        self.timeout: float = float(cfg.get("timeout", 30))
        self.retries: int = 2
        self.retry_wait: float = 1.0

    @classmethod
    def from_config(cls, path: str | Path = CONFIG_PATH) -> "LocalModel":
        return cls(load_config(path))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, prompt: str, system: str | None = None) -> str:
        """Free-text chat. Returns the model's raw string response."""
        messages = self._build_messages(prompt, system)
        return self._call(messages)

    def chat_json(
        self,
        prompt: str,
        system: str | None = None,
        schema: dict | None = None,
    ) -> dict | list:
        """Chat that expects JSON back. Retries on parse failure."""
        schema_hint = ""
        if schema:
            schema_hint = "\n期望JSON结构：" + json.dumps(
                schema, ensure_ascii=False, separators=(",", ":")
            )
        full_prompt = f"{prompt.rstrip()}{schema_hint}{JSON_SUFFIX}"
        messages = self._build_messages(full_prompt, system)

        last: dict = {"error": "parse_failed", "raw": ""}
        for attempt in range(self.retries + 1):
            raw = self._call(messages)
            result = self._parse_json(raw)
            if not (isinstance(result, dict) and result.get("error") == "parse_failed"):
                return result
            last = result
            if attempt < self.retries:
                time.sleep(self.retry_wait)
        return last

    def test_connection(self) -> dict[str, Any]:
        try:
            resp = self.chat('你好，请回复 OK')
            return {"ok": True, "response": resp}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_messages(
        self, prompt: str, system: str | None
    ) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = []
        # 直接使用 system 原文，不截断——SKILL文档需要完整传入
        if system:
            msgs.append({"role": "system", "content": system.strip()})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def _call(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        body = json.dumps(payload, ensure_ascii=False).encode()
        req = request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        prompt_len = sum(len(m["content"]) for m in messages)
        last_exc: Exception | None = None

        for attempt in range(self.retries + 1):
            t0 = time.perf_counter()
            resp_text = ""
            try:
                with request.urlopen(req, timeout=self.timeout) as r:
                    resp_text = self._extract(json.loads(r.read().decode()))
                self._log(prompt_len, len(resp_text), time.perf_counter() - t0, True)
                return resp_text
            except Exception as exc:
                self._log(
                    prompt_len, len(resp_text),
                    time.perf_counter() - t0, False, str(exc)
                )
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.retry_wait)

        raise RuntimeError(f"Model call failed: {last_exc}")

    def _extract(self, api_json: dict) -> str:
        choices = api_json.get("choices") or []
        if not choices:
            raise ValueError(f"No choices in response: {api_json}")
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") for p in content if isinstance(p, dict)
            )
        return str(content).strip()

    def _parse_json(self, raw: str) -> dict | list:
        raw = raw.strip()
        # 去掉 markdown 代码块
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # 提取第一个完整 {...} 或 [...]
        candidate = self._find_json_block(raw)
        if candidate:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        return {"error": "parse_failed", "raw": raw[:500]}

    def _find_json_block(self, raw: str) -> str | None:
        m = re.search(r"[{\[]", raw)
        if not m:
            return None
        start = m.start()
        opener = raw[start]
        closer = "}" if opener == "{" else "]"
        depth, in_str, escaped = 0, False, False
        for i in range(start, len(raw)):
            c = raw[i]
            if in_str:
                escaped = (not escaped and c == "\\")
                if not escaped and c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return raw[start: i + 1]
        return None

    def _log(
        self,
        prompt_len: int,
        resp_len: int,
        elapsed: float,
        ok: bool,
        err: str | None = None,
    ) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model": self.model_name,
            "prompt_len": prompt_len,
            "resp_len": resp_len,
            "elapsed_ms": round(elapsed * 1000, 1),
            "ok": ok,
        }
        if err:
            rec["error"] = err
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
