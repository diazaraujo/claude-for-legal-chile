# Skills — claude-legal-chile

Skills invocables del plugin `claude-legal-chile`. Dos grupos: **transversales**
(método) y **de corpus** (el diferenciador — orquestan los MCP sobre el corpus
real, anti-alucinación por retrieval).

## Skills de corpus ⭐ (lo que Argentina no puede tener)
| Skill | Función | MCPs |
|---|---|---|
| [`verificar-cita`](verificar-cita/SKILL.md) | Valida artículo/rol/dictamen contra el corpus antes de afirmarlo | corpus-search, pjud, tc-fallos, cgr/dt/sii |
| [`buscar-jurisprudencia`](buscar-jurisprudencia/SKILL.md) | Sentencias (CS, CA, TC, TDLC, ambiental, TTA, TDPI) por materia/rol | pjud, tc-fallos, tdlc, corpus-search |
| [`buscar-dictamen`](buscar-dictamen/SKILL.md) | Jurisprudencia administrativa (CGR, DT, CPLT, SUSESO, SII) | cgr-dictamenes, dt-dictamenes, sii-juris |
| [`linea-jurisprudencial`](linea-jurisprudencial/SKILL.md) | Evolución del criterio sobre un punto de derecho | (compone los anteriores) |
| [`red-flags-contrato`](red-flags-contrato/SKILL.md) | Revisa contrato vs normativa vigente recuperada | corpus-search + dictamen/jurisprudencia |
| [`consulta-concursal`](consulta-concursal/SKILL.md) | Procedimientos concursales (Ley 20.720) por RUT/deudor/rol sobre el Registro del Boletín Concursal (747k publicaciones) | concursal (tabla estructurada) |

## Skills transversales (método)
| Skill | Función |
|---|---|
| [`diagnostico`](diagnostico/SKILL.md) | Diagnóstico estructurado de un escrito antes de modificarlo |
| [`plazos`](plazos/SKILL.md) | Días hábiles vs corridos, feriados, Art. 66 CPC |
| [`marcadores-glosario`](marcadores-glosario/SKILL.md) | Desambigua siglas/unidades/órganos chilenos (UF, CMF, DT, COT…) |

## Evals
[`evals/`](evals/README.md) — casos de verificación con solución conocida
(método del fork argentino, contenido 100% chileno verificable contra el corpus).

## Principio
Todo skill que cite DEBE recuperar del corpus y pasar por `verificar-cita`. Nunca
contenido normativo de otra jurisdicción. Output = borrador para abogado habilitado.
