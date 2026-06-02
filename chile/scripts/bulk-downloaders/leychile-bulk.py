#!/usr/bin/env python3
"""Bulk LeyChile XML — texto íntegro de las normas chilenas.

Itera todos los archivos en `chile/normativa/catalogo/{tipo}/*.md`,
extrae `leychile_code` del frontmatter, y descarga el XML estructurado
desde:

  https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma={N}

Output: `chile/data/leychile/{tipo}/{idNorma}.xml`

XML contiene texto íntegro de cada artículo + estructura jerárquica
(libros, títulos, capítulos, artículos, incisos). Esquema BCN
EsquemaIntercambioNorma-v1-0.xsd.

Reglamentos: tipo `dto` (decreto supremo) en el catálogo. Hay 20.546
decretos catalogados — incluye todos los reglamentos vigentes que
implementan leyes.

Idempotente: skip si el XML ya existe y tiene >100 bytes.
"""
from __future__ import annotations
import argparse, base64, json, os, sqlite3, sys, time, urllib.error, urllib.request, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

_REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = _REPO_ROOT / "chile/normativa/catalogo"
USER_AGENT = "claude-legal-chile/0.7 (unholster.com)"
BASE_URL = "https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma="
BCN_BASE_URL = "https://www.bcn.cl/leychile/Consulta/obtxml?opt=7&idNorma="
ZYTE_API = "https://api.zyte.com/v1/extract"
_STATS = {"ok": 0, "skip": 0, "404": 0, "err": 0, "stub": 0, "ban": 0, "bytes": 0}
_LOCK = Lock()
# Per-thread rate limiter
from threading import local as _threadlocal
_RATE = _threadlocal()
_GLOBAL_BACKOFF = {"until": 0.0}  # epoch s — pause-all-workers señal


def _rate_wait(seconds: float) -> None:
    """Sleep al menos `seconds` desde la última request en este thread."""
    now = time.time()
    # Global backoff (si Zyte está banneando, todos esperan)
    with _LOCK:
        until = _GLOBAL_BACKOFF["until"]
    if until > now:
        time.sleep(until - now)
    last = getattr(_RATE, "last", 0.0)
    wait = seconds - (time.time() - last)
    if wait > 0:
        time.sleep(wait)
    _RATE.last = time.time()

CODE_RE = re.compile(r"^leychile_code:\s*(\d+)\s*$", re.MULTILINE)
PUBL_RE = re.compile(r"^publicacion:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)


def init_manifest(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS normas ("
        "id_norma INTEGER PRIMARY KEY, tipo TEXT, slug TEXT, "
        "publicacion TEXT, downloaded INTEGER DEFAULT 0, size INTEGER, "
        "status TEXT)"
    )
    conn.commit()
    return conn


def enumerate_catalog() -> list[tuple[int, str, str, str]]:
    """Yields (id_norma, tipo, slug, publicacion) for each catalog entry."""
    results: list[tuple[int, str, str, str]] = []
    if not CATALOG.exists():
        return results
    for tipo_dir in sorted(CATALOG.iterdir()):
        if not tipo_dir.is_dir():
            continue
        tipo = tipo_dir.name
        for md in tipo_dir.glob("*.md"):
            try:
                head = md.read_text(encoding="utf-8", errors="replace")[:4000]
            except Exception:
                continue
            m_code = CODE_RE.search(head)
            if not m_code:
                continue
            m_pub = PUBL_RE.search(head)
            results.append((
                int(m_code.group(1)), tipo, md.stem,
                m_pub.group(1) if m_pub else "",
            ))
    return results


def _is_valid_xml(body: bytes) -> bool:
    """XML real BCN. Rechaza stubs HTML 'Este sitio fue movido'."""
    head = body.lstrip()
    return (
        (head.startswith(b"<?xml") or head.startswith(b"<Norma"))
        and b"sitio fue movido" not in body
        and b"window.location.href" not in head[:300]
    )


# 🥇 ROTACIÓN DE GEOLOCALIZACIONES (regla de oro persistencia anti-ban):
# si una geo da 520 (Website Ban del WAF de BCN), probar la siguiente, y así.
# NUNCA usar CL (BCN banea IPs chilenas). Orden por confiabilidad medida.
GEO_ROTATION = ["US", "AR", "CA", "GB", "DE", "BR", "MX", "FR", "ES", "NL", "IT", "PL"]

def _fetch_zyte(url: str, zyte_auth: str, geo: str, timeout: int = 25) -> bytes:
    payload = {"url": url, "httpResponseBody": True, "geolocation": geo}
    req = urllib.request.Request(
        ZYTE_API, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Basic {zyte_auth}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    body_b64 = data.get("httpResponseBody", "")
    return base64.b64decode(body_b64) if body_b64 else b""


_RAW_CAP = 25  # muestras raw por categoría — evidencia de QUÉ bajamos, sin guardar 46k copias
def _save_raw(dest: Path, status: str, body: bytes | None) -> None:
    """Guarda una muestra acotada del cuerpo crudo de respuestas fallidas (stub/tiny)
    en data/leychile/_raw/, para poder inspeccionar EXACTAMENTE qué devolvió la fuente.
    Acotado a _RAW_CAP por categoría para no inflar el disco."""
    try:
        key = f"_raw_{status}"
        with _LOCK:
            n = _STATS.get(key, 0)
            if n >= _RAW_CAP:
                return
            _STATS[key] = n + 1
        raw_dir = dest.parent.parent / "_raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{status}-{dest.stem}.bin").write_bytes(body or b"")
    except Exception:
        pass


def download_xml(
    id_norma: int,
    dest: Path,
    zyte_auth: str | None = None,
    rate_seconds: float = 1.0,
    max_retries: int = 1,
) -> str:
    if dest.exists() and dest.stat().st_size > 500:
        with _LOCK: _STATS["skip"] += 1
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # 🥇 Persistencia anti-ban: si zyte, rotar por TODAS las geos en GEO_ROTATION
    # ante un 520; solo se declara "ban" si TODAS las geos fallan. Sin zyte, directo.
    geos = GEO_ROTATION if zyte_auth else [None]
    for attempt in range(max_retries + 1):
        _rate_wait(rate_seconds)
        try:
            body = None
            if zyte_auth:
                last_ban = False
                for geo in geos:                     # rotación de geolocalizaciones
                    try:
                        body = _fetch_zyte(BCN_BASE_URL + str(id_norma), zyte_auth, geo)
                        last_ban = False
                        break
                    except urllib.error.HTTPError as e:
                        if e.code == 520:             # ban en esta geo → siguiente
                            last_ban = True; continue
                        raise
                if body is None:                      # todas las geos baneadas
                    with _LOCK: _STATS["ban"] += 1
                    return "ban"
            else:
                req = urllib.request.Request(
                    BCN_BASE_URL + str(id_norma),
                    headers={"User-Agent": USER_AGENT},
                )
                with urllib.request.urlopen(req, timeout=30) as r:
                    body = r.read()

            if not _is_valid_xml(body):
                _save_raw(dest, "stub", body)   # copia raw para depurar "¿por qué stub?"
                with _LOCK: _STATS["stub"] += 1
                return "stub"
            if len(body) < 500:
                _save_raw(dest, "tiny", body)
                with _LOCK: _STATS["err"] += 1
                return "tiny"
            tmp = dest.with_suffix(".tmp")
            tmp.write_bytes(body)
            tmp.rename(dest)
            with _LOCK:
                _STATS["ok"] += 1
                _STATS["bytes"] += len(body)
            return "ok"

        except urllib.error.HTTPError as e:
            if e.code == 404:
                with _LOCK: _STATS["404"] += 1
                return "404"
            with _LOCK: _STATS["err"] += 1
            return f"http{e.code}"
        except Exception:
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            with _LOCK: _STATS["err"] += 1
            return "err"
    return "err"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_REPO_ROOT / "chile/data/leychile"))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--tipos", default="",
                        help="Comma-separated (default: todos). "
                             "Ej: 'ley,dto,dfl,dl,cod' para core normativo.")
    parser.add_argument("--max", type=int, default=0,
                        help="Limit total downloads (0 = unlimited)")
    parser.add_argument("--zyte", action="store_true",
                        help="Usar Zyte API (bypassa CloudFront WAF de BCN). "
                             "Requiere env ZYTE_API_KEY")
    parser.add_argument("--rate-seconds", type=float, default=1.0,
                        help="Sleep mínimo per-worker entre requests (default 1s). "
                             "Sube a 2-3s si Zyte devuelve 520 bans en cascada.")
    args = parser.parse_args()

    zyte_auth = None
    if args.zyte:
        key = os.environ.get("ZYTE_API_KEY", "")
        if not key:
            print("ERROR: --zyte requiere env ZYTE_API_KEY", flush=True)
            return 2
        zyte_auth = base64.b64encode(f"{key}:".encode()).decode()
        print(f"[ZYTE] proxy habilitado (browser-grade)", flush=True)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "manifest.sqlite3"
    conn = init_manifest(db_path)

    print("[FASE 1] Enumerando catálogo BCN...", flush=True)
    entries = enumerate_catalog()
    if args.tipos:
        wanted = set(args.tipos.split(","))
        entries = [e for e in entries if e[1] in wanted]
    # Reverse chronological: más recientes primero
    entries.sort(key=lambda x: (x[3] or "0000", x[0]), reverse=True)
    print(f"  Total: {len(entries)} normas a procesar", flush=True)

    # Insert into manifest
    for id_norma, tipo, slug, pub in entries:
        conn.execute(
            "INSERT OR IGNORE INTO normas(id_norma, tipo, slug, publicacion) "
            "VALUES (?, ?, ?, ?)",
            (id_norma, tipo, slug, pub),
        )
    conn.commit()

    # Excluir status TERMINALES (norma movida/inexistente) para no re-molerlos en
    # cada run. stub/404/http4xx no van a bajar nunca como XML → fuera de la cola.
    # Reintentables: status NULL (nunca tocado) + err/ban/tiny/http5xx (transitorios).
    def _terminal(st):
        return st in ("stub", "404") or (st or "").startswith("http4")
    pending = []
    for e in entries:
        row = conn.execute("SELECT downloaded, status FROM normas WHERE id_norma=?",
                           (e[0],)).fetchone() or (0, None)
        if row[0] == 0 and not _terminal(row[1]):
            pending.append(e)
    if args.max > 0:
        pending = pending[:args.max]
    print(f"\n[FASE 2] Descargando {len(pending)} XMLs...", flush=True)
    if not pending:
        return 0

    def worker(item):
        id_norma, tipo, slug, pub = item
        dest = output_dir / tipo / f"{id_norma}.xml"
        status = download_xml(
            id_norma, dest, zyte_auth=zyte_auth,
            rate_seconds=args.rate_seconds,
        )
        # Persistir SIEMPRE el status (no solo ok/skip): así los terminales
        # (stub/404/http4xx) quedan registrados y salen de la cola para siempre.
        done = 1 if status in ("ok", "skip") else 0
        c = sqlite3.connect(str(db_path), timeout=30)
        try:
            size = dest.stat().st_size if (done and dest.exists()) else 0
            c.execute(
                "UPDATE normas SET downloaded=?, size=?, status=? "
                "WHERE id_norma=?", (done, size, status, id_norma),
            )
            c.commit()
        finally:
            c.close()
        return id_norma, status

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(worker, item) for item in pending]
        for i, fut in enumerate(as_completed(futures), 1):
            try: fut.result()
            except Exception: pass
            if i % 200 == 0 or i == len(pending):
                mb = _STATS["bytes"] / 1024 / 1024
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i) / rate if rate > 0 else 0
                print(
                    f"  [{i}/{len(pending)}] ok={_STATS['ok']} skip={_STATS['skip']} "
                    f"stub={_STATS['stub']} ban={_STATS['ban']} "
                    f"404={_STATS['404']} err={_STATS['err']} | "
                    f"{mb:.0f} MB | rate={rate:.1f}/s eta={eta:.0f}s",
                    flush=True,
                )

    elapsed = time.time() - start
    print(
        f"\n[DONE] {elapsed:.0f}s | ok={_STATS['ok']} | "
        f"{_STATS['bytes']/1024/1024:.0f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
