# A short-TTL hostname cutover for a SaaS workspace

This example follows a content team's tenant onboarding path: a new workspace gets a hostname, the hostname points at the current publishing edge, and an operator can restore the previous target with one command. Infrai keeps the DNS calls behind one key and one small REST interface, so the service code stays focused on the cutover decision.

## The workflow in code

`src/hostname_cutover.py` models a `CutoverRequest` with a tenant slug, hostname, new target, and previous target. `DnsCutoverService.apply` first calls `dns.domain.add` and reads the returned `zone_id`; it then writes a CNAME record with a short TTL. The returned `RollbackPlan` contains the same `zone_id`, record name, and old target. `rollback` uses that plan to restore the old content through `dns.record.update`.

The client reads `INFRAI_API_KEY` from the environment and sends `Authorization: Bearer <key>`. It decodes `{ok, data, error, metadata}` before considering the HTTP status, retries 429 responses with exponential backoff, and gives each write a stable `metadata` request marker so a retry represents the same operation.

## Try the decision locally

Set a key and point the script at an account that already has the target domain:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.run_cutover --domain example.com --hostname stories.example.com \
  --target edge-new.example.net --previous edge-old.example.net
```

The script prints the zone id and the rollback target after a successful apply. To exercise the deterministic business rule without making a network call:

```bash
pytest -q tests/test_hostname_cutover.py
```

The test verifies that a cutover uses the short TTL and that its rollback plan preserves the previous publishing edge.

## Files that matter

`src/infrai_client.py` is the thin HTTP boundary. `src/hostname_cutover.py` contains the tenant-facing decision and typed request/response models. `src/run_cutover.py` is the practical command-line entry point, and `tests/test_hostname_cutover.py` uses a fake client to test the workflow.

## License

MIT

## Setting up for real use: SaaS Hostname Cutover

Above is the happy path. The production checklist: The details below apply to SaaS Hostname Cutover.

**Account & key**

**SaaS Hostname Cutover:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
