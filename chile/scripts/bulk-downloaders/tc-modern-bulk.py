#!/usr/bin/env python3
"""Bulk TC moderno — sentencias post-2018 vía tramitacion.tcchile.cl.

Endpoint público:
  POST /tc/rest/causa/listSetenciasByFilter (JSON body: {"filter": "ultimosIngresos"})
  → últimas 50 sentencias con tramite_documento (PDF ID).
  GET /tc/download/{tramite_documento}?inlineifpossible=true
  → PDF real (requiere session cookie del dashboard).

Limitación: el endpoint público solo expone los últimos 50. Para
histórico completo se necesitarían credenciales TC (do_search requiere
login + reCAPTCHA).

Strategy del script:
- Modo "recientes" (default): baja los 50 últimos sin auth.
- Modo "brute" (opcional): enumera tramite_documento IDs en un rango
  con la session activa — válido para los IDs que TC mantiene públicos.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys, time, re
from pathlib import Path
from playwright.sync_api import sync_playwright

_REPO_ROOT = Path(__file__).resolve().parents[3]
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sentencias_modernas ("
        "tramite_documento INTEGER PRIMARY KEY, "
        "causa_rol TEXT, causa_id INTEGER, "
        "procedimiento_iniciales TEXT, "
        "fecha TEXT, caratula TEXT, "
        "downloaded INTEGER DEFAULT 0, pdf_size INTEGER, filename TEXT)"
    )
    conn.commit()
    return conn


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", s)[:200]


def bulk_recientes(output_dir: Path, db_path: Path) -> int:
    conn = init_manifest(db_path)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, accept_downloads=True)
        page = context.new_page()

        # Establish session
        print("Estableciendo sesión TC...", flush=True)
        page.goto(
            "https://tramitacion.tcchile.cl/tc/sentencias?filter=ultimosIngresos",
            wait_until="networkidle", timeout=60000,
        )
        page.wait_for_timeout(3000)

        # Fetch the list of sentencias
        print("Obteniendo listado...", flush=True)
        sentencias = page.evaluate("""
            async () => {
                const r = await fetch('/tc/rest/causa/listSetenciasByFilter', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json; charset=utf-8',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({filter: 'ultimosIngresos'}),
                });
                const j = await r.json();
                return j.results || [];
            }
        """)
        print(f"  {len(sentencias)} sentencias en feed público", flush=True)

        # Insert into manifest
        for s in sentencias:
            conn.execute(
                "INSERT OR IGNORE INTO sentencias_modernas("
                "tramite_documento, causa_rol, causa_id, procedimiento_iniciales, "
                "fecha, caratula) VALUES (?, ?, ?, ?, ?, ?)",
                (s["tramite_documento"], s.get("causa_rol", ""), s.get("causa_id"),
                 s.get("procedimiento_iniciales", ""), s.get("tramite_sentencia", ""),
                 s.get("causa_caratula", "")),
            )
        conn.commit()

        # Download each PDF
        pending = [s for s in sentencias if conn.execute(
            "SELECT downloaded FROM sentencias_modernas WHERE tramite_documento=?",
            (s["tramite_documento"],)
        ).fetchone()[0] == 0]
        print(f"\nDescargando {len(pending)} PDFs...", flush=True)

        ok, err = 0, 0
        bytes_total = 0
        for i, s in enumerate(pending, 1):
            doc_id = s["tramite_documento"]
            try:
                # Use page.expect_download to capture the PDF
                with page.expect_download(timeout=30000) as dl_info:
                    page.evaluate(f"""
                        () => {{
                            const a = document.createElement('a');
                            a.href = '/tc/download/{doc_id}?inlineifpossible=false';
                            a.download = 'tc.pdf';
                            document.body.appendChild(a);
                            a.click();
                        }}
                    """)
                dl = dl_info.value
                fname = dl.suggested_filename or f"tc_{doc_id}.pdf"
                fname = safe_name(fname)
                dest = output_dir / fname
                dl.save_as(str(dest))
                size = dest.stat().st_size
                conn.execute(
                    "UPDATE sentencias_modernas SET downloaded=1, pdf_size=?, "
                    "filename=? WHERE tramite_documento=?",
                    (size, fname, doc_id),
                )
                conn.commit()
                ok += 1
                bytes_total += size
                if i % 5 == 0 or i == len(pending):
                    print(f"  [{i}/{len(pending)}] ok={ok} err={err} | "
                          f"{bytes_total/1024/1024:.0f} MB", flush=True)
            except Exception as e:
                err += 1
                print(f"  doc {doc_id}: ERR {type(e).__name__}: {str(e)[:60]}",
                      flush=True)

        browser.close()
    print(f"\n[DONE] ok={ok}, err={err}, {bytes_total/1024/1024:.0f} MB", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/tc-moderno"))
    parser.add_argument("--mode", default="recientes",
                        choices=["recientes", "brute"])
    parser.add_argument("--from-id", type=int, default=400000)
    parser.add_argument("--to-id", type=int, default=460000)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"

    if args.mode == "recientes":
        return bulk_recientes(output_dir, db_path)

    print("Brute mode no implementado todavía (necesita session loop + retry)",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
