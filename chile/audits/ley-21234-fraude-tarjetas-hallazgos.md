---
archivo_revisado: ley-21234-fraude-tarjetas
fecha_revision: 2026-05-20
revisor_tecnico: Claude Opus 4.7 (no abogado, revisión técnica solamente)
issue_validacion: "#21"
estado: pendiente-de-validador
---

# Auto-revisión técnica: Ley 21.234 (Fraude tarjetas)

## Hallazgos críticos

### H1 — Tope de 35 UF para reembolso íntegro

El perfil declara tope de 35 UF para PN. **Verificar**:
- ¿35 UF por operación o 35 UF acumuladas por evento?
- ¿La cifra se actualizó por reglamento posterior?
- Régimen PYMEs: 60 UF — confirmar.

### H2 — Plazo de 5 días hábiles para reembolso

Confirmar:
- ¿5 días desde el reclamo formal o desde el aviso del fraude?
- ¿Se suspende durante investigación del emisor (15 días)?
- Sanción al emisor por incumplimiento del plazo.

### H3 — Carga de prueba invertida

El perfil destaca la inversión de carga (emisor debe probar culpa
grave). **Verificar**:
- ¿Aplica también a fraude electrónico (phishing) o solo a tarjeta
  física?
- Casos donde la carga vuelve al usuario.

## Hallazgos técnicos

T1: Frontmatter usa `relacionada_per` ✅.
T2: Cruces a complementar: `ley-21663-ciberseguridad` (fraude
informático), `ley-19628-proteccion-datos` (datos comprometidos).

## Preguntas abiertas

1. ¿La **CMF** ha emitido **NCG específica** sobre autenticación
   reforzada post-Ley 21.234?
2. ¿La protección **alcanza a billeteras digitales** (Mach, Tenpo,
   MercadoPago)?
3. ¿La protección **alcanza a transferencias electrónicas** entre
   personas (no solo tarjetas)?
4. Régimen de **fraude entre cuentas del mismo titular** vs entre
   distintos titulares.
5. ¿La **acción colectiva** vía SERNAC se ha usado para masivos?

## Referencias

| Cita | Verificada |
|---|---|
| URL BCN id=1146361 | ⚠️ BCN no respondió |
| 35 UF / 60 UF tope | ⚠️ ver H1 |
| 5 días reembolso | ⚠️ ver H2 |

## Estado: pendiente-de-validador.
