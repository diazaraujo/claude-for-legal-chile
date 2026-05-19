# Skill — Citas verificables

Skill **obligatorio**. Toda cita normativa o jurisprudencial del sistema debe ser
verificable contra una fuente oficial. Este skill define el formato, las reglas de
honestidad y los procedimientos cuando una cita no se puede verificar.

## Principio rector

> **El abogado que firma el output debe poder verificar cualquier cita en menos
> de un minuto.** Si una cita no cumple eso, está mal formada.

## Formatos canónicos

### Normativa

| Tipo | Formato | Ejemplo |
|---|---|---|
| Constitución | `Art. <N> [N° <NN>] CPR` | `Art. 19 N° 24 CPR` |
| Código | `Art. <N> <Código abreviado>` | `Art. 1545 CC`, `Art. 162 CT` |
| Ley | `Art. <N> de la Ley <NN.NNN>` | `Art. 16 de la Ley 19.496` |
| DFL / DL | `Art. <N> del DFL <N>/<año>` | `Art. 5 del DFL 1/2002` |
| Decreto Supremo | `Art. <N> del DS <N> (<Ministerio>, <año>)` | `Art. 21 del DS 40 (Mintrab, 1969)` |
| Reglamento de ley | `Art. <N> del Reglamento de la Ley <NN.NNN>` | `Art. 3 del Reglamento de la Ley 19.886` |
| Tratado | `Art. <N> de la <Convención>` | `Art. 8 de la Convención Americana sobre Derechos Humanos` |

**Abreviaciones aceptadas:**

- CC = Código Civil
- CT = Código del Trabajo
- CdC = Código de Comercio
- CTrib = Código Tributario
- CP = Código Penal
- CPP = Código Procesal Penal
- CPC = Código de Procedimiento Civil
- COT = Código Orgánico de Tribunales
- LSA = Ley 18.046 sobre SA
- LMV = Ley 18.045 sobre Mercado de Valores
- LPC = Ley 19.496 del Consumidor
- LPDP = Ley 19.628 (con 21.719 desde 2026-12-01) sobre datos personales
- CPR = Constitución Política de la República

### Jurisprudencia

| Tribunal | Formato | Ejemplo |
|---|---|---|
| Corte Suprema | `CS Rol N° <número>-<año>` | `CS Rol N° 12.345-2022` |
| Corte de Apelaciones | `CA <ciudad> Rol N° <número>-<año>` | `CA Santiago Rol N° 6.789-2023` |
| Tribunal Constitucional | `TC Rol N° <número>-<año>` | `TC Rol N° 12.123-21` |
| Tribunal del Trabajo | `JL <ciudad> RIT <tipo>-<número>-<año>` | `JL Santiago RIT T-456-2024` |
| Tribunal de Familia | `JF <ciudad> RIT C-<número>-<año>` | `JF Concepción RIT C-789-2024` |
| Juzgado Civil | `JC <N>° de <ciudad> Rol <número>-<año>` | `4° JC Santiago Rol C-1234-2023` |
| TDLC | `TDLC Sentencia N° <número>` | `TDLC Sentencia N° 180/2023` |
| Tribunal Constitucional (sentencias) | `Sentencia TC Rol N° <número>-<año>` | `Sentencia TC Rol N° 12.345-2022` |

### Doctrina administrativa

| Tipo | Formato | Ejemplo |
|---|---|---|
| Dictamen DT | `Dictamen DT N° <número>/<año>` | `Dictamen DT N° 4.567/2024` |
| Oficio SII | `Oficio SII N° <número> de <fecha>` | `Oficio SII N° 1.234 de 15-03-2023` |
| Dictamen Contraloría | `Dictamen CGR N° <número>/<año>` | `Dictamen CGR N° 67.890/2023` |
| NCG CMF | `NCG CMF N° <número>` | `NCG CMF N° 408` |
| Resolución SUSESO | `Resolución SUSESO N° <número>/<año>` | `Resolución SUSESO N° 234/2024` |

## Regla de honestidad: declarar el nivel de verificación

Antes de citar, el sistema declara cómo verifica:

| Nivel | Significado | Cuándo usar |
|---|---|---|
| ✅ **Verificada** | Texto presente en el corpus capa 3 validado, o consultado en BCN al momento | Para citas que sustentan una conclusión operativa |
| 🟨 **Catalogada** | La norma existe en BCN (capa 1) pero el sistema no validó el texto literal | Para mencionar existencia o referencia general |
| 🟧 **Inferida** | Cita razonable según contexto pero no verificada en línea | Solo si se declara explícitamente; preferible declinar |
| 🟥 **No verificable** | No se encuentra en BCN ni en el corpus | NO citar; declarar que no se puede verificar |

Cuando el sistema cita, prefijar visualmente:

```
Conforme al [✅ Art. 162 CT — verificado en corpus capa 3], el empleador debe...
```

o

```
La [🟧 cita inferida sobre el Dictamen DT N° 4.567/2024] sugiere que...
(no se pudo verificar; consultar https://www.dt.gob.cl/portal/...)
```

## Procedimiento cuando no se puede verificar

1. **Declarar explícitamente**: "No puedo verificar esta cita contra BCN en este
   momento."
2. **Sugerir verificación manual**: dar la URL de búsqueda (BCN, PJUD, DT, SII).
3. **No inventar números de rol o artículos**. Si no sabes el número exacto, di
   "el artículo del Código del Trabajo que regula X" sin número.

## Errores frecuentes a evitar

| Error | Por qué está mal | Correcto |
|---|---|---|
| "Art. 1545 del Código Civil de Chile" | Redundante (CC = chileno) | `Art. 1545 CC` |
| "el Código del Trabajo establece que..." sin artículo | Vago y no verificable | `Art. 162 CT establece que...` |
| Citar precedente sin rol | No verificable | `CS Rol N° 12.345-2022` |
| Mezclar normativa argentina con chilena | Error de jurisdicción | Solo chilena |
| "según se ha establecido jurisprudencialmente..." sin caso | Inverificable | Citar al menos un fallo, o declinar |

## Verificación cruzada para casos críticos

Cuando la cita sustenta una decisión de alto impacto (despido, denuncia, juicio):

1. Citar la norma con formato canónico.
2. Citar al menos un fallo de Corte que la haya aplicado.
3. Citar dictamen administrativo si es operativo (laboral → DT, tributario → SII).
4. Indicar al abogado que **verifique vigencia** del fallo y del dictamen.

## Disclaimer del sistema

El sistema incluye en cada respuesta:

```
Disclaimer: las citas declaradas como "verificadas" corresponden al texto que
el corpus tenía en el momento de la última actualización (ver frontmatter de
cada archivo). Antes de actuar, verificar texto vigente en BCN.
```
