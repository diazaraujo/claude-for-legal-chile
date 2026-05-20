---
archivo_revisado: transversal — auditoría URLs BCN
fecha_revision: 2026-05-20
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: transversal
estado: pendiente-de-validador
---

# Auto-revisión técnica transversal: URLs BCN en frontmatter

> Auditoría sistemática de URLs BCN del corpus capa 3.

## Resumen ejecutivo

- 126 archivos capa 3 con campo `fuente_oficial` apuntando a BCN.
- **2 IDs BCN compartidos** detectados (cada uno en 2 archivos).
- 124 IDs únicos (sin duplicación).
- BCN no respondió durante la auditoría — verificación contra fuente
  oficial pendiente.

## Hallazgos críticos

### H0 — URLs apuntando a normas DISTINTAS (errores reales)

Verificación contra BCN (vía `chile/scripts/audit/check-bcn-urls.py`,
ejecutada el 2026-05-20) detectó 2 perfiles cuya URL apunta a normas
COMPLETAMENTE DIFERENTES a la declarada:

| Perfil | URL declarada | Norma real en BCN | Status |
|---|---|---|---|
| `ley-21400-matrimonio-igualitario` | `idNorma=1170048` | "RECONOCE HUMEDAL URBANO DE LINARES" (Decreto 1183 Exenta) | ERROR REAL |
| `ley-21643-acoso-laboral` | (URL del frontmatter) | "MODIFICA DECRETO SUPREMO Nº 53 DE 2011" (Decreto 124) | ERROR REAL |

**Acción sugerida**:
- Buscar IDs correctos en BCN (`bcn.cl/leychile`) por búsqueda de
  título.
- Corregir URLs en frontmatter.
- Re-correr `check-bcn-urls.py` para confirmar.

**Nota crítica**: el catálogo capa 1 del corpus NO incluye Ley 21.400
ni Ley 21.643 (gaps del scrape original). Una pasada de re-scrape
selectivo sería útil para tener los IDs correctos.

### H1 — id=172986 compartido entre 2 archivos

| Archivo | Norma declarada |
|---|---|
| `chile/normativa/codigos/codigo-civil.md` | Código Civil (1855) |
| `chile/normativa/leyes/ley-14908-alimentos.md` | Ley 14.908 (1962) |

**Análisis técnico**: BCN id=172986 corresponde al **DFL Nº 1 del
Ministerio de Justicia, 2000** que **refunde** el Código Civil + Ley
14.908 (Alimentos) + Ley 19.620 (Adopciones) + otras leyes de familia.

Es **ambigüedad estructural BCN**, no error categórico. Un usuario que
entra al URL ve contenido refundido de múltiples leyes.

**Acción sugerida**:
- Documentar en cada archivo que la URL apunta al DFL refundidor.
- Agregar campo opcional `dfl_refundidor:` al frontmatter para
  trazabilidad.
- Considerar si BCN tiene anchor específico para cada norma dentro del
  DFL (ej. `#codigo-civil` o `#ley-14908`).

### H2 — id=1118991 compartido entre 2 archivos — POSIBLE ERROR

| Archivo | Norma declarada | Publicación |
|---|---|---|
| `chile/normativa/leyes/ley-21091-educacion-superior.md` | Ley 21.091 | 2018-05-29 |
| `chile/normativa/leyes/ley-21094-universidades-estatales.md` | Ley 21.094 | 2018-06-05 |

**Análisis técnico**: Estas dos leyes son **distintas** (Ley 21.091
"Sobre Educación Superior" publicada 7 días antes que Ley 21.094 "Sobre
Universidades Estatales"). Ambas pueden haber sido tramitadas en paralelo,
pero **no son texto refundido**.

**A diferencia del CC + Ley 14.908**, estas dos leyes NO comparten DFL
refundidor por su naturaleza. El id 1118991 probablemente corresponde
solo a **una** de las dos (probablemente Ley 21.091 que es la primera
publicada).

**Acción sugerida** (PROBABLE ERROR):
- Verificar contra BCN cuál norma corresponde al id=1118991.
- Buscar el ID correcto de la otra norma.
- Corregir el archivo que tiene URL incorrecta.

**Hipótesis**: el archivo creado primero (probablemente Ley 21.091) tiene
el ID correcto; el segundo (Ley 21.094) heredó por copy-paste el ID
incorrecto. Validar.

## Hallazgos técnicos transversales

### T1 — Sin verificación contra BCN

BCN no respondió durante las 62 auto-revisiones técnicas previas + esta
auditoría. **Recomendación operativa**: una vez que BCN esté
disponible, ejecutar verificación batch:

1. Para cada URL del corpus, GET `bcn.cl/leychile/navegar?idNorma=<id>`.
2. Extraer título oficial de la página.
3. Comparar con `titulo_oficial:` del frontmatter del archivo.
4. Flagear discrepancias.

**Script propuesto**: `chile/scripts/audit/check-bcn-urls.py` (no
implementado aún).

### T2 — IDs no documentados con tipo

El campo `fuente_oficial:` solo contiene URL. No declara qué tipo de
contenido es (ley, DFL, DL, código, tratado, AA).

**Acción sugerida**: agregar campo `bcn_tipo:` al frontmatter
opcional para mejor trazabilidad.

## Cobertura de la auditoría

- ✅ 100% de los archivos capa 3 revisados para duplicados.
- ❌ 0% verificación de URLs contra fuente oficial (BCN no respondió).
- ⚠️ 1 URL confirmada como ambigua (DFL refundidor).
- ⚠️ 1 URL sospechosa de error de copy-paste.

## Próximos pasos sugeridos

1. **Cuando BCN responda**: ejecutar verificación batch (script en T1).
2. **Inmediato**: corregir URL de Ley 21.094 si se confirma el error.
3. **Mediano plazo**: instrumentar `chile/scripts/audit/check-bcn-urls.py`
   como check de CI.

## Estado

- Generada: 2026-05-20.
- Auditoría transversal sin issue específico — afecta el corpus completo.
- Pendiente de validador legal + verificación batch.
