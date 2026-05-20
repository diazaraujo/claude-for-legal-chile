---
archivo_revisado: ley-20393-rppj
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#11"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 20.393 (RPPJ + MPD)

> Revisión técnica (consistencia, gaps), NO legal. El validador
> resuelve las decisiones sustantivas.

> **Importante**: este perfil opera bajo régimen **post-Ley 21.595
> (2023)** que **modificó estructuralmente** la 20.393. Ambas leyes
> deben validarse juntas (ver `ley-21595-delitos-economicos-hallazgos.md`
> en preparación).

## Resumen ejecutivo

- **5 hallazgos críticos** para validador.
- **2 hallazgos técnicos** (consistencia).
- **6 preguntas abiertas** específicas.
- BCN no respondió en revisión técnica.

## Hallazgos críticos — decisión del validador

### H1 — Certificación de MPD: ¿"por empresas certificadoras autorizadas por CMF"?

El perfil declara:
> Certificación del MPD: Voluntaria, por empresas certificadoras
> autorizadas por CMF.

**Observación**: Históricamente la autoridad acreditadora de
certificadoras era la **SVS** (Superintendencia de Valores y Seguros).
Con la **fusión SVS+SBIF en CMF (Ley 21.000, 2017)**, la facultad pasa
a la CMF. Pero algunas certificadoras pueden estar acreditadas por
**Inacap** u otras vías indirectas.

**Acción sugerida**:
- Confirmar que la facultad de acreditación de certificadoras está en
  la CMF (no en organismo independiente).
- Mencionar las certificadoras actualmente acreditadas si la lista es
  pública.

### H2 — Catálogo de delitos: lista completa post-Ley 21.595

El perfil lista 14 delitos como "entre otros". La Ley 21.595 amplió a
**~250 delitos económicos** atribuibles según fuentes secundarias.

**Observación**: El listado del perfil es **incompleto** + ambiguo. Para
ser operativamente útil:

- Validador debe revisar el catálogo completo del Art. 1 modificado.
- Considerar enlazar a una **tabla anexa** con TODOS los delitos
  catalogados.

**Acción sugerida**:
- Verificar texto vigente del Art. 1.
- Considerar mover el catálogo completo a un archivo
  `ley-20393-rppj-catalogo-delitos.md` por extensión.
- Mantener resumen en el perfil principal.

### H3 — Tope de multa: 200 a 300.000 UTM vs cifras post-21.595

El perfil declara:
> Multa: De 200 a 300.000 UTM según delito y reincidencia

**Observación**: La Ley 21.595 **elevó significativamente** los topes
para delitos económicos. En algunos delitos puede ser **hasta el 30% de
las ventas anuales** (similar a sanciones CMF/FNE en libre competencia).

**Acción sugerida**:
- Verificar la tabla de multas vigentes post-21.595.
- Distinguir régimen general (200 - 300.000 UTM) vs régimen reforzado
  para delitos económicos específicos.

### H4 — "Personas vinculadas": alcance exacto

El perfil declara:
> Persona vinculada: Quien actúa a nombre o en interés de la PJ;
> dueños, controladores, ejecutivos, empleados, contratistas en
> algunos casos.

**Observación**: La Ley 21.595 extendió el concepto de "persona
vinculada" a:
- **Subcontratistas** y **proveedores** en ciertos casos.
- **Filiales y matrices** del grupo empresarial.
- **Joint ventures**.

"En algunos casos" es vago. El validador debe precisar.

**Acción sugerida**:
- Definir alcance exacto de "persona vinculada" post-21.595.
- Documentar implicancias para due diligence M&A.

### H5 — Sujetos: ¿empresas del Estado plenamente?

El perfil dice:
> Sociedades, asociaciones, fundaciones (privadas y empresas del Estado)

**Observación**: Las **empresas del Estado** (Codelco, ENAP,
BancoEstado, TVN) tienen régimen específico. Algunas pueden estar
excluidas o tener inmunidades parciales.

**Acción sugerida**:
- Confirmar qué empresas del Estado están plenamente sujetas a RPPJ.
- Documentar excepciones si las hay (FFAA, organismos autónomos
  constitucionales).

## Hallazgos técnicos

### T1 — Frontmatter: `relacionada_con` vs `relacionada_per`

Mismo problema sistemático. Cambiar a `relacionada_per`.

### T2 — Faltan cruces importantes

`relacionada_con` solo declara 3 (CP, CPP, Ley 21.595). Faltan:

- `ley-19913-lavado-activos` — UAF + reportes obligatorios.
- `ley-21643-acoso-laboral` — Karin como delito atribuible.
- `ley-18045-mercado-valores` — insider trading.
- `dl-211-libre-competencia` — delitos competencia.
- `ley-19300-medio-ambiente` — delitos ambientales.
- `ley-20730-lobby` + `ley-20880-probidad-publica` — cohecho.

## Preguntas abiertas para el validador

1. **¿Hay diferencia entre el "Encargado de Prevención"** (Art. 4 Ley
   20.393) y el **"Oficial de Cumplimiento" / "Compliance Officer"** en
   el sentido internacional? ¿Son la misma figura?

2. **¿La certificación voluntaria** del MPD tiene un peso jurisprudencial
   reconocido en tribunales chilenos, o sigue siendo cuestionada como
   "formalismo"?

3. **¿La acción de cumplimiento** del MPD se ejerce **antes o durante** la
   investigación penal? ¿En qué momento procesal se invoca como
   eximente?

4. **¿Qué jurisprudencia hay** sobre PJ condenadas tras Ley 20.393?
   ¿Cuál es el caso emblemático que se cita en defensa / acusación?

5. **¿Las PYMES tienen régimen reducido** o aplican las mismas
   exigencias de MPD que grandes empresas?

6. **¿La auto-denuncia de la PJ** (Art. xxx) puede ser **suficiente para
   eximir** de pena, o solo atenúa?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| Art. 1 — catálogo delitos | ⚠️ no verificada contra texto post-21.595 |
| Art. 2 — sujetos obligados | ⚠️ no verificada |
| Art. 3 — atribución | ⚠️ no verificada |
| Art. 4 — MPD | ⚠️ no verificada |
| Art. 14 — penas + cuantías | ⚠️ no verificada — ver H3 |
| URL BCN id=1008668 | ⚠️ BCN no respondió |

## Sugerencias estructurales

- **Archivo separado** `ley-20393-rppj-catalogo-delitos.md` con la
  lista completa de delitos atribuibles + agrupación por sector (para
  matriz de riesgos).
- **Plantilla de matriz de riesgos** anexa para construcción de MPD.
- **Ejemplos** específicos:
  - PJ certificada vs no certificada en sentencia penal.
  - Auto-denuncia con efecto eximente.
  - PJ con MPD que falla en operación.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #11.
- **Respuesta del validador**: pendiente.
