#!/bin/bash
# DOWNSTREAM del refresh: tras bajar el delta de las fuentes, procesa SOLO lo nuevo.
# (1) embed delta (bge-m3 enigma; embed-loop auto-descubre data/*/ y skip lo embebido)
# (2) embed concursal nuevo  (3) LLM extract pjud nuevo (idempotente vía *_done/_resultado)
# (4) re-agregar perfiles  (5) regenerar coverage map + audit. Cómputo pesado = ENIGMA (túnel 11435).
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
GEN="http://localhost:11435/api/generate"; EMB="http://localhost:11435/api/embed"
# túnel enigma vivo
curl -s --max-time 8 localhost:11435/api/tags >/dev/null || { unset SSH_AUTH_SOCK; nohup ssh -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -L 11435:localhost:11434 antonio@10.0.0.3 >/tmp/tunnel-enigma.log 2>&1 & sleep 5; }

echo "=== (1) EMBED delta de fuentes nuevas (embed-loop, una pasada) ==="
OLLAMA_EMBED_URL="$EMB" timeout 7200 bash -c 'for d in data/*/; do n=$(basename "$d"); [ "$n" = "_index" ] && continue; for ext in txt html htm pdf xml; do [ -n "$(find "$d" -name "*.$ext" -print -quit 2>/dev/null)" ] && OLLAMA_EMBED_URL="'"$EMB"'" python3 scripts/embed-new-source.py --src "$d" --glob "*.$ext" --source "$n" --batch 16 --workers 6; done; done' || true

echo "=== (2) EMBED concursal nuevo ==="
OLLAMA_EMBED_URL="$EMB" python3 scripts/embed-concursal.py --batch 64 || true

echo "=== (3) LLM extract PJUD nuevo (partes + resultado laboral/penal; idempotente) ==="
OLLAMA_GEN_URL="$GEN" FASE1_MODEL="qwen2.5:14b" python3 scripts/perfiles/extract-laboral-resultado.py --workers 6 || true
OLLAMA_GEN_URL="$GEN" FASE1_MODEL="llama3.1:8b" python3 scripts/perfiles/extract-penal-resultado.py --workers 8 || true
# FASE1 partes: descomentar cuando laboral/penal estén al día
# OLLAMA_GEN_URL="$GEN" FASE1_MODEL="qwen2.5:14b" python3 scripts/extract-partes/fase1-llm.py --all --workers 6 || true

echo "=== (4) RE-AGREGAR perfiles (jueces/empresas/tribunales) ==="
python3 scripts/perfiles/aggregate-empresas-laboral.py --min-juicios 1 || true
python3 scripts/perfiles/aggregate-jueces.py --min-causas 5 || true

echo "=== (5) VERIFICACIÓN: coverage map + audit embeddings ==="
python3 scripts/generate-coverage-map.py || true
python3 scripts/audit-embeddings.py | tail -20 || true
echo "=== DOWNSTREAM completo · $(date '+%H:%M:%S') ==="
