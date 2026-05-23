#!/usr/bin/env python3
"""Test E2E de mcp-corpus-search vía stdio JSON-RPC.

Lanza el server real como subprocess, envía initialize + tools/list +
tools/call y verifica respuestas. Cubre el surface MCP, no solo
el client Python interno.
"""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
MCP_BIN = _SCRIPTS / "mcp-corpus-search/.venv/bin/mcp-corpus-search"


def _send(proc: subprocess.Popen, msg: dict) -> None:
    line = json.dumps(msg, ensure_ascii=False) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()


def _read_until(proc: subprocess.Popen, want_id: int, timeout: float = 5) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            continue
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("id") == want_id:
            return d
    return None


def main() -> int:
    if not MCP_BIN.exists():
        print(f"FAIL: MCP binary no existe: {MCP_BIN}")
        return 1

    proc = subprocess.Popen(
        [str(MCP_BIN)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, bufsize=1,
    )

    fails = 0
    try:
        # 1. Initialize
        _send(proc, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smoke", "version": "0"},
            },
        })
        r = _read_until(proc, 1)
        if not r or "result" not in r:
            print("FAIL: initialize"); fails += 1
        else:
            print(f"PASS: initialize → {r['result']['serverInfo']['name']}")

        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        time.sleep(0.2)

        # 2. tools/list
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        r = _read_until(proc, 2)
        if not r or "tools" not in r.get("result", {}):
            print("FAIL: tools/list"); fails += 1
        else:
            tools = [t["name"] for t in r["result"]["tools"]]
            expected = {
                "corpus_search", "corpus_recent", "corpus_list_sources",
                "corpus_stats", "corpus_get_text", "corpus_cite",
                "corpus_related", "corpus_embeddings_status",
            }
            missing = expected - set(tools)
            if missing:
                print(f"FAIL: tools/list missing {missing}"); fails += 1
            else:
                print(f"PASS: tools/list → 8/8 ({', '.join(tools)})")

        # 3. corpus_stats
        _send(proc, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "corpus_stats", "arguments": {}},
        })
        r = _read_until(proc, 3, timeout=10)
        if r and r.get("result", {}).get("content"):
            text = r["result"]["content"][0]["text"]
            d = json.loads(text)
            total = d.get("total_docs", 0)
            if total > 0:
                print(f"PASS: corpus_stats → {total} docs")
            else:
                print("FAIL: corpus_stats total=0"); fails += 1
        else:
            print("FAIL: corpus_stats"); fails += 1

        # 4. corpus_cite
        _send(proc, {
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {
                "name": "corpus_cite",
                "arguments": {"path": "chile/data/tc-moderno/STC_Rol_N_17_083-25_INA.pdf.txt"},
            },
        })
        r = _read_until(proc, 4, timeout=5)
        if r and r.get("result", {}).get("content"):
            d = json.loads(r["result"]["content"][0]["text"])
            if "17.083-2025" in d.get("citation", ""):
                print(f"PASS: corpus_cite → {d['citation']}")
            else:
                print(f"FAIL: corpus_cite wrong format: {d.get('citation')}"); fails += 1
        else:
            print("FAIL: corpus_cite"); fails += 1

        # 5. corpus_search
        _send(proc, {
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {
                "name": "corpus_search",
                "arguments": {"query": "huelga ilegal", "limit": 2},
            },
        })
        r = _read_until(proc, 5, timeout=10)
        if r and r.get("result", {}).get("content"):
            d = json.loads(r["result"]["content"][0]["text"])
            n = d.get("n_hits", 0)
            if n > 0:
                print(f"PASS: corpus_search 'huelga ilegal' → {n} hits, "
                      f"top score={d['results'][0]['score']:.2f}")
            else:
                print("FAIL: corpus_search 0 hits"); fails += 1
        else:
            print("FAIL: corpus_search"); fails += 1

    finally:
        proc.terminate()
        proc.wait(timeout=3)

    print(f"\n{'PASS' if fails == 0 else 'FAIL'}: stdio E2E ({fails} fails)")
    return fails


if __name__ == "__main__":
    sys.exit(main())
