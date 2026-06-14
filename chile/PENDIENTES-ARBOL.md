# Pendientes — árbol normativo legalchile

Estado: árbol en producción, consistente (npz=jsonl=arbol_mat=18.117), con tests de regresión.

## Abiertos (de la crítica de utilidad)

- [ ] **CI real para los tests de datos.** `tests/test_arbol_consistencia.py` hoy corre contra
  la copia local del Mac (skip si no hay DB). Para gate de CI: apuntarlos a la DB del entorno
  de CI o crear una **muestra fixture chica** (ej. 5k citas + normas_titulos reducida) versionada,
  y correr `pytest` en el pipeline de GitHub Actions. Los tests de extractor (unit) ya son CI-ready.

- [ ] **#9 Capa administrativa sin contenido.** Hoy muestra solo el conteo por organismo
  ("Contraloría: 298k docs"). Falta exponer QUÉ dictaminó: dictámenes de ejemplo con extracto +
  idealmente tesis administrativas (clustering de citas_admin análogo a las judiciales).

- [ ] **Cobertura temporal jurisprudencial.** PJUD indexado desde 2005; jurisprudencia anterior
  no está (límite de la fuente PJUD). Evaluar fuentes históricas si se requiere doctrina antigua.

- [ ] **Validación con abogado real.** Todo el diseño del árbol es hipótesis nuestra. Una sesión
  de 1h con un litigante usando /arbol revelaría más que semanas de features.

- [ ] **Sesgo léxico laboral en la entrada semántica.** Familia (custodia, alimentos) y términos
  genéricos ('daño') resuelven a Código del Trabajo porque pjud-laborales domina el corpus.
  Fix: re-ranking normalizado por volumen de fuente, o ampliar corpus de familia. (Hallazgo
  comparación A/B 13-jun, COMPARACION-SKILL.md)
- [ ] **Competidor: basejurisprudencial.cl** ofrece búsqueda semántica de fallos gratis.
  Diferenciar legalchile por el árbol normativo estructurado, no por la búsqueda semántica.

## Descartado por Antonio
- Dimensión temporal de la norma (qué redacción del artículo regía al dictarse cada fallo).
