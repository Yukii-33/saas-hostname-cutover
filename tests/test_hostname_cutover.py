from src.hostname_cutover import CutoverRequest, DnsCutoverService


class FakeDns:
    def __init__(self):
        self.calls = []

    def domain_add(self, domain):
        self.calls.append(("domain_add", domain))
        return {"ok": True, "data": {"zone_id": "zone-123"}}

    def record_upsert(self, body):
        self.calls.append(("upsert", body))
        return {"ok": True, "data": {"record_id": "record-9"}}

    def record_update(self, body):
        self.calls.append(("update", body))
        return {"ok": True, "data": {}}

    def record_delete(self, zone_id, record_id):
        self.calls.append(("record_delete", zone_id, record_id))
        return {"ok": True, "data": {}}

    def domain_delete(self, domain, zone_id):
        self.calls.append(("domain_delete", domain, zone_id))
        return {"ok": True, "data": {}}


def test_cutover_keeps_previous_target_for_rollback():
    fake = FakeDns()
    service = DnsCutoverService(fake)
    plan = service.apply(CutoverRequest("example.com", "stories.example.com", "edge-new.example.net", "edge-old.example.net"))

    assert fake.calls[1][1]["zone_id"] == "zone-123"
    assert fake.calls[1][1]["ttl"] == 60
    assert plan.previous_target == "edge-old.example.net"
    service.rollback(plan)
    assert fake.calls[2][1]["content"] == "edge-old.example.net"


def test_cleanup_deletes_record_before_zone():
    fake = FakeDns()
    service = DnsCutoverService(fake)
    plan = service.apply(CutoverRequest("example.com", "stories.example.com", "edge-new.example.net", "edge-old.example.net"))
    service.cleanup(plan)
    assert fake.calls[-2:] == [("record_delete", "zone-123", "record-9"), ("domain_delete", "example.com", "zone-123")]
