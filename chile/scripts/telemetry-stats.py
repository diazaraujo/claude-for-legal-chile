#!/usr/bin/env python3
"""Resumen del log de telemetría del MCP corpus-search.

Lee ~/.claude-legal-chile/telemetry.jsonl (o CORPUS_TELEMETRY_LOG) y
muestra top tools, p50/p95 de latencia, top queries y errores.

Uso:
  python3 telemetry-stats.py                # default path
  python3 telemetry-stats.py --tail 100     # último N
  python3 telemetry-stats.py --top 20       # top queries
  python3 telemetry-stats.py --path /tmp/foo.jsonl
"""
from __future__ import annotations
import argparse, json, os, sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median


DEFAULT_PATH = os.environ.get(
    "CORPUS_TELEMETRY_LOG",
    str(Path.home() / ".claude-legal-chile" / "telemetry.jsonl"),
)


def pctl(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = int(p * (len(xs) - 1))
    return xs[k]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=DEFAULT_PATH)
    parser.add_argument("--tail", type=int, default=0, help="Solo último N events")
    parser.add_argument("--top", type=int, default=10, help="Top queries a mostrar")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"No existe: {p}", file=sys.stderr)
        return 1

    events: list[dict] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if args.tail > 0:
        events = events[-args.tail:]

    if not events:
        print("(sin eventos)")
        return 0

    by_tool: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        by_tool[e.get("tool", "?")].append(e)

    print(f"Telemetry: {len(events)} eventos  ·  {p}\n")
    print(f"{'tool':30s} {'count':>6s}  {'p50_ms':>8s}  {'p95_ms':>8s}  {'errors':>7s}")
    print("-" * 70)
    for tool, evs in sorted(by_tool.items(), key=lambda x: -len(x[1])):
        lat = [e["latency_ms"] for e in evs if e.get("latency_ms") is not None]
        errs = sum(1 for e in evs if e.get("error"))
        print(f"{tool:30s} {len(evs):>6d}  {pctl(lat, 0.5):>8.1f}  "
              f"{pctl(lat, 0.95):>8.1f}  {errs:>7d}")

    queries = Counter(
        e.get("query", "")[:80] for e in events
        if e.get("query") and e.get("tool") in ("corpus_search", "corpus_search_articulos",
                                                 "corpus_expand_query")
    )
    if queries:
        print(f"\nTop {args.top} queries:")
        for q, n in queries.most_common(args.top):
            print(f"  {n:>4d}  {q}")

    errors = [e for e in events if e.get("error")]
    if errors:
        print(f"\nErrores ({len(errors)}):")
        for e in errors[-5:]:
            print(f"  {e.get('tool')}: {e.get('error')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
