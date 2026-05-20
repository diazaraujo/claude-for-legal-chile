---
archivo_revisado: ley-21713-reforma-tributaria-2024
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#10"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.713 (Reforma Tributaria 2024)

> Revisión técnica (consistencia, gaps), NO legal. Alerta de
> volatilidad activa: reglamentos SII en publicación progresiva.

## Resumen ejecutivo

El perfil cubre los 5 componentes principales (NGA, sanciones,
plataformas, DJ, BEPS) + tabla de vigencias escalonadas. Hallazgos:

- **5 críticos** para validador tributarista.
- **2 técnicos**.
- **8 preguntas abiertas** (técnicas — tributarista experto).
- BCN no respondió.

## Hallazgos críticos — decisión del validador

### H1 — NGA: Comité Antielusión vs Director Nacional SII

El perfil declara:
> Procedimiento: aprobación del Director Nacional SII previo dictamen
> del Comité Antielusión.

**Observación**: El **Comité Asesor del SII** sobre NGA ya existía con
la Ley 20.780. La 21.713 lo reforma. Es importante distinguir:

- Composición del Comité (¿internos SII, externos, mixto?).
- Vinculatoriedad del dictamen (¿consultivo o vinculante?).
- Posibilidad de impugnar la calificación de elusión.

**Acción sugerida**:
- Documentar composición + procedimiento exacto post-21.713.
- Aclarar el efecto del dictamen en el procedimiento.

### H2 — Multas hasta 300% del impuesto eludido

El perfil declara:
> Infracciones graves: hasta 300% del impuesto eludido + acción penal
> cuando hay dolo.

**Observación**: Verificar la cuantía exacta. Las multas tributarias
históricas estaban en rangos del 50%-100%. Un techo del 300% es un
cambio estructural muy fuerte.

**Acción sugerida**:
- Confirmar techo + base de cálculo.
- Distinguir multa administrativa vs sanción penal (Art. 97 N° 4 CT).

### H3 — Plataformas digitales: obligaciones de retención

El perfil declara:
> Plataformas intermediarias (Uber, Cornershop, Mercado Libre, etc.):
> obligaciones de retención + reporte al SII.

**Observación**: Esto es técnicamente importante. Hay tres tipos de
plataforma a distinguir:

1. **Plataformas extranjeras** que prestan servicios digitales en Chile
   (Netflix, Spotify, AWS) → IVA digital.
2. **Plataformas chilenas o foráneas** que intermedian transacciones
   B2C (Uber, Cornershop, MercadoLibre) → retención + reporte.
3. **Plataformas P2P** (Airbnb, BlaBlaCar) → régimen específico.

El perfil mezcla estos casos. **Acción sugerida**:
- Separar los 3 regímenes.
- Documentar obligaciones específicas + plazos.

### H4 — Vigencia escalonada: NGA "Octubre 2025"

El perfil declara:
> | NGA reforzada | Octubre 2025 |

**Observación**: Si la ley entró en vigor el 24-octubre-2024, y la NGA
reforzada entra "octubre 2025", esto sería **+1 año desde publicación**.
Pero algunos componentes pueden tener vigencia distinta.

**Acción sugerida**:
- Confirmar fecha exacta de cada componente.
- Especificar **día** (no solo mes) para NGA.

### H5 — Renta atribuida residual eliminada

El perfil declara:
> Renta atribuida residual: eliminada definitivamente.

**Observación**: La "renta atribuida" fue uno de los regímenes que
introdujo Ley 20.780 (2014) + ajustó Ley 20.899 (2016) + 21.210 (2020).
Su "eliminación residual" tiene implicancias para empresas que la
mantenían en transición.

**Acción sugerida**:
- Confirmar qué exactamente queda "eliminado" (todos los Art. 14 A?
  régimen específico ProPyme?).
- Documentar transición para empresas que estaban en régimen anterior.

## Hallazgos técnicos

### T1 — Frontmatter ya usa `relacionada_per` ✅

¡Excelente! Este perfil **ya usa el campo canónico**. No requiere
corrección.

### T2 — Cruces a complementar

`relacionada_per` declara 4 normas. Faltan:
- `ley-21000-cmf` — para sanciones a empresas reguladas.
- `ley-19913-lavado-activos` — cruce con planificación agresiva.
- `ley-21591-royalty-minero` — para mineras grandes.
- `codigo-penal` — Art. 470 + delitos económicos.

## Preguntas abiertas para el validador

1. **¿La NGA tiene "lista negra" de operaciones**, o solo criterios
   abiertos? ¿Cómo se predice exposición?

2. **¿La Norma Especial Antielusión (NEA)** del Art. 4 ter sigue
   coexistiendo con la NGA reforzada, o queda subsumida?

3. **¿Las DJ por criptoactivos** tienen umbral de monto? ¿Aplican a
   exchanges extranjeros usados por chilenos?

4. **¿La acción penal por delito tributario** (Art. 97 N° 4) ahora se
   ejerce más automáticamente bajo el régimen 21.595 + 21.713, o sigue
   siendo discrecional del SII?

5. **¿La elusión vía paraísos fiscales** tiene régimen específico
   reforzado en 21.713 (más allá de CRS / BEPS)?

6. **¿La sanción "publicación de la calificación de elusión"** está en
   el texto, o quedó solo en discusión legislativa?

7. **¿Los honorarios profesionales prestados por SpA bajo Ley 21.420**
   tienen alguna interacción con la NGA si la estructura SpA es para
   evitar IVA?

8. **¿BEPS Pilar 2 (mínimo global 15%)** está implementado
   completamente o queda en transición?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=1207870 | ⚠️ BCN no respondió |
| Fecha publicación 2024-10-24 | ⚠️ asumida |
| Art. 4 bis y ss. CT (NGA) | ⚠️ no verificada |
| Art. 14 D LIR (ProPyme) | ⚠️ no verificada |
| Vigencias escalonadas | ⚠️ confirmar día exacto cada item |
| Cifras de multa | ⚠️ ver H2 |

## Sugerencias estructurales

- **Tabla de vigencia con día exacto** por componente (no solo mes).
- **Ejemplo** de aplicación de NGA con un caso hipotético.
- **Checklist de impacto** para distintos tipos de empresa (Pyme,
  mediana exportadora, multinacional con BEPS).
- **Mapa de fiscalización SII** post-21.713: programas + sectores
  prioritarios.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #10.
- **Respuesta del validador**: pendiente.
