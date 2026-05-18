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

Estado del corpus normativo chileno. Solo los archivos marcados ✅ están publicados
como borrador estructurado; ninguno ha pasado validación legal todavía.

### Códigos

| Código | Estado | Archivo |
|---|---|---|
| Código del Trabajo (DFL 1/2002) | ✅ Borrador | [`codigo-trabajo.md`](chile/normativa/codigos/codigo-trabajo.md) |
| Código Civil | ⏳ Pendiente | — |
| Código de Comercio | ⏳ Pendiente | — |
| Código Tributario (DL 830) | ⏳ Pendiente | — |
| Código de Procedimiento Civil | ⏳ Pendiente | — |
| Código Procesal Penal | ⏳ Pendiente | — |
| Código Penal | ⏳ Pendiente | — |

[Ver índice completo](chile/normativa/codigos/00-indice.md) (12 códigos).

### Leyes especiales

| Ley | Materia | Estado |
|---|---|---|
| Ley 19.628 | Protección de datos personales | ✅ [Borrador](chile/normativa/leyes/ley-19628-proteccion-datos.md) |
| Ley 21.719 | Modificación LPDP + creación APDP (vigencia 2026-12-01) | ✅ [Borrador](chile/normativa/leyes/ley-21719-modificacion-lpd.md) |
| Ley 21.643 | Ley Karin — acoso y violencia laboral | ✅ [Borrador](chile/normativa/leyes/ley-21643-acoso-laboral.md) |
| Ley 16.744 | Accidentes del trabajo | ⏳ Pendiente |
| Ley 20.123 | Subcontratación | ⏳ Pendiente |
| Ley 21.561 | Reducción jornada 40h | ⏳ Pendiente |
| Ley 21.015 | Inclusión laboral discapacidad | ⏳ Pendiente |
| Ley 21.220 | Teletrabajo | ⏳ Pendiente |
| Ley 18.046 | Sociedades Anónimas | ⏳ Pendiente |
| Ley 19.886 | Compras públicas | ⏳ Pendiente |
| Ley 19.496 | Consumidor | ⏳ Pendiente |
| Ley 20.720 | Concursal | ⏳ Pendiente |

[Ver índice completo](chile/normativa/leyes/00-indice.md) (19 leyes).

### Perfiles y skills

Capa de orquestación sobre el corpus. Pendientes de redacción una vez que las leyes
que invocan estén validadas.

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
- 🚧 **Fase 1** — Validación legal de las normas publicadas (issue #1) y cobertura de
  10 leyes prioritarias + 3 códigos
- ⏳ **Fase 2** — Perfiles por rama (civil, laboral, societario) + 3 skills
  transversales (diagnóstico, citas verificables, plazos)
- ⏳ **Fase 3** — Release v1.0 público + anuncio + cobertura comparable al fork
  argentino

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
