from __future__ import annotations

import json
from typing import Any, Iterator

from curl_cffi import requests

from services.config import config
from services.proxy_service import proxy_settings
from utils.helper import ensure_ok, iter_sse_payloads


class OpenAICompatibleUpstream:
    def settings(self) -> dict[str, object]:
        return config.get_openai_compatible_upstream_settings()

    def is_configured(self) -> bool:
        settings = self.settings()
        return bool(
            settings.get("enabled")
            and str(settings.get("base_url") or "").strip()
            and str(settings.get("api_key") or "").strip()
        )

    def should_proxy(self, kind: str, model: object = None) -> bool:
        settings = self.settings()
        if not self.is_configured():
            return False
        if not bool(settings.get(f"proxy_{kind}", False)):
            return False
        if kind == "models":
            return True
        model_name = str(model or "").strip()
        models = [str(item).strip() for item in settings.get("models") or [] if str(item).strip()]
        prefixes = [str(item).strip() for item in settings.get("model_prefixes") or [] if str(item).strip()]
        if not models and not prefixes:
            return True
        return bool(model_name and (model_name in models or any(model_name.startswith(prefix) for prefix in prefixes)))

    def list_models(self) -> dict[str, Any] | None:
        if not self.should_proxy("models"):
            return None
        return self._request_json("GET", "/v1/models")

    def chat_completions(self, body: dict[str, Any]) -> dict[str, Any] | Iterator[dict[str, Any]] | None:
        if not self.should_proxy("chat", body.get("model")):
            return None
        return self._proxy_json_or_stream("/v1/chat/completions", body)

    def image_generations(self, body: dict[str, Any]) -> dict[str, Any] | Iterator[dict[str, Any]] | None:
        if not self.should_proxy("images", body.get("model")):
            return None
        return self._proxy_json_or_stream("/v1/images/generations", body)

    def responses(self, body: dict[str, Any]) -> dict[str, Any] | Iterator[dict[str, Any]] | None:
        if not self.should_proxy("responses", body.get("model")):
            return None
        return self._proxy_json_or_stream("/v1/responses", body)

    def _proxy_json_or_stream(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any] | Iterator[dict[str, Any]]:
        if body.get("stream"):
            return self._request_stream(endpoint, body)
        return self._request_json("POST", endpoint, body)

    def _request_json(self, method: str, endpoint: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._url(endpoint)
        headers = self._headers(url)
        kwargs = proxy_settings.build_session_kwargs(upstream=True)
        response = requests.request(
            method,
            url,
            headers=headers,
            json=body,
            timeout=self._timeout(),
            **kwargs,
        )
        ensure_ok(response, endpoint)
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}

    def _request_stream(self, endpoint: str, body: dict[str, Any]) -> Iterator[dict[str, Any]]:
        url = self._url(endpoint)
        headers = self._headers(url)
        kwargs = proxy_settings.build_session_kwargs(upstream=True)
        response = requests.post(
            url,
            headers=headers,
            json=body,
            timeout=self._timeout(),
            stream=True,
            **kwargs,
        )
        try:
            ensure_ok(response, endpoint)
            for payload in iter_sse_payloads(response):
                if payload == "[DONE]":
                    break
                try:
                    item = json.loads(payload)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"invalid upstream SSE payload: {payload[:200]}") from exc
                if isinstance(item, dict):
                    yield item
        finally:
            response.close()

    def _headers(self, url: str) -> dict[str, object]:
        settings = self.settings()
        headers = {
            "Authorization": f"Bearer {settings.get('api_key')}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json",
        }
        return proxy_settings.build_headers(headers, target_url=url, upstream=True)

    def _url(self, endpoint: str) -> str:
        base_url = str(self.settings().get("base_url") or "").strip().rstrip("/")
        if not base_url:
            raise RuntimeError("openai compatible upstream base_url is empty")
        if base_url.endswith("/v1") and endpoint.startswith("/v1/"):
            return base_url + endpoint[3:]
        return base_url + endpoint

    def _timeout(self) -> int:
        try:
            return max(1, int(self.settings().get("timeout_sec") or 120))
        except (OverflowError, TypeError, ValueError):
            return 120


openai_compatible_upstream = OpenAICompatibleUpstream()
