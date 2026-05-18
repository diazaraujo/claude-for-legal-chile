# claude-for-legal · Adaptación Chile

Configuración de Claude para práctica legal chilena. Se diferencia del fork argentino
en una decisión arquitectónica: **el eje del sistema es el corpus normativo chileno**
(códigos, leyes, decretos), no los perfiles por rama del derecho. Esto es coherente con
la tradición civil law que se cita por artículo, no por caso.

> **Estado:** Work in progress. Los archivos llevan `estado_revision` en su
> frontmatter; solo los marcados `validada` están revisados por abogado habilitado.

---

## Estructura

```
chile/
├── CLAUDE.md                       Perfil general — cargar en todo Project
├── README.md                       Este archivo
├── CHANGELOG.md                    Historial de cambios
│
├── normativa/                      🆧 SPINE — corpus normativo chileno
│   ├── README.md                   Esquema de archivo de norma
│   ├── codigos/
│   │   ├── 00-indice.md
│   │   ├── codigo-trabajo.md       (DFL 1/2002)
│   │   ├── codigo-civil.md         pendiente
│   │   ├── codigo-comercio.md      pendiente
│   │   └── ...
│   ├── leyes/
│   │   ├── 00-indice.md
│   │   ├── ley-19628-proteccion-datos.md
│   │   ├── ley-21719-modificacion-lpd.md
│   │   ├── ley-21643-acoso-laboral.md
│   │   └── ...
│   ├── decretos/
│   │   └── 00-indice.md
│   └── dictamenes/                 v2 — DT, SII, Contraloría
│
├── perfiles/                       Vistas por rama (orquestan normativa)
│   ├── civil.md                    pendiente
│   ├── laboral.md                  pendiente
│   ├── societario.md               pendiente
│   └── ...
│
├── skills/                         Transversales
│   ├── diagnostico.md              ruteo consulta → ley(es) relevantes
│   ├── citas-verificables.md       patrón de cita normativa chilena
│   └── plazos.md                   plazos hábiles vs corridos
│
├── ejemplos/                       Casos canónicos por rama
│
├── fuentes.md                      BCN, PJUD, DT, SII, etc.
└── setup-interview.md              Configuración inicial del Project del usuario
```

---

## Por qué normativa-spine

1. **Tradición civil law** — los abogados chilenos citan "Art. 1545 CC" o "Art. 162
   del Código del Trabajo", no precedentes. Las normas son la fuente.
2. **Mantenimiento centralizado** — cuando Ley 21.719 entra en vigencia el 2026-12-01,
   se actualiza un archivo (`leyes/ley-21719-modificacion-lpd.md`) y todos los
   perfiles que la referencian heredan.
3. **Validación granular** — cada norma se valida con experto en ella, no por rama
   transversal. Reduce el costo de validación legal.
4. **Razonamiento sistémico** — cada archivo declara conexiones (`relacionada_con:`).
   El LLM razona sobre el sistema normativo, no sobre piezas aisladas.

---

## Qué opera bajo este corpus

**Códigos:** Código Civil · Código del Trabajo · Código de Comercio · Código
Tributario · CPC · CPP · Código Penal · Código Orgánico de Tribunales.

**Leyes especiales prioritarias:** Ley 19.628 + Ley 21.719 (datos personales) · Ley
16.744 (accidentes del trabajo) · Ley 20.123 (subcontratación) · Ley 21.561
(reducción jornada 40h) · Ley 21.643 (Ley Karin — acoso) · Ley 21.015 (inclusión) ·
Ley 21.220 (teletrabajo) · Ley 18.046 (sociedades anónimas) · Ley 19.886 (compras
públicas) · Ley 19.496 (consumidor) · Ley 20.720 (concursal).

**Fuera de alcance v1:** derecho indígena (Ley 19.253), aguas (Cód. Aguas), minero
(Cód. Minería), aeronáutico, marítimo.

Lista completa en `normativa/codigos/00-indice.md` y `normativa/leyes/00-indice.md`.

---

## Reglas de uso

- **No reemplaza al abogado.** Todo output es un borrador para revisión por abogado
  habilitado en Chile. El sistema explicita esto en cada interacción crítica y NO
  entrega asesoría legal directa al usuario final.
- **Fuente autoritativa = BCN/LeyChile.** Este corpus es metadata + síntesis útil.
  Para texto literal e historial completo de modificaciones, siempre verificar contra
  https://www.bcn.cl/leychile.
- **Estado de revisión declarado.** Cada norma lleva en su frontmatter
  `estado_revision: <borrador-no-validado | revision-legal-en-curso | validada>`. Solo
  archivos `validada` pueden invocarse sin disclaimer adicional.

---

## Origen

Fork de [`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal)
(Apache-2.0). Patrón estructural inspirado en
[`cristianaboitiz-eng/claude-for-legal-argentina`](https://github.com/cristianaboitiz-eng/claude-for-legal-argentina),
con divergencia arquitectónica: normativa-spine en lugar de perfiles-spine.

Mantenido por [Unholster](https://unholster.com) bajo dirección de
[Antonio Díaz-Araujo](https://github.com/diazaraujo).

---

## Disclaimers

- **No constituye asesoría legal.** El sistema produce borradores y análisis
  auxiliares; la responsabilidad profesional recae en el abogado que revisa, firma y
  aplica el output.
- **Verificación humana obligatoria** de citas normativas y jurisprudenciales contra
  fuentes oficiales (BCN, PJUD).
- **Jurisdicción asumida.** Derecho chileno aplicable salvo indicación expresa.
- **Vigencia y actualización.** El corpus se actualiza; verificar
  `ultima_modificacion` del frontmatter al usar.

---

## Licencia

Apache-2.0 (heredada del upstream). Ver [LICENSE](../LICENSE) en raíz del repo.
