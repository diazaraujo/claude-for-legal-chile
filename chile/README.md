# claude-for-legal · Adaptación Chile

Configuración de Claude para práctica legal chilena. El material se construye sobre
derecho chileno: Código Civil, Código del Trabajo, Código de Comercio, Ley 19.628 y
Ley 21.719 (datos personales), CPC, CPP, Código Tributario, Ley 18.046 (SA),
Ley 20.720 (concursal), entre otras. No requiere ningún repositorio externo para
funcionar; puede usarse de forma autónoma desde Claude.ai Projects o Claude Code.

> **Estado:** Work in progress. Los perfiles por rama del derecho se publicarán a
> medida que sean revisados por abogado habilitado en Chile. Ver `CHANGELOG.md`.

---

## Estructura prevista

```
chile/
  CLAUDE.md                         # Perfil general — cargar en todo Project
  CHANGELOG.md                      # Historial de cambios normativos y del sistema
  marcadores-GLOSARIO.md            # Glosario canónico de marcadores
  setup-interview.md                # Entrevista de configuración inicial
  setup-output-TEMPLATE.md          # Template de output de la entrevista
  diagnostico-SKILL.md              # Skill de diagnóstico previo (transversal)
  diagnostico-casos-prueba.md       # Casos de prueba del skill
  red-flags-contratos.md            # Alertas para revisión de contratos
  contratos-CLAUDE.md               # Perfil unificado de revisión y redacción
  administrativo-CLAUDE.md          # Derecho administrativo (Ley 19.880)
  civil-CLAUDE.md                   # Derecho civil (Código Civil chileno)
  concursal-CLAUDE.md               # Concursal (Ley 20.720)
  familia-CLAUDE.md                 # Derecho de familia (Ley 19.947, Tribunales de Familia)
  laboral-CLAUDE.md                 # Derecho del trabajo (Código del Trabajo)
  penal-CLAUDE.md                   # Derecho penal (CP, CPP)
  societario-CLAUDE.md              # Societario (Ley 18.046 SA, Ley 3.918 SRL)
  tributario-CLAUDE.md              # Tributario (DL 830, IVA, renta)
  ejemplos-civil.md                 # Casos de daños y responsabilidad civil chilena
  ejemplos-laboral.md               # Liquidaciones, finiquito, tutela laboral
  ejemplos-societario.md            # Due diligence y pactos de accionistas
  fuentes.md                        # Fuentes primarias y conectores MCP
```

---

## Qué hace este sistema

**Opera bajo:**

- **Código Civil chileno** para contratos, obligaciones y responsabilidad civil
- **Código del Trabajo** para materia laboral (DT, juzgados del trabajo, tutela laboral)
- **Ley 19.628** y **Ley 21.719** (vigente desde 2026) para datos personales
- **CPC** (Código de Procedimiento Civil) y **CPP** (Código Procesal Penal)
- **Código de Comercio** y **Ley 18.046** para sociedades anónimas
- **Ley 20.720** para procedimientos concursales (reorganización y liquidación)
- **Ley 19.880** para procedimiento administrativo
- **Ley 19.947** y reglas de Tribunales de Familia
- **Código Tributario (DL 830)** y leyes de IVA / renta

**No reemplaza al abogado.** Todo output es un borrador para revisión por
abogado habilitado en Chile. El sistema explicita esto en cada interacción crítica
y NO entrega asesoría legal directa al usuario final.

---

## Origen

Fork de [`anthropics/claude-for-legal`](https://github.com/anthropics/claude-for-legal)
(Apache-2.0). Patrón estructural inspirado en
[`cristianaboitiz-eng/claude-for-legal-argentina`](https://github.com/cristianaboitiz-eng/claude-for-legal-argentina).

Iniciativa mantenida por [Unholster](https://unholster.com) bajo dirección de
[Antonio Díaz-Araujo](https://github.com/diazaraujo).

---

## Disclaimers

- **No constituye asesoría legal.** El sistema produce borradores y análisis
  auxiliares; la responsabilidad profesional recae siempre en el abogado que
  revisa, firma y aplica el output.
- **Verificación humana obligatoria.** Las citas normativas y jurisprudenciales
  emitidas por el sistema deben ser verificadas contra fuentes oficiales (LeyChile
  de la BCN para normas, Poder Judicial para jurisprudencia).
- **Jurisdicción asumida.** El sistema asume derecho chileno aplicable salvo que
  el operador indique expresamente jurisdicción extranjera. No aplica doctrinas
  argentinas, españolas o de common law por defecto.

---

## Licencia

Apache-2.0 (heredada del upstream). Ver [LICENSE](../LICENSE) en raíz del repo.
