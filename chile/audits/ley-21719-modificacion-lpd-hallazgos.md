---
archivo_revisado: ley-21719-modificacion-lpd
fecha_revision: 2026-05-19
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#9"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.719 (Modificación LPDP + APDP)

> Revisión técnica (consistencia, gaps), NO legal. El validador legal
> resuelve las decisiones sustantivas.

## Resumen ejecutivo

El perfil está bien estructurado, cubre la mayoría de cambios
estructurales y advierte explícitamente sobre la vigencia diferida.
Hallazgos:

- **4 hallazgos críticos** para validador.
- **2 hallazgos técnicos** (consistencia).
- **7 preguntas abiertas** (zonas técnicas que requieren especialista
  en privacidad).
- **BCN no respondió** durante la revisión técnica.

## Hallazgos críticos — decisión del validador

### H1 — Cuantía sancionatoria: cifras ilustrativas vs cifras del texto

El perfil declara:
> | Leves | Hasta 100 UTM |
> | Graves | 101 a 5.000 UTM |
> | Gravísimas | 5.001 a 20.000 UTM |
>
> (Las cuantías son ilustrativas; el texto definitivo y los reglamentos
> APDP precisan los montos.)

**Observación**: Es honesto declararlo como ilustrativo, pero el corpus
debe tener las cifras **exactas** del texto promulgado. Algunas fuentes
externas mencionan multas en **UF** (no UTM) y hasta **20.000 UTM** o
hasta el **4% de los ingresos anuales** (similar a GDPR).

**Acción sugerida**:
- Verificar contra el texto promulgado.
- Confirmar unidad (UF vs UTM).
- Documentar cuantías por tipo de infracción.

### H2 — Vigencia: 1° de diciembre 2026 vs "dos años desde publicación"

El perfil dice:
> Su entrada en vigencia plena es el **1 de diciembre de 2026**,
> otorgando dos años para la adecuación de los responsables.

**Observación**: 13-diciembre-2024 + 2 años = **13-diciembre-2026**, no
1-diciembre-2026. La discrepancia puede deberse a una norma transitoria
específica.

**Acción sugerida**:
- Verificar fecha de vigencia exacta contra texto del art. transitorio.
- Si la fecha es **2026-12-01** (en lugar de 2026-12-13), documentar la
  base legal de ese día específico.

### H3 — APDP "ad-hoc" o servicio público

El perfil declara:
> APDP - autoridad de control independiente

> Servicio público descentralizado, con personalidad jurídica y
> patrimonio propio.

**Observación**: "Independiente" + "servicio público descentralizado"
son categorías distintas en derecho administrativo chileno. Un servicio
descentralizado depende formalmente del Ejecutivo (con autonomía
funcional). Un órgano "independiente" implica autonomía constitucional
(como CGR, INDH).

**Acción sugerida**:
- Confirmar la naturaleza precisa de la APDP según el texto.
- Si es "descentralizada", aclarar que la "independencia" es funcional
  (no constitucional).

### H4 — Datos de menores: edad de consentimiento

El perfil declara:
> Datos de menores: Protección reforzada. Consentimiento del
> representante legal cuando aplique.

**Observación**: La GDPR define edad de consentimiento digital (13-16
años según país). La 21.719 probablemente define una edad específica
(creo es **14 años**) bajo la cual el consentimiento del representante
legal es obligatorio.

**Acción sugerida**:
- Confirmar la edad de consentimiento digital en la 21.719.
- Especificar el régimen para distintas franjas etarias.

## Hallazgos técnicos (no requieren abogado)

### T1 — Frontmatter: `relacionada_con` vs `relacionada_per`

Mismo problema que la Ley Karin: el frontmatter usa `relacionada_con`
pero el glosario `MARCADORES.md` establece `relacionada_per` como
canónico.

**Acción**: cambiar a `relacionada_per`.

### T2 — Cruces normativos incompletos

El perfil cita solo `ley-19628-proteccion-datos` + `codigo-penal` en
`relacionada_con`. Faltan cruces obvios:

- `ley-21663-ciberseguridad` — notificación de brechas + ANCI.
- `ley-19496-consumidor` — datos personales como bien de consumo.
- `ley-21234-fraude-tarjetas` — cruce con fraude electrónico.
- `ley-21430-garantias-nna` — protección reforzada datos NNA.
- `dfl-725-codigo-sanitario` — datos sensibles de salud.

**Acción**: ampliar `relacionada_per` para reflejar el ecosistema.

## Preguntas abiertas para el validador

1. **¿La obligación de DPO es para qué umbral exacto** de tratamiento?
   (volumen de titulares, sectores específicos, tratamientos
   automáticos a gran escala).

2. **¿La transferencia internacional a EEUU** está cubierta por algún
   esquema de adecuación específico** (similar al Data Privacy Framework
   post-Schrems II) o requiere cláusulas tipo + análisis caso a caso?

3. **¿El plazo de respuesta a derechos ARCO** se mantiene en 20 días
   hábiles** (como en 19.628) o cambia con la 21.719?

4. **¿Plazo de notificación de brecha**: 72 horas (similar a GDPR) o
   distinto?

5. **¿Cuál es el régimen transitorio** para tratamientos en curso al
   2026-12-01? ¿Hay obligación de reconfirmar consentimientos
   recolectados bajo el régimen previo?

6. **¿La APDP sustituye al rol del Consejo para la Transparencia
   (CPLT)** en materia de datos personales del sector público, o ambos
   coexisten?

7. **¿Hay régimen específico para sectores regulados** (bancos sujetos a
   CMF, salud sujeta a Superintendencia de Salud) que pueda generar
   conflicto / doble fiscalización?

## Referencias verificadas / no verificadas

| Cita | Verificada |
|---|---|
| URL BCN id=1208595 | ⚠️ BCN no respondió en revisión técnica |
| Fecha publicación 2024-12-13 | ⚠️ asumida, no verificada contra DO |
| Fecha vigencia 2026-12-01 | ⚠️ asumida, ver H2 |
| Cuantías UTM (100/5.000/20.000) | ⚠️ ilustrativas — ver H1 |

## Sugerencias estructurales (opcional)

- **Agregar tabla comparativa** 19.628 vigente vs 21.719 vigente con
  columna de impacto operativo (lista de tareas para el responsable).
- **Agregar checklist de adecuación** para el período transitorio
  (próximo a 2026-12-01).
- **Ejemplo cruzado**: agregar caso de respuesta a derecho de
  portabilidad (nuevo derecho) en `chile/ejemplos/privacidad-`.

## Estado

- **Generada**: 2026-05-19.
- **Enviada al validador via issue**: #9.
- **Respuesta del validador**: pendiente.
