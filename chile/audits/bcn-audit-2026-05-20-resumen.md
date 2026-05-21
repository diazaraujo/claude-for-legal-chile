---
audit_fecha: 2026-05-20
audit_tipo: transversal contra BCN/LeyChile (con MVP mcp-bcn-leychile)
total_perfiles: 156 (capa 3)
discrepancias_detectadas: 72 (46%)
exit_code_check: 1
estado: crítico — requiere decisión maintainer
---

# Audit transversal contra BCN — Resumen

## TL;DR

**El 46% (72/156) de los perfiles capa 3 tiene URLs BCN incorrectas.**
Las URLs apuntan a normas distintas a las declaradas. Esto es
**resultado de la generación heurística del corpus sin verificación
contra fuente**.

El catálogo capa 1 (4.921 leyes scrapeadas de BCN/SPARQL) contiene
los IDs correctos para **32 de los 72** perfiles con discrepancia.
Los **40 restantes** requieren re-scrape específico o búsqueda manual.

## Distribución del problema

| Status | Count | % |
|---|---|---|
| URLs correctas (OK contra BCN) | 84 | 54% |
| Discrepancia con corrección en catálogo capa 1 | 32 | 21% |
| Discrepancia sin match en catálogo (pendiente manual) | 40 | 25% |

## Ejemplos críticos detectados

### Errores de bandera publicitaria

| Perfil | Norma declarada | URL apunta a | Severidad |
|---|---|---|---|
| `ley-21400-matrimonio-igualitario` | Ley 21.400 Matrimonio Igualitario | "RECONOCE HUMEDAL URBANO DE LINARES" (Dec 1183 Ex) | CRÍTICO |
| `ley-21643-acoso-laboral` | Ley 21.643 (Ley Karin) | "MODIFICA DECRETO SUPREMO Nº 53 DE 2011" (Dec 124) | CRÍTICO |
| `ley-21719-modificacion-lpd` | Ley 21.719 Reforma LPD | "AUTORIZA COMERCIALIZACIÓN PRODUCTOS DE TABACO" (Dec 1432 Ex) | CRÍTICO |

### Discrepancias con sugerencia válida del catálogo

| Perfil | ID actual | ID catálogo capa 1 |
|---|---|---|
| `ley-18695-loc-municipalidades` | 251693 | 30077 |
| `ley-18834-estatuto-administrativo` | 236392 | 30210 |
| `ley-19070-estatuto-docente` | 60439 | 30437 |
| `ley-21435-reforma-codigo-aguas` | 1175131 | 1174443 |
| `ley-21057-entrevista-videograbada` | 1115208 | 1113932 |
| ... 27 más | | |

### Pendientes manual (gaps del catálogo)

40 perfiles cuyo número (Ley 21.400, 21.643, etc.) no está en el catálogo
capa 1. Requieren:

- Re-scrape específico de BCN.
- O búsqueda manual por título en BCN.

Mayoría son **leyes recientes** (2018+) + algunos **DLs/DFLs antiguos**.

## Por qué ocurrió

El corpus capa 3 fue **generado heurísticamente** asumiendo IDs BCN sin
verificar. La hipótesis del generador (yo, Claude) fue que los IDs BCN
seguían un patrón cronológico predictible. **El patrón no es
predictible** — BCN asigna IDs por sistema interno, no por número de ley.

El catálogo capa 1 sí tiene IDs reales (vino de scrape BCN/SPARQL).
Pero el generador de perfiles capa 3 NO consultó el catálogo capa 1
al construir el frontmatter.

## Decisión maintainer requerida

### Opción A — Auto-aplicar 32 correcciones del catálogo

- Aplicar las 32 correcciones donde el catálogo capa 1 tiene el ID
  correcto.
- Re-correr check-bcn-urls para confirmar.
- Documentar 40 pendientes como TODO.
- **Pros**: 32 perfiles correctos inmediatos.
- **Contras**: algunos de los 32 pueden ser falsos matches
  (ej. `dfl-2-1998` vs `dfl-2-2009` ambos matchean el mismo
  archivo del catálogo).

### Opción B — Re-scrape antes de auto-aplicar

- Re-correr `scripts/bcn/scrape-catalogo.py` para completar gaps.
- Después aplicar correcciones validadas contra BCN.
- **Pros**: cobertura completa.
- **Contras**: requiere BCN responder; 2-3 horas adicionales.

### Opción C — Esperar validación legal

- No tocar las URLs hasta que un validador legal revise.
- **Pros**: máxima seguridad.
- **Contras**: lock-out de adopción del corpus hasta validador.

## Recomendación

**Opción A con guardrails**:

1. Auto-aplicar las 32 correcciones EXCEPTO para slugs `dfl-N-AÑO-*`
   que requieren desambiguación por año.
2. Marcar los 40 pendientes con `[VERIFICAR URL BCN]` en el cuerpo.
3. Re-correr check-bcn-urls + commit.
4. PR separado con título "fix(urls): corrige IDs BCN según catálogo
   capa 1" para que el validador revise antes de mergear a main.

## Archivos

- `chile/audits/bcn-audit-2026-05-20.log` — log completo del audit
  (214s, 156 perfiles).
- `chile/audits/bcn-suggestions-2026-05-20.log` — sugerencias del
  catálogo (32) + pendientes-manual (66 entradas incluyendo
  duplicados por tipo).
- `chile/scripts/audit/check-bcn-urls.py` — script de verificación.
- `chile/scripts/audit/suggest-bcn-urls.py` — script de sugerencias.
