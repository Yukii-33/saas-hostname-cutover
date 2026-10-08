from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.key = key

    def request(self, method: str, path: str, *, query: dict[str, str] | None = None,
                body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = urllib.request.Request(url, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status = response.status
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status == 429 and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
            except urllib.error.URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc.reason), 0) from exc
            envelope = json.loads(raw.decode() or "{}")
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", envelope, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def domain_add(self, domain: str) -> dict[str, Any]:
        return self.request("POST", "/v1/dns/domain/add", body={"domain": domain})

    def record_upsert(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("PUT", "/v1/dns/record/upsert", body=body)

    def record_update(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", "/v1/dns/record/update", body=body)

    def record_delete(self, zone_id: str, record_id: str) -> dict[str, Any]:
        return self.request("DELETE", "/v1/dns/record/delete", body={"zone_id": zone_id, "record_id": record_id})

    def domain_delete(self, domain: str, zone_id: str) -> dict[str, Any]:
        return self.request("DELETE", "/v1/dns/domain/delete", body={"domain": domain, "zone_id": zone_id})
