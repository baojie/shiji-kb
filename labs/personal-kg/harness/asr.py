"""ASR client — calls the FunASR microservice (paraformer-zh)."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib import request, error
import json

ASR_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".mp4", ".aac"}


class ASRClient:
    def __init__(self, endpoint: str, model: str = "paraformer-zh", timeout: int = 300):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ASRClient":
        asr_cfg = config.get("asr", {})
        return cls(
            endpoint=asr_cfg.get("endpoint", "http://192.168.196.191:8015"),
            model=asr_cfg.get("model", "paraformer-zh"),
            timeout=int(asr_cfg.get("timeout", 300)),
        )

    def health(self) -> dict[str, Any]:
        """Check if ASR service is up."""
        try:
            with request.urlopen(f"{self.endpoint}/health", timeout=5) as r:
                return json.loads(r.read().decode())
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def transcribe(self, audio_path: str | Path) -> list[dict[str, Any]]:
        """
        Transcribe an audio file.

        Returns a list of utterance dicts:
            [{"text": "...", "start": 0.0, "end": 2.5, "speaker": "spk_0"}, ...]

        Falls back to a single utterance if the service returns only plain text.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        url = f"{self.endpoint}/v1/audio/transcriptions"

        # Build multipart/form-data manually (stdlib only)
        boundary = f"----Boundary{int(time.time())}"
        body_parts: list[bytes] = []

        def _field(name: str, value: str) -> bytes:
            return (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()

        body_parts.append(_field("model", self.model))
        body_parts.append(_field("language", "zh"))
        body_parts.append(_field("response_format", "verbose_json"))

        # File part
        mime = _mime_for(audio_path.suffix)
        file_header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
        body_parts.append(file_header)
        body_parts.append(audio_path.read_bytes())
        body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode())

        body = b"".join(body_parts)
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )

        t0 = time.perf_counter()
        try:
            with request.urlopen(req, timeout=self.timeout) as r:
                raw = json.loads(r.read().decode())
        except error.HTTPError as exc:
            raise RuntimeError(f"ASR HTTP {exc.code}: {exc.read().decode()[:200]}") from exc
        except Exception as exc:
            raise RuntimeError(f"ASR request failed: {exc}") from exc

        elapsed = time.perf_counter() - t0
        return _parse_response(raw, elapsed)


def _mime_for(ext: str) -> str:
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".mp4": "video/mp4",
        ".aac": "audio/aac",
    }.get(ext.lower(), "application/octet-stream")


def _parse_response(raw: dict[str, Any], elapsed: float) -> list[dict[str, Any]]:
    """
    Normalize verbose_json response into a flat list of utterances.

    Input (verbose_json):
        {
          "text": "全文",
          "segments": [
            {"text": "...", "start": 0.0, "end": 2.5},   # speaker optional
            ...
          ],
          "duration": 60.0
        }

    Output:
        [{"text": "...", "start": 0.0, "end": 2.5, "speaker": "spk_0"}, ...]
    """
    segments = raw.get("segments") or []

    if segments:
        result = []
        for seg in segments:
            result.append({
                "text": str(seg.get("text", "")).strip(),
                "start": float(seg.get("start", 0.0)),
                "end": float(seg.get("end", 0.0)),
                "speaker": str(seg.get("speaker") or seg.get("spk", "spk_0")),
            })
        return [u for u in result if u["text"]]

    # Fallback: service returned only plain text
    full_text = str(raw.get("text", "")).strip()
    if not full_text:
        return []
    duration = float(raw.get("duration", 0.0) or elapsed)
    return [{"text": full_text, "start": 0.0, "end": duration, "speaker": "spk_0"}]


def is_audio_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() in ASR_AUDIO_EXTS
