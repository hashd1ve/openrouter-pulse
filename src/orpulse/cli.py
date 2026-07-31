"""Command line entry point."""

from __future__ import annotations

import argparse
import logging
import sys

from . import config, dashboard, derive, ingest, quality, report, transform


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)-18s %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_ingest(args) -> int:
    manifest = ingest.run(
        sweep_endpoints=not args.no_endpoints, max_models=args.max_models
    )
    if manifest.requests_failed:
        print(
            f"note: {manifest.requests_failed} request(s) failed and were recorded "
            f"in the manifest; the snapshot is still complete.",
            file=sys.stderr,
        )
    return 0


def cmd_build(args) -> int:
    staging = transform.build_staging()
    transform.build_marts(staging)
    # Statistical marts depend on the SQL ones, so they run second and are
    # reloaded together before validation.
    derive.build_all(transform.load_marts())
    marts = transform.load_marts()
    results = quality.run_all(marts)
    print()
    for r in results:
        print(f"  {r}")
    print()
    if args.no_enforce:
        return 0
    try:
        quality.enforce(results)
    except quality.DataQualityError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def cmd_check(args) -> int:
    marts = transform.load_marts()
    if not marts:
        print("no marts found; run `make build` first", file=sys.stderr)
        return 1
    results = quality.run_all(marts)
    for r in results:
        print(f"  {r}")
    return 1 if any(r.blocking for r in results) else 0


def cmd_report(args) -> int:
    marts = transform.load_marts()
    if not marts:
        print("no marts found; run `make build` first", file=sys.stderr)
        return 1
    path = report.write(marts)
    print(f"wrote {path}")
    return 0


def cmd_dashboard(args) -> int:
    marts = transform.load_marts()
    if not marts:
        print("no marts found; run `make build` first", file=sys.stderr)
        return 1
    if args.fragment:
        print(f"wrote {dashboard.write_fragment(marts)}")
    print(f"wrote {dashboard.write(marts)}")
    return 0


def cmd_snapshots(args) -> int:
    dates = ingest.list_snapshots()
    if not dates:
        print("no completed snapshots")
        return 0
    print(f"{len(dates)} completed snapshot(s):")
    for d in dates:
        m = ingest.load_manifest(d)
        print(
            f"  {d}  {m['requests_ok']:>4} ok  {m['requests_failed']:>3} failed  "
            f"{m['bytes_received'] / 1e6:>6.1f} MB  {m.get('duration_seconds', 0):>6.1f}s"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orpulse", description="Workload fingerprinting from OpenRouter public data"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="capture one immutable snapshot")
    p.add_argument(
        "--no-endpoints",
        action="store_true",
        help="skip the per-model endpoint sweep (fast; usage data only)",
    )
    p.add_argument("--max-models", type=int, help="limit the endpoint sweep, for testing")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("build", help="rebuild staging and marts, then validate")
    p.add_argument(
        "--no-enforce", action="store_true", help="report quality failures without exiting non-zero"
    )
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("check", help="run quality checks against existing marts")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("report", help="regenerate docs/FINDINGS.md from the marts")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("dashboard", help="build the self-contained HTML dashboard")
    p.add_argument(
        "--fragment",
        action="store_true",
        help="also emit the body-only form, for a host that supplies its own "
             "document skeleton",
    )
    p.set_defaults(func=cmd_dashboard)

    p = sub.add_parser("snapshots", help="list completed snapshots")
    p.set_defaults(func=cmd_snapshots)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
