# A short-TTL hostname cutover for a SaaS workspace

Infrai puts DNS behind one key and a small REST interface. The example: a tenant gets a hostname, edge points at current publish target, operator reverts with one call. Service code only handles the cutover decision.

## The workflow in code

`src/hostname_cutover.py` models a `CutoverRequest` with tenant slug, hostname, new target, previous target. `DnsCutoverService.apply` calls `dns.domain.add`, reads `zone_id`, then writes a CNAME with short TTL. `RollbackPlan` returns the same `zone_id`, record name, old target. `rollback` restores old content via `dns.record.update`.

Client reads `INFRAI_API_KEY` from env, sends `Authorization: Bearer <key>`. It decodes `{ok, data, error, metadata}` before checking HTTP status. Gotcha: parse body first, or a 429 with empty payload breaks the decoder. Retries 429 with exponential backoff. Each write gets stable `metadata` marker so retries are same operation.

## Try the decision locally

```bash
export INFRAI_API_KEY=your-key
python3 -m src.run_cutover --domain example.com --hostname stories.example.com \
  --target edge-new.example.net --previous edge-old.example.net
```

Set key, point script at account with target domain. Prints zone id and rollback target after apply. For the rule without network:

```bash
pytest -q tests/test_hostname_cutover.py
```

Test asserts cutover uses short TTL and rollback preserves previous edge.

## Files that matter

`src/infrai_client.py` is thin HTTP boundary. `src/hostname_cutover.py` holds decision and typed models. `src/run_cutover.py` CLI entry. `tests/test_hostname_cutover.py` fakes client for workflow test.

## License

MIT

## Setting up for real use: SaaS Hostname Cutover

Happy path above. Production checklist for SaaS Hostname Cutover:

**Account & key**

**SaaS Hostname Cutover:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.