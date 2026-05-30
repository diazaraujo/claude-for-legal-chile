---
name: consulta-concursal
description: >
  Consulta procedimientos concursales chilenos (Ley N° 20.720) en el Registro del
  Boletín Concursal: liquidaciones y reorganizaciones de empresas y personas, por
  RUT, razón social/nombre del deudor o rol de causa. 747k publicaciones reales
  (2014-10 → hoy), no inventa. Usar cuando el usuario pregunta "¿tiene este RUT un
  procedimiento concursal?", "¿está en quiebra/liquidación esta empresa?", "muéstrame
  el estado del rol C-1234-2024", due diligence de contraparte o cobranza.
argument-hint: "[RUT | nombre del deudor | rol de causa]"
---

# /consulta-concursal

## Cuándo corre
El usuario quiere saber si una persona o empresa tiene un **procedimiento concursal**
vigente o histórico (liquidación voluntaria/forzosa, reorganización, renegociación),
su estado, su tribunal o su línea de tiempo de publicaciones. Típico en due diligence
de contraparte, evaluación de riesgo de crédito, cobranza, o verificación previa a
contratar. Para fallos judiciales generales usar [[buscar-jurisprudencia]]; para la
norma de fondo (Ley 20.720) usar [[verificar-cita]].

## Fuente
Registro del **Boletín Concursal** (Superintendencia de Insolvencia y Reemprendimiento,
Ley N° 20.720), indexado en `data/_index/new-sources.fts.sqlite3`, tabla `concursal`.
**747.552 publicaciones**, cobertura **2014-10 → hoy**. Cada fila es una *publicación*;
un *procedimiento* se identifica por **(rol, tribunal)** y agrupa sus publicaciones en
el tiempo. La **última publicación** es la mejor señal del estado actual.

## Qué hacer
1. **Identificar el criterio de búsqueda**:
   - RUT (con o sin puntos/guion) → búsqueda exacta.
   - Razón social / nombre del deudor → búsqueda parcial (mayúsculas, sin acento si dudas).
   - Rol de causa (`C-1234-2024`), opcionalmente acotado por tribunal.
2. **Ejecutar** el consultor estructurado:
   ```bash
   python skills/consulta-concursal/query.py --rut 17994454-5
   python skills/consulta-concursal/query.py --nombre "COMERCIAL LOS ANDES"
   python skills/consulta-concursal/query.py --rol C-418-2026 --tribunal "Villa Alemana"
   ```
   (Agregar `--json` para procesar el resultado.)
3. **Presentar** por procedimiento: **rol + tribunal**, deudor + RUT, **tipo de
   procedimiento** (liquidación voluntaria/forzosa/refleja, reorganización,
   renegociación; empresa vs persona deudora), rango de fechas, número de
   publicaciones y la **última publicación como estado aproximado**. Si el usuario
   lo pide, desplegar la línea de tiempo completa de publicaciones (resolución de
   liquidación, junta de acreedores, nómina de créditos, remates, término, etc.).

## Reglas
- **Anti-alucinación**: solo procedimientos que el Registro devuelve. Sin resultados
  → decirlo explícito, con el alcance temporal (2014-10 → hoy). Ausencia de
  publicación ≠ ausencia absoluta de procedimiento (uno muy reciente puede no estar
  aún publicado).
- El **"estado aproximado"** se infiere de la última publicación, no es un campo
  oficial de estado. Señalarlo como aproximación; el estado jurídico definitivo se
  confirma en el expediente del tribunal / Boletín oficial.
- Distinguir **tipo de procedimiento**: liquidación (cesación de pagos → realización
  de bienes) vs reorganización/renegociación (continuidad con acuerdo de acreedores).
  No describir una liquidación como "quiebra" sin matizar (la Ley 20.720 reemplazó el
  régimen de quiebra de la Ley 18.175).
- Un mismo RUT puede tener **varios procedimientos** (histórico). Mostrarlos todos,
  ordenados del más reciente.
- **No es asesoría**: el output es insumo para due diligence / decisión de un abogado
  o analista; los efectos jurídicos (desasimiento, fueros, plazos de verificación) se
  evalúan caso a caso sobre la Ley 20.720.

## Relación con otros skills
- Cruce de identidad del deudor (socios, RUT, razón social) → API Mallas, fuera de
  este corpus.
- Norma aplicable (artículos de la Ley 20.720) → [[verificar-cita]].
- Jurisprudencia sobre insolvencia → [[buscar-jurisprudencia]] / [[buscar-dictamen]].
