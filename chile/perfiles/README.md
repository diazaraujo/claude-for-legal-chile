# Perfiles por rama

> Orquestadores del corpus normativo. Cada perfil invoca normativa capa 3
> cuando una consulta cae en su ámbito. No contienen derecho sustantivo:
> son **vistas** sobre `chile/normativa/`.

## Estado

9 perfiles publicados como borrador. Estado: `borrador-no-validado` —
pendientes de revisión por abogado de la especialidad.

## Índice

| Perfil | Ámbito principal | Cuándo se activa |
|---|---|---|
| [`laboral`](laboral.md) | Derecho del trabajo individual + colectivo + previsional | Contratos de trabajo, despidos, jornada, Ley Karin, subcontratación, sindicatos, accidentes, AFP/AFC, fueros |
| [`societario`](societario.md) | Derecho societario + gobierno corporativo + compliance | SA, SpA, SRL, EIRL, gobierno corporativo, MPD (Ley 20.393), OPAs, fusiones, fideicomiso, lavado |
| [`civil`](civil.md) | Derecho civil + familia patrimonial | Contratos, obligaciones, responsabilidad, compraventa, arriendo, mutuo, herencia, sociedad conyugal, AUC |
| [`tributario`](tributario.md) | Derecho tributario + procedimiento ante SII | LIR, IVA, contribuciones, patente municipal, royalty minero, reorganizaciones, NGA, TTA |
| [`penal`](penal.md) | Derecho penal sustantivo + procesal | CP + CPP, RPP, RPPJ, delitos económicos, crimen organizado, drogas, RPA, VIF, DDHH |
| [`familia`](familia.md) | Derecho de familia + NNA + adopciones | Matrimonio, divorcio, AUC, alimentos, cuidado personal, VIF, adopciones, identidad de género |
| [`administrativo`](administrativo.md) | Derecho administrativo + control externo | Procedimiento administrativo, sumarios funcionarios, CGR, compras públicas, transparencia, probidad, lobby, municipalidades |
| [`privacidad`](privacidad.md) | Protección de datos + ciberseguridad + digital | LPDP, Ley 21.719, brechas, ARCO, datos sensibles, ciberseguridad, firma electrónica, datos NNA |
| [`concursal`](concursal.md) | Insolvencia empresarial + personal | Reorganización + liquidación + PDP + Renegociación administrativa + SIR + revocatoria concursal |

## Diseño

Cada perfil sigue la misma estructura canónica:

1. **Frontmatter** con ámbito + estado_revision + fuente_corpus.
2. **Cuándo se activa** — keywords/contextos que disparan el perfil.
3. **Normas que invoca** — referencias a los archivos capa 3 con
   descripción breve de cuándo aplicar cada uno.
4. **Red flags** (señales automáticas) — agrupadas por área del perfil.
   Operativas para revisión de escritos.
5. **Plazos críticos** — tabla con norma + tipo (hábil/corrido/UTM/etc.).
6. **Skills que orquesta** — los 4 skills transversales aplicables.
7. **Casos típicos** — ejemplos resueltos (pendientes Fase 3).
8. **Disclaimers** — específicos del ámbito.
9. **Conexiones con otros perfiles** — cross-links semánticos.

## Pendientes Fase 3

- [ ] Validación legal de cada perfil por abogado de la especialidad.
- [ ] 2-3 ejemplos resueltos por perfil en `chile/ejemplos/`.
- [ ] Casos de prueba integrados para validar el sistema activa el
  perfil correcto.
- [ ] Glosario específico por rama (opcional, si crece la complejidad).

## Cómo invocar un perfil

El sistema (Claude) consulta automáticamente el perfil correspondiente
cuando detecta keywords del ámbito. Para forzar:

> "Aplica el perfil **societario** a esta consulta."

O para excluir:

> "Sin aplicar el perfil familiar, analízame el aspecto contractual."

## Mantenimiento

- Cuando se publica un nuevo perfil capa 3 en `chile/normativa/leyes/`,
  agregar al perfil de rama correspondiente.
- Cuando una norma se reforma, actualizar la sección "Alertas de
  volatilidad" en [`chile/CLAUDE.md`](../CLAUDE.md) + frontmatter del
  perfil de rama.
- Cross-links entre perfiles (`Conexiones con otros perfiles`) deben
  permanecer consistentes — si se renombra un perfil, actualizar todos
  los que lo citen.

> Ver [`MARCADORES.md`](../MARCADORES.md) para el vocabulario controlado.
