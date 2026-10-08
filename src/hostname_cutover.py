from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class DnsClient(Protocol):
    def domain_add(self, domain: str) -> dict[str, Any]:
        pass

    def record_upsert(self, body: dict[str, Any]) -> dict[str, Any]:
        pass

    def record_update(self, body: dict[str, Any]) -> dict[str, Any]:
        pass

    def record_delete(self, zone_id: str, record_id: str) -> dict[str, Any]:
        pass

    def domain_delete(self, domain: str, zone_id: str) -> dict[str, Any]:
        pass


@dataclass(frozen=True)
class CutoverRequest:
    domain: str
    hostname: str
    target: str
    previous_target: str
    ttl: int = 60


@dataclass(frozen=True)
class RollbackPlan:
    zone_id: str
    hostname: str
    previous_target: str
    record_id: str | None = None
    domain: str = ""


class DnsCutoverService:
    def __init__(self, client: DnsClient) -> None:
        self.client = client
        self.capability_name = "dns.domain.add"

    def apply(self, request: CutoverRequest) -> RollbackPlan:
        zone = self.client.domain_add(request.domain)
        zone_id = zone["data"]["zone_id"]
        result = self.client.record_upsert({
            "zone_id": zone_id,
            "record_type": "CNAME",
            "name": request.hostname,
            "content": request.target,
            "ttl": request.ttl,
            "metadata": {"operation": "tenant-hostname-cutover"},
        })
        record_id = result.get("data", {}).get("record_id")
        return RollbackPlan(zone_id, request.hostname, request.previous_target, record_id, request.domain)

    def rollback(self, plan: RollbackPlan) -> None:
        body: dict[str, Any] = {
            "zone_id": plan.zone_id,
            "record_type": "CNAME",
            "name": plan.hostname,
            "content": plan.previous_target,
            "ttl": 60,
            "metadata": {"operation": "tenant-hostname-rollback"},
        }
        if plan.record_id:
            body["record_id"] = plan.record_id
        self.client.record_update(body)

    def cleanup(self, plan: RollbackPlan) -> None:
        if not plan.record_id:
            raise ValueError("record_id is required to clean up a cutover")
        if not plan.domain:
            raise ValueError("domain is required to clean up a cutover")
        self.client.record_delete(plan.zone_id, plan.record_id)
        self.client.domain_delete(plan.domain, plan.zone_id)
