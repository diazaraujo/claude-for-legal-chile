# Fuentes oficiales y conectores

Mapa de **fuentes autoritativas** del derecho chileno que el sistema usa para
verificar citas, recuperar texto vigente y razonar sobre temas legales. Toda
afirmación normativa del sistema debe ser trazable a una de estas fuentes.

## Fuentes primarias

### Normativa

| Fuente | URL | Qué contiene | Uso típico |
|---|---|---|---|
| **BCN — Ley Chile** | https://www.bcn.cl/leychile | Texto vigente de leyes, códigos, decretos, DFL, DL, tratados, autos acordados. Historial de modificaciones. | Citar texto literal, verificar vigencia, ver línea de tiempo de modificaciones |
| **BCN — Linked Open Data** | https://datos.bcn.cl/sparql | Ontología `bcn-norms` con metadata estructurada de las normas | Consultas semánticas, scraping de catálogo |
| **Diario Oficial** | https://www.diariooficial.interior.gob.cl/ | Publicación oficial de leyes y normas (entrada en vigencia) | Verificar fecha de publicación |

### Jurisprudencia

| Fuente | URL | Qué contiene | Uso típico |
|---|---|---|---|
| **Poder Judicial — Buscador Unificado** | https://oficinajudicialvirtual.pjud.cl/ | Sentencias de Corte Suprema, Cortes de Apelaciones y tribunales | Buscar precedentes por rol o materia |
| **Corte Suprema** | https://www.pjud.cl/courts/corte-suprema | Sentencias y acuerdos del máximo tribunal | Precedentes en casación |
| **Tribunal Constitucional** | https://www.tribunalconstitucional.cl/ | Sentencias del TC | Inaplicabilidad, control constitucional |
| **TDLC** | https://www.tdlc.cl/ | Sentencias del Tribunal de Defensa de la Libre Competencia | Casos de libre competencia |

### Interpretación administrativa

| Fuente | URL | Qué contiene | Uso típico |
|---|---|---|---|
| **Dirección del Trabajo — Dictámenes** | https://www.dt.gob.cl/portal/1626/w3-propertyvalue-22580.html | Dictámenes interpretativos de la DT sobre Código del Trabajo y leyes laborales | Materia laboral operativa |
| **SII — Jurisprudencia administrativa** | https://www.sii.cl/normativa_legislacion/jurisprudencia_administrativa/index.html | Oficios, circulares y resoluciones del SII | Tributario |
| **Contraloría General de la República** | https://www.contraloria.cl/ | Dictámenes de control de legalidad | Derecho administrativo, función pública |
| **CMF — Normativa** | https://www.cmfchile.cl/portal/principal/613/w3-propertyvalue-19089.html | Normas de Carácter General (NCG), circulares | Mercado financiero, SA abiertas |
| **SUSESO** | https://www.suseso.cl/ | Resoluciones sobre seguridad social y Ley 16.744 | Accidentes del trabajo, enfermedades profesionales |
| **APDP** (vigente desde 2026-12-01) | _pendiente — sitio oficial será publicado por el gobierno_ | Reglamentos y resoluciones sobre Ley 21.719 | Protección de datos personales |

### Identidad y registros

| Fuente | URL | Uso típico |
|---|---|---|
| **SERVEL** | https://www.servel.cl/ | Padrón electoral, calificación de partidos |
| **Registro Civil** | https://www.registrocivil.cl/ | Identidad, estado civil, matrimonio civil |
| **Conservador de Bienes Raíces** | varía por jurisdicción | Inscripciones de dominio, hipotecas, gravámenes |
| **SII — RUT** | https://zeus.sii.cl/dii_doc/rut/htm/i_pago_renta_anual.htm | Verificación de RUT vigente |

## Conectores MCP recomendados

Cuando se opera vía Claude Code o Claude.ai con MCP habilitado, conectores útiles:

- **Google Drive / SharePoint**: para acceder a expedientes del cliente.
- **Slack / Email**: para comunicar resultados al equipo.
- **Linear / Jira**: tracking de matters.
- **Google Calendar**: gestionar plazos y audiencias.

No hay conectores MCP oficiales para BCN/PJUD/DT/SII al momento de este escrito.
Las consultas a esos sistemas se hacen vía web fetch o scripts dedicados.

## Reglas de citación

Cuando el sistema responde con una cita normativa o jurisprudencial:

1. **Cita normativa**: formato `Art. <número> de la <Ley/Código>` (ej. `Art. 1545 CC`,
   `Art. 162 Código del Trabajo`, `Art. 19 N° 4 CPR`).
2. **Cita jurisprudencial**: formato `<Tribunal> Rol N° <número>-<año>` (ej.
   `CS Rol N° 12.345-2022`, `CA Santiago Rol N° 6.789-2023`).
3. **Cita administrativa**: `Dictamen DT N° <número>-<año>`, `Oficio SII N° <número>
   de <fecha>`, `NCG CMF N° <número>`.
4. **Toda cita lleva enlace a la fuente** cuando es posible.
5. **Si el sistema no puede verificar la cita en línea**, lo declara antes de
   mencionarla y sugiere consultar manualmente.

## Reglas de actualización

Cuando una norma se modifica:

1. Verificar texto vigente en BCN.
2. Actualizar archivo de norma en `chile/normativa/` si está en capa 2 o 3.
3. Registrar modificación en frontmatter `ultima_modificacion`.
4. Si la modificación es estructural (no de detalle), actualizar también los
   perfiles que la invocan.

## Fuentes secundarias útiles (académicas y editoriales)

No autoritativas, pero útiles para interpretación y doctrina. **No reemplazan
las primarias**. El sistema NO debe citar estas fuentes como si fueran autoritativas.

- Revistas jurídicas chilenas: Revista de Derecho UC, RDPUCV, Anuario de Derecho
  Constitucional Latinoamericano, etc.
- Editoriales: LegalPublishing (Thomson Reuters), Punto Lex, Editorial Jurídica.
- Centros de investigación: CEP, Libertad y Desarrollo, ConGen.

---

## Disclaimer

Este documento es un mapa de fuentes. La verificación contra las fuentes oficiales es
**responsabilidad del abogado** que firma el output del sistema. El sistema señala
las fuentes pero no garantiza que el texto cargado en su corpus esté siempre al día.
