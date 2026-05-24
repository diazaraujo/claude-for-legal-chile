#!/usr/bin/env python3
"""Runner del golden test suite.

Lee `golden_queries.yaml`, ejecuta cada caso contra el corpus FTS,
reporta pass/fail por caso + score promedio. Salir con código 0 si
todos passan, 1 en caso contrario.
"""
from __future__ import annotations
import sys
import re
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SCRIPTS / "mcp-corpus-search/src"))

from mcp_corpus_search.search_client import CorpusSearchClient

_YAML = Path(__file__).parent / "golden_queries.yaml"


def parse_yaml_lite(text: str) -> dict:
    """Parser YAML mínimo para evitar dependencia PyYAML.
    Soporta: list of dicts, strings cuoted/unquoted, nested dicts/lists.
    Suficiente para el formato fijo de golden_queries.yaml.
    """
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        pass

    # Fallback: parse manual del schema conocido
    cases: list[dict] = []
    cur: dict | None = None
    indent_stack: list[tuple[int, str, list]] = []
    in_or: list | None = None
    in_expect_any: list | None = None

    for line in text.splitlines():
        raw = line.rstrip()
        if not raw or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.lstrip()

        if stripped.startswith("- id:"):
            if cur:
                cases.append(cur)
            cur = {"id": stripped[5:].strip().strip('"')}
            in_or = None
            in_expect_any = None
            continue
        if cur is None:
            continue

        # In or-block
        if in_or is not None and stripped.startswith("- path_contains:"):
            v = stripped[len("- path_contains:"):].strip().strip('"')
            in_or.append({"path_contains": v})
            continue

        if stripped.startswith("- path_contains:"):
            v = stripped[len("- path_contains:"):].strip().strip('"')
            if in_expect_any is not None:
                in_expect_any.append({"path_contains": v})
            continue
        if stripped.startswith("- or:"):
            in_or = []
            in_expect_any = in_expect_any or []
            in_expect_any.append({"or": in_or})
            continue

        # key: value
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            k = k.strip()
            v = v.strip()
            if v == "":
                # Block — next lines belong
                if k == "expect_any":
                    in_expect_any = []
                    cur[k] = in_expect_any
                    in_or = None
                continue
            if v.startswith("[") and v.endswith("]"):
                # inline list
                items = [x.strip().strip('"\'') for x in v[1:-1].split(",") if x.strip()]
                cur[k] = items
            elif v.isdigit():
                cur[k] = int(v)
            elif v.lstrip("-").isdigit():
                cur[k] = int(v)
            else:
                cur[k] = v.strip('"\'')

    if cur:
        cases.append(cur)
    return {"cases": cases}


def check_case(c: CorpusSearchClient, case: dict) -> tuple[bool, str]:
    query = case["query"]
    source = case.get("source", "")
    sources = case.get("sources", [])
    year_from = str(case.get("year_from", ""))
    year_to = str(case.get("year_to", ""))
    top = int(case.get("expect_top", 1))
    min_score = float(case.get("min_score", -50))

    hits = c.search(
        query=query, source=source,
        sources=sources if isinstance(sources, list) and sources else None,
        year_from=year_from, year_to=year_to, limit=top,
    )
    if not hits:
        return False, "0 hits"
    paths = [h.path for h in hits]
    expect = case.get("expect_any", [])
    matched = []
    for cond in expect:
        if "path_contains" in cond:
            substr = cond["path_contains"]
            for p in paths:
                if substr in p:
                    matched.append(substr)
                    break
        elif "or" in cond:
            for alt in cond["or"]:
                if "path_contains" in alt:
                    substr = alt["path_contains"]
                    for p in paths:
                        if substr in p:
                            matched.append(f"or:{substr}")
                            break
                    if any(f"or:{alt['path_contains']}" == m for m in matched):
                        break

    if not matched and expect:
        return False, f"none of {[c.get('path_contains','or') for c in expect]} in top {top}: {[p[-40:] for p in paths]}"

    if hits[0].score < min_score:
        return False, f"top score {hits[0].score:.1f} < {min_score}"

    return True, f"matched={matched} top_score={hits[0].score:.1f}"


def main() -> int:
    if not _YAML.exists():
        print(f"FAIL: missing {_YAML}")
        return 2
    data = parse_yaml_lite(_YAML.read_text(encoding="utf-8"))
    cases = data.get("cases", [])

    c = CorpusSearchClient()
    print(f"\n{'='*70}")
    print(f"Golden test suite — {len(cases)} cases")
    print(f"{'='*70}\n")
    passed = 0
    for case in cases:
        cid = case.get("id", "(no id)")
        try:
            ok, msg = check_case(c, case)
        except Exception as e:
            ok, msg = False, f"EXCEPTION: {type(e).__name__}: {e}"
        flag = "✅" if ok else "❌"
        print(f"  {flag} {cid:40s} {msg}")
        if ok:
            passed += 1

    print(f"\n{'='*70}")
    print(f"{passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
