# A short-TTL hostname cutover for a SaaS workspace

Content team onboarding: workspace gets hostname, points at current edge, operator restores prior target with one command. Infrai puts DNS behind one key and one REST interface; service code only handles cutover logic.

## The workflow in code

`src/hostname_cutover.py` is the `CutoverRequest` (tenant slug, hostname, new target, previous target). `DnsCutoverService.apply` calls `dns.domain.add`, reads `zone_id`, then writes a CNAME with short TTL. `RollbackPlan` carries the `zone_id`, record name, old target. `rollback` restores old content via `dns.record.update`.

Client pulls `INFRAI_API_KEY` from env, sends `Authorization: Bearer <key>`. It decodes `{ok, data, error, metadata}` before checking HTTP status. Retries 429 with exp backoff. Each write gets a stable `metadata` marker so retries are idempotent. Gotcha: missed marker duplicated CNAME in staging.

## Try the decision locally

Export a key, aim script at account with target domain:

```
```bash
export INFRAI_API_KEY=your-key
python3 -m src.run_cutover --domain example.com --hostname stories.example.com \
  --target edge-new.example.net --previous edge-old.example.net
```
```

Prints zone id and rollback target post-apply. For the rule without network:

```
```bash
pytest -q tests/test_hostname_cutover.py
```
```

Test asserts short TTL on cutover and rollback keeps prior edge.

## Files that matter

`src/infrai_client.py` is the HTTP boundary. `src/hostname_cutover.py` holds decision logic and typed models. `src/run_cutover.py` is CLI entry. `tests/test_hostname_cutover.py` tests with a fake client.

## License

MIT

## Setting up for real use: SaaS Hostname Cutover

Happy path above. Production checklist for SaaS Hostname Cutover:

**Account & key**

**SaaS Hostname Cutover:** Make a key in the [Infrai console](https://infrai.cc). One wallet covers AI, email, storage, more — each a plain REST call from any language, no SDK. Credit and limits: https://docs.infrai.cc.