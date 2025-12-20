#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from toxicornot_inference import load_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal HTTP server for toxicity inference.")
    parser.add_argument("--artifacts", default="results/toxic_logreg.joblib", help="Path to .joblib artifacts")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--threshold", type=float, default=0.5, help="Classification threshold")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model = load_model(args.artifacts)
    threshold = float(args.threshold)

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path in ("/", "/health"):
                self._send_json(200, {"ok": True})
                return
            self._send_json(404, {"error": "not_found"})

        def do_POST(self) -> None:
            if self.path != "/predict":
                self._send_json(404, {"error": "not_found"})
                return

            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._send_json(400, {"error": "invalid_json"})
                return

            texts: list[str]
            if isinstance(payload, dict) and isinstance(payload.get("text"), str):
                texts = [payload["text"]]
                single = True
            elif isinstance(payload, dict) and isinstance(payload.get("texts"), list):
                texts = [str(t) for t in payload["texts"]]
                single = False
            else:
                self._send_json(400, {"error": "expected {'text': str} or {'texts': [str, ...]}"})
                return

            probs = model.predict_proba(texts)
            labels = (probs >= threshold).astype(int)
            outputs = [
                {"toxic": int(label), "toxic_proba": float(prob)}
                for prob, label in zip(probs.tolist(), labels.tolist(), strict=False)
            ]

            self._send_json(200, outputs[0] if single else {"results": outputs})

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Listening on http://{args.host}:{args.port} (POST /predict)")
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
