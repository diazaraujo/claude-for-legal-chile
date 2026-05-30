# Casos de verificación (evals) — claude-for-legal-chile

Casos de control con solución conocida para verificar que los perfiles y skills
detectan lo que un abogado chileno detectaría. Si el sistema no lo detecta, el
perfil/skill tiene un problema que corregir.

> Método adaptado del framework de evals del fork argentino. **Contenido 100%
> chileno**: normativa, fueros y criterios de Chile, recuperados/verificables
> contra el corpus. Cero contenido argentino.

No es automatización: el abogado pega `caso.md` en el sistema, lee el análisis y
lo compara contra `rubrica.md` (puntos binarios) y `resultado.md` (solución
esperada).

## Estructura de un caso

```
evals/
  README.md
  <area>-<tema-corto>/
    caso.md       # Pieza procesal/contrato anonimizado que se pega al sistema
    rubrica.md    # Puntos que el sistema DEBE detectar (binario: lo detecta o no)
    resultado.md  # Solución esperada / criterios mínimos de aprobación + citas
```

## Reglas para crear casos
1. **Anonimizado**: sin nombres, RUT ni datos reales (placeholders neutros).
2. **Solución conocida y verificable**: la `rubrica` se apoya en normativa/
   jurisprudencia que existe en el corpus (cita el artículo/rol/dictamen).
3. **Binario**: cada punto de la rúbrica se detecta o no; sin grises.
4. **Cubre las skills de corpus**: un buen caso ejercita [[verificar-cita]],
   [[buscar-jurisprudencia]] o [[buscar-dictamen]].

## Casos
- `laboral-fuero-maternal-desafuero/` — despido de trabajadora con fuero maternal
  sin desafuero judicial previo (nulidad). Ejercita perfil laboral + verificar-cita.
