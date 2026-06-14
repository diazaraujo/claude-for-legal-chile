# Tests del árbol normativo — regresión

`python3 -m pytest tests/ -q` (requiere `pip install pytest`).

- **test_extractor_citas.py** — unidad del extractor (siempre corre, sin DB). Blinda:
  truncamiento de nombres de código, parsing de listas de artículos, tipos ley/DL/DFL/CPR/código.
- **test_arbol_consistencia.py** — invariantes sobre `data/_index/citas_normativas.sqlite3`
  (skip si no está la DB). Blinda los bugs corregidos: resoluciones canónicas (Código Penal→1984,
  CPR→242302, COT→13755), 0 citas de código a normas modificatorias, precisión de resolución ≥97%,
  jerarquía/temporal/arbol_mat coherentes.

Correr tras cada `refresh-arbol.sh` o cambio en el extractor/resolver.
