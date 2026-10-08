from __future__ import annotations

import argparse

from .hostname_cutover import CutoverRequest, DnsCutoverService
from .infrai_client import InfraiClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Cut over a SaaS hostname with a rollback plan")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--previous", required=True)
    parser.add_argument("--cleanup", action="store_true", help="Remove the created DNS record and zone after applying")
    args = parser.parse_args()
    plan = DnsCutoverService(InfraiClient()).apply(CutoverRequest(
        args.domain, args.hostname, args.target, args.previous,
    ))
    print(f"cut over {plan.hostname} in zone {plan.zone_id}; rollback target: {plan.previous_target}")
    if args.cleanup:
        DnsCutoverService(InfraiClient()).cleanup(plan)
        print(f"removed {plan.hostname} and zone {plan.zone_id}")


if __name__ == "__main__":
    main()
