#!/bin/bash
# Actualización INCREMENTAL del árbol normativo tras el refresh de fuentes.
# Procesa solo los considerandos/sentencias nuevos (cursor por max rowid) → citas →
# resuelve → re-materializa tablas → re-cluster de las keys tocadas. NO re-hace el histórico.
# Pensado para correr semanal tras refresh-downstream.sh. Cómputo en enigma (túnel).
set -u
cd "/Volumes/SSD ADA/claude-for-legal-chile/chile"
DB=data/_index/citas_normativas.sqlite3
LOG(){ echo "$(TZ=America/Santiago date '+%F %H:%M') CLT · $*"; }

LOG "=== refresh árbol normativo (incremental) ==="

# (1) extraer citas de considerandos nuevos (extract-citas-normativas es reanudable por rango
#     rowid vía citas_progreso → solo procesa los rangos nuevos del corpus). Mismo para admin.
LOG "(1) extracción incremental de citas (judicial + administrativa)"
python3 scripts/extract-citas-normativas.py || true
python3 scripts/extract-citas-admin.py || true

# (2) resolver las citas nuevas (id_norma NULL) — el resolver es idempotente por par (tipo,cuerpo)
LOG "(2) resolución a id_norma (judicial + admin)"
python3 scripts/resolve-citas-normativas.py || true
python3 scripts/resolve-citas-normativas.py --table citas_admin || true

# (3) fechas de sentencias nuevas (build-sentencias-fechas es reanudable por página)
LOG "(3) fechas de sentencias nuevas"
python3 scripts/build-sentencias-fechas.py || true

# (4) re-materializar tablas del árbol (rápido; reflejan el delta)
LOG "(4) re-materializar arbol_mat / temporal / jerarquia / admin / doc_fechas"
python3 - <<'PY'
import sqlite3
con=sqlite3.connect("data/_index/citas_normativas.sqlite3", timeout=300)
con.execute("DROP TABLE IF EXISTS doc_fechas")
con.execute("CREATE TABLE doc_fechas AS WITH d AS (SELECT DISTINCT doc_path, substr(doc_path,instr(doc_path,'/')+1) s1 FROM citas), d2 AS (SELECT doc_path, replace(substr(s1,instr(s1,'/')+1),'.txt','') stem FROM d) SELECT d2.doc_path,f.fecha,f.rol,f.era,f.sala,f.caratulado,f.tribunal FROM d2 JOIN sentencias_fechas f ON f.sent_id=d2.stem")
con.execute("CREATE INDEX idx_docfechas ON doc_fechas(doc_path)")
for s in [
 "DROP TABLE IF EXISTS arbol_mat",
 "CREATE TABLE arbol_mat AS SELECT id_norma,articulo,count(DISTINCT doc_path) n_sentencias,count(*) n_citas FROM citas WHERE id_norma IS NOT NULL GROUP BY id_norma,articulo",
 "CREATE INDEX idx_arbolmat ON arbol_mat(id_norma,articulo)",
 "DROP TABLE IF EXISTS arbol_temporal_mat",
 "CREATE TABLE arbol_temporal_mat AS SELECT c.id_norma,c.articulo,substr(df.fecha,1,4) anio,count(DISTINCT c.doc_path) n_sentencias,count(*) n_citas FROM citas c JOIN doc_fechas df USING(doc_path) WHERE c.id_norma IS NOT NULL GROUP BY c.id_norma,c.articulo,anio",
 "CREATE INDEX idx_arboltmat ON arbol_temporal_mat(id_norma,articulo)",
 "DROP TABLE IF EXISTS arbol_jerarquia_mat",
 "CREATE TABLE arbol_jerarquia_mat AS SELECT id_norma,articulo,count(DISTINCT CASE WHEN doc_path LIKE 'pjud/Corte_Suprema/%' THEN doc_path END) n_suprema,count(DISTINCT CASE WHEN doc_path NOT LIKE 'pjud/Corte_Suprema/%' THEN doc_path END) n_instancia FROM citas WHERE id_norma IS NOT NULL AND articulo!='' AND source LIKE 'pjud%' GROUP BY id_norma,articulo",
 "CREATE INDEX idx_jerarquia ON arbol_jerarquia_mat(id_norma,articulo)",
 "DROP TABLE IF EXISTS arbol_admin_mat",
 "CREATE TABLE arbol_admin_mat AS SELECT id_norma,articulo,source,count(DISTINCT doc_path) n_docs,count(*) n_citas FROM citas_admin WHERE id_norma IS NOT NULL GROUP BY id_norma,articulo,source",
 "CREATE INDEX idx_arboladmin ON arbol_admin_mat(id_norma,articulo)",
 "PRAGMA wal_checkpoint(TRUNCATE)",
]:
    con.execute(s)
con.commit(); print("tablas OK")
PY

# (5) ventanas + embeddings de las citas nuevas, y re-cluster de keys tocadas
#     (extract-citas-windows reanudable por rango; embed-windows reanudable por progress)
LOG "(5) ventanas + embeddings + re-cluster de keys nuevas → corre en ENIGMA"
echo "    NOTA: pasos 5-6 (embed ventanas nuevas + recluster) se ejecutan en enigma con"
echo "    scripts/embed-windows.py (reanudable) y scripts/recluster-keys.py sobre las keys"
echo "    con citas nuevas. Disparar tras este script con el túnel TEI/Ollama activo."

# (6) sync a enigma + reload backend
LOG "(6) sync citas DB a enigma + reload backend"
rsync -a --inplace --partial -e "ssh -o ServerAliveInterval=30" "$DB" antonio@10.0.0.3:/home/antonio/lc-index/ \
  && ssh antonio@10.0.0.3 'docker restart app-backend-1' \
  && LOG "=== árbol actualizado y servido ===" \
  || LOG "!!! error en sync/reload — revisar"
