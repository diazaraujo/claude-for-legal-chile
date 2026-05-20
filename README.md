# Claude for Legal · Chile

> **Corpus normativo chileno estructurado para uso con Claude.** Códigos, leyes
> especiales, decretos y reglamentos chilenos descritos en archivos markdown con
> frontmatter canónico, listos para que Claude los invoque al razonar sobre derecho
> chileno.

[![License](https://img.shields.io/github/license/diazaraujo/claude-for-legal-chile)](LICENSE)
[![Stars](https://img.shields.io/github/stars/diazaraujo/claude-for-legal-chile?style=flat)](https://github.com/diazaraujo/claude-for-legal-chile/stargazers)
[![Issues](https://img.shields.io/github/issues/diazaraujo/claude-for-legal-chile)](https://github.com/diazaraujo/claude-for-legal-chile/issues)
[![Last Commit](https://img.shields.io/github/last-commit/diazaraujo/claude-for-legal-chile)](https://github.com/diazaraujo/claude-for-legal-chile/commits/main)
![Estado](https://img.shields.io/badge/estado-work%20in%20progress-yellow)
![Validación legal](https://img.shields.io/badge/validaci%C3%B3n%20legal-pendiente-orange)

---

## ¿Qué es esto?

Una adaptación al **derecho chileno** del proyecto open source
[`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal). La
diferencia arquitectónica con otros forks nacionales: **el corpus normativo es el eje
del sistema**, no los perfiles por rama del derecho. Es coherente con la tradición
civil law que se cita por artículo, no por precedente.

Todo el contenido chileno vive en [`chile/`](chile/). El upstream se mantiene intacto
para facilitar sync futuros con Anthropic.

## ¿Para quién?

- **Abogados y estudios jurídicos chilenos** que quieran usar Claude como asistente
  de análisis legal sin que cite por default normativa española o mexicana.
- **Equipos legales in-house** en empresas con operación en Chile.
- **Builders y developers** construyendo productos legal-tech para el mercado chileno.
- **Estudiantes de derecho** que necesiten un corpus estructurado de la normativa
  vigente.

## ¿Por qué este fork?

1. **Claude por default cita normativa genérica** o aplicable a otras jurisdicciones
   (típicamente España/México). En práctica chilena eso induce a errores.
2. **La tradición civil law chilena** se cita por artículo de cuerpo normativo
   ("Art. 1545 CC", "Art. 162 Código del Trabajo"), no por precedentes. Un sistema
   diseñado para common law no encaja.
3. **Mantenimiento centralizado**: cuando entra en vigencia la Ley 21.719 el
   1 de diciembre de 2026, se actualiza un archivo. Los perfiles que la citan heredan.
4. **Validación granular**: cada norma se valida con un experto en esa norma — no por
   rama transversal. Reduce el costo de revisión legal.

## ¿Cómo se usa?

Tres modos, una misma fuente:

### 1. Con Claude Code

```bash
git clone https://github.com/diazaraujo/claude-for-legal-chile.git
cd claude-for-legal-chile
claude  # apunta Claude Code a esta carpeta como contexto
```

Claude leerá [`chile/CLAUDE.md`](chile/CLAUDE.md) y el corpus en
[`chile/normativa/`](chile/normativa/) al razonar.

### 2. Con Claude.ai Projects

1. Crea un Project en [Claude.ai](https://claude.ai).
2. Sube los archivos de [`chile/`](chile/) como "Project files".
3. En el system prompt del Project escribe:
   ```
   Eres un asistente de análisis legal configurado para práctica chilena.
   Lee chile/CLAUDE.md y opera bajo sus reglas.
   ```
4. Empieza a consultar.

### 3. Con la API de Claude / Managed Agents

Carga el corpus como contexto base de tu agente. Ver upstream
[`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal) para
patrones de despliegue.

---

## Cobertura actual

El corpus se publica en tres capas (ver `decisions/ADR-0002`):

| Capa | Qué tiene | Cobertura actual |
|---|---|---|
| **1 — Catálogo** | Metadata estructurada por norma desde BCN/SPARQL | **12.465 archivos** (4.921 leyes + 4.167 DL + 3.171 DFL + 167 tratados + 27 AA + 11 códigos) |
| **2 — Resumen estructural** | Libros/títulos/artículos + conceptos clave desde XML estructurado de LeyChile | **~11.800 archivos** (4.833 leyes + 3.827 DL + 2.942 DFL + 167 tratados + 15 AA + 10 códigos; pipeline en `scripts/bcn/promote-to-capa2.py`) |
| **3 — Análisis operativo curado** | Lo que ves abajo, con disclaimer + validación legal | **126 archivos borrador** (115 leyes + 9 códigos + 2 constitución) + 4 skills + setup interview + fuentes |

Detalle de capa 1 en [`chile/normativa/catalogo/README.md`](chile/normativa/catalogo/README.md).
Estado de capa 3 a continuación. Solo los marcados ✅ están publicados como borrador
estructurado; ninguno ha pasado validación legal todavía.

### Constitución

| Norma | Estado | Archivo |
|---|---|---|
| Constitución Política de la República | ✅ Borrador | [`constitucion-politica.md`](chile/normativa/constitucion/constitucion-politica.md) |

### Códigos

| Código | Estado | Archivo |
|---|---|---|
| Código del Trabajo (DFL 1/2002) | ✅ Borrador | [`codigo-trabajo.md`](chile/normativa/codigos/codigo-trabajo.md) |
| Código de Comercio | ✅ Borrador | [`codigo-comercio.md`](chile/normativa/codigos/codigo-comercio.md) |
| Código Civil (Andrés Bello, 1855) | ✅ Borrador | [`codigo-civil.md`](chile/normativa/codigos/codigo-civil.md) |
| Código Tributario (DL 830) | ✅ Borrador | [`codigo-tributario.md`](chile/normativa/codigos/codigo-tributario.md) |
| Código Penal | ✅ Borrador | [`codigo-penal.md`](chile/normativa/codigos/codigo-penal.md) |
| Código Procesal Penal (Ley 19.696) | ✅ Borrador | [`codigo-procesal-penal.md`](chile/normativa/codigos/codigo-procesal-penal.md) |
| Código de Procedimiento Civil | ✅ Borrador | [`codigo-procedimiento-civil.md`](chile/normativa/codigos/codigo-procedimiento-civil.md) |
| Código Orgánico de Tribunales (Ley 7.421) | ✅ Borrador | [`codigo-organico-tribunales.md`](chile/normativa/codigos/codigo-organico-tribunales.md) |

[Ver índice completo](chile/normativa/codigos/00-indice.md) (12 códigos).

### Leyes especiales

**115 perfiles** publicados como borrador, organizados por bloque temático.
Todos en `estado_revision: borrador-no-validado` salvo indicación expresa.

#### Constitucional · Orgánico · Control

LOC Banco Central (18.840) · LOC TC (17.997) · LOC Congreso (18.918) · LOC
Municipalidades (18.695) · LOC FFAA — pendientes · CGR (10.336) · LOC MP (19.640) ·
DPP (19.718) · Reforma orgánica PJUD (19.665) · LOC Votaciones (18.700) ·
Gobernadores Regionales (21.073) · LOC Concesiones Mineras (18.097) · Bases
AdEstado (18.575).

#### Tributario · Municipal

Renta DL 824 · IVA DL 825 · Reducción exenciones (21.420) · Reforma Tributaria 2024
(21.713) · Impuesto Territorial (17.235) · Rentas Municipales (DL 3.063) · Royalty
Minero (21.591).

#### Laboral · Previsional · Seguridad Social

Subcontratación (20.123) · 40h (21.561) · Ley Karin (21.643) · Teletrabajo (21.220) ·
Inclusión Laboral (21.015) · Accidentes del Trabajo (16.744) · Sindicatos (20.940) ·
Tribunales del Trabajo (20.022) · Procedimiento Laboral (20.087) · SENCE (19.518) ·
Cesantía AFC (19.728) · DL 3.500 Pensiones · Reforma Previsional 2008 (20.255) ·
PGU (21.419).

#### Familia · Niñez · DDHH

Matrimonio Civil (19.947) · Matrimonio Igualitario (21.400) · AUC (20.830) ·
Tribunales Familia (19.968) · Adopciones (19.620) · Alimentos (14.908) · VIF
(20.066) · Garantías NNA (21.430) · SNN (21.302) · RRSJ (21.527) · Defensoría Niñez
(21.067) · Entrevista videograbada (21.057) · RPA (20.084) · Identidad de género
(21.120) · Reparación Rettig (19.123) · Reparación Valech (19.992) · INDH (20.405).

#### Salud

Código Sanitario (DFL 725) · Derechos del Paciente (20.584) · AUGE/GES (19.966) ·
Aborto 3 causales (21.030) · Salud Mental (21.331) · APS Municipal (19.378).

#### Educación

LGE (DFL 2/2009) · Subvención Escolar (DFL 2/1998) · Estatuto Docente (19.070) ·
SLEP (21.040) · UE (21.094) · Educación Superior (21.091).

#### Recursos Naturales · Sectorial

Bases Medio Ambiente / SEIA (19.300) · Cambio Climático (21.455) · Código de Aguas
(DFL 1.122) · LGPA Pesca (18.892) · Código de Minería (18.248) · Royalty (21.591) ·
LGUC (DFL 458) · Bienes del Estado (DL 1.939) · Monumentos Nacionales (17.288).

#### Penal · Procesal Penal · Crimen Organizado

RPPJ (20.393) · Delitos Económicos (21.595) · Crimen Organizado (21.601) · Drogas
(20.000) · VIF (20.066) · Lavado de Activos (19.913) · ANI Inteligencia (19.974) ·
RPA (20.084).

#### Comercial · Financiero · Consumidor

Sociedades Anónimas (18.046) · Mercado de Valores (18.045) · Gobierno Corporativo
SA (21.314) · CMF (21.000) · Banco Central (18.840) · Concursal (20.720) · Letras y
Pagarés (18.092) · OCD (18.010) · Consumidor (19.496) · Fintec (21.521) · Fraude
Tarjetas (21.234) · Competencia Desleal (20.169) · Libre Competencia (DL 211) ·
Propiedad Industrial (19.039) · Propiedad Intelectual (17.336).

#### Inmobiliario · Urbanismo

LGUC (DFL 458) · Copropiedad inmobiliaria (19.537) · Compraventa inmuebles —
información falsa (21.484) · Código Aguas (DFL 1.122).

#### Administrativo · Transparencia · Compliance

Procedimiento Administrativo (19.880) · Bases AdEstado (18.575) · EA general
(18.834) · EAM (18.883) · Transparencia (20.285) · Probidad (20.880) · Lobby
(20.730) · Asociaciones (20.500) · JJVV (19.418) · Compras Públicas (19.886).

#### Privacidad · Digital · Ciberseguridad

LPDP (19.628) · Modificación LPDP (21.719) · Firma electrónica (19.799) ·
Transformación digital (21.180) · Ciberseguridad (21.663) · ANI (19.974) · CNTV
(18.838) · Libertades opinión (19.733).

#### Sectorial · Otros

Aeronáutico (18.916) · Telecomunicaciones (18.168) · Migración (21.325) · No
discriminación (20.609) · Discapacidad (20.422) · Transparencia (20.285).

[**Ver índice completo de las 115 leyes**](chile/normativa/leyes/00-indice.md).

### Skills transversales

| Skill | Función |
|---|---|
| [`diagnostico`](chile/skills/diagnostico.md) | Diagnóstico inicial: clasifica consulta, identifica normas aplicables, sugiere análisis |
| [`citas-verificables`](chile/skills/citas-verificables.md) | Genera citas con `Art.` + `cuerpo normativo` + URL BCN, evitando alucinación de jurisprudencia |
| [`plazos`](chile/skills/plazos.md) | Cálculo de plazos legales con día hábil / corrido, feriados, suspensiones |
| [`compliance-corporativo`](chile/skills/compliance-corporativo.md) | Modelo de prevención del delito (Ley 20.393 + 21.595) + lobby + probidad |
| [`diagnostico-casos-prueba`](chile/skills/diagnostico-casos-prueba.md) | 20 casos de prueba para validar que el sistema activa perfil + normas correctas |

### Perfiles por rama

**9 perfiles** publicados como borrador, cubriendo las ramas más demandadas:

| Perfil | Ámbito | Activación |
|---|---|---|
| [`laboral`](chile/perfiles/laboral.md) | CT + 13 leyes especiales + previsional + procesal | Contratos, despidos, jornada, Karin, sindicatos, accidentes |
| [`societario`](chile/perfiles/societario.md) | SA + LMV + GC + RPPJ + MPD + lavado + concursal | Constitución, gobierno corporativo, OPAs, MPD, fusiones |
| [`civil`](chile/perfiles/civil.md) | CC + familia patrimonial + contratos + responsabilidad | Contratos, obligaciones, compraventa, herencia, AUC |
| [`tributario`](chile/perfiles/tributario.md) | CT + LIR + IVA + Reformas + royalty + municipal | LIR, IVA, contribuciones, patente, reorganización, NGA, TTA |
| [`penal`](chile/perfiles/penal.md) | CP + CPP + MP + DPP + delitos económicos + crimen organizado | RPP, RPPJ, delitos económicos, drogas, RPA, VIF, DDHH |
| [`familia`](chile/perfiles/familia.md) | Matrimonio + AUC + TF + alimentos + VIF + adopciones | Divorcio, alimentos, cuidado personal, VIF, adopciones |
| [`administrativo`](chile/perfiles/administrativo.md) | Ley 19.880 + LOC + Estatutos + CGR + Compras + Transparencia | Sumarios funcionarios, CGR, compras públicas, lobby, transparencia |
| [`privacidad`](chile/perfiles/privacidad.md) | LPDP 19.628 + Reforma 21.719 + ciberseguridad 21.663 | Datos personales, brechas, ARCO, datos sensibles, ciberseguridad |
| [`concursal`](chile/perfiles/concursal.md) | Ley 20.720 + SIR + reorganización + liquidación | Insolvencia, reorganización, liquidación, PDP |

Cada perfil declara: cuándo se activa, normas que invoca (~10-20 c/u), ~25
red flags accionables, tabla de plazos críticos, skills orquestados,
conexiones con otros perfiles. Ver [`chile/perfiles/README.md`](chile/perfiles/README.md).

### Ejemplos resueltos

**13 ejemplos** que demuestran el sistema operando sobre las 9 ramas con
casos realistas. Cada ejemplo sigue patrón canónico de 10 secciones
(escenario, análisis, plazos, cálculo de exposición, red flags, etc.).
Ver [`chile/ejemplos/README.md`](chile/ejemplos/README.md).

---

## Ejemplo de consulta

Una vez cargado el contexto, una consulta típica:

> **Q:** Una empleada me informa que su jefe la ha humillado públicamente en
> reuniones durante dos meses. ¿Qué plazo tengo para iniciar la investigación interna?
>
> **A (sistema, con corpus cargado):** Conforme a la **Ley 21.643 ("Ley Karin")**,
> publicada el 15 de enero de 2024, el empleador tiene **3 días hábiles** desde la
> recepción formal de la denuncia para iniciar la investigación interna. Adicional:
>
> 1. Adoptar **medidas de resguardo inmediatas** (separación física, cambio de
>    funciones, licencia preventiva si aplica).
> 2. Investigar con **perspectiva de género** y debido proceso.
> 3. Comunicar a la Dirección del Trabajo dentro del plazo legal.
> 4. Si la conducta afectó la salud de la trabajadora, notificar a la Mutual de
>    Seguridad (Ley 16.744).
>
> Si la trabajadora prefiere, también puede denunciar directamente ante la DT o
> iniciar tutela laboral (Arts. 485-495 CT) por afectación de derechos fundamentales.
>
> **Disclaimer:** este análisis es un borrador para revisión por abogado habilitado.
> Verificar texto vigente en BCN/LeyChile. El archivo de norma utilizado
> (`ley-21643-acoso-laboral`) está en estado `borrador-no-validado`.

Ver más ejemplos en [`chile/ejemplos/`](chile/ejemplos/).

---

## Hoja de ruta

- ✅ **Fase 0** — Fork + arquitectura normativa-spine + 4 normas iniciales publicadas
- ✅ **Fase 1** — Capa 1 catálogo completo (12.465 archivos) + capa 2 estructural
  (~11.800 archivos) + 9 códigos + ~50 leyes prioritarias publicadas en borrador
- ✅ **Fase 2** — 4 skills transversales (diagnóstico, citas verificables, plazos,
  compliance corporativo) + cobertura ampliada a 115 leyes especiales
- ✅ **Fase 3** — 9 perfiles por rama (laboral, societario, civil, tributario,
  penal, familia, administrativo, privacidad, concursal) + 13 ejemplos resueltos +
  20 casos de prueba + principio LLM-wiki + protocolo anti-alucinación +
  glosario de marcadores
- 🚧 **Fase 4** — Validación legal por abogados habilitados +
  [MCP connectors](chile/scripts/mcp/README.md) (BCN como MVP) + release v1.0
- ⏳ **Fase 5** — Integración con productos Unholster + monetización selectiva

Ver [issues abiertas](https://github.com/diazaraujo/claude-for-legal-chile/issues)
para el detalle.

---

## Quiero contribuir

Bienvenidas las contribuciones en cualquiera de estas líneas:

1. **Redactar archivos de norma** siguiendo el [schema canónico](chile/normativa/README.md).
2. **Validación legal** — si eres abogado habilitado en Chile y quieres revisar
   archivos en estado `borrador-no-validado`, abre un issue presentándote y vamos
   coordinando.
3. **Casos de prueba / ejemplos** en [`chile/ejemplos/`](chile/ejemplos/) que muestren
   cómo el sistema responde consultas reales.
4. **Reportar errores** normativos: si Claude cita mal, ese es un bug que queremos
   cerrar.
5. **Sugerir reglas operativas** para los skills transversales.

Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir un PR. Issues marcados con
[`good first issue`](https://github.com/diazaraujo/claude-for-legal-chile/labels/good%20first%20issue)
son buenos puntos de entrada.

---

## ⚠️ Disclaimer legal

**Este sistema NO entrega asesoría legal directa al usuario final.** Es una
herramienta de apoyo para análisis legal. Toda salida es un **borrador para revisión
por abogado habilitado en Chile**, quien firma y aplica el resultado.

- **Verificación humana obligatoria** de citas normativas y jurisprudenciales contra
  fuentes oficiales: [BCN — LeyChile](https://www.bcn.cl/leychile) y
  [Poder Judicial de Chile](https://www.pjud.cl).
- **Jurisdicción asumida**: derecho chileno, salvo indicación expresa.
- **Estado de revisión** declarado en cada archivo: solo los marcados `validada`
  pueden invocarse sin disclaimer adicional.
- El sistema no reemplaza al abogado y no se constituye relación cliente-abogado por
  su uso.

---

## Mantenido por Unholster

[**Unholster**](https://unholster.com) es una empresa chilena de consultoría e
ingeniería en datos y AI. Este proyecto es parte de nuestra iniciativa pública de
acelerar la adopción responsable de Claude en industrias reguladas chilenas.

Dirección y publicación: [Antonio Díaz-Araujo](https://github.com/diazaraujo) ·
antonio@unholster.com

Si tu organización necesita un programa de adopción de Claude para práctica legal
(perfiles privados de tu firma, RAG sobre tu jurisprudencia, integración con sistemas
internos), [contáctanos](https://unholster.com).

---

## Upstream original

Este es un fork de [`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal),
distribuido bajo licencia Apache-2.0. La adaptación chilena vive en
[`chile/`](chile/); el resto del repositorio reproduce el upstream para facilitar
sync. Para el README original en inglés, ver
[el upstream](https://github.com/anthropics/claude-for-legal#readme).

Patrón estructural inspirado en el fork análogo argentino
[`cristianaboitiz-eng/claude-for-legal-argentina`](https://github.com/cristianaboitiz-eng/claude-for-legal-argentina),
con divergencia arquitectónica documentada en
[`chile/CHANGELOG.md`](chile/CHANGELOG.md).

---

## Licencia

[Apache-2.0](LICENSE) — heredada del upstream.

Las contribuciones a este fork (`chile/`) quedan bajo la misma licencia.
