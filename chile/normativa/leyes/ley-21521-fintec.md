---
norma: Ley 21.521
slug: ley-21521-fintec
titulo_oficial: Promueve la competencia e inclusión financiera a través de la innovación y tecnología en la prestación de servicios financieros
publicacion: 2023-01-04
fuente_oficial: https://www.bcn.cl/leychile/navegar?idNorma=1187323
ultima_modificacion: 2023-01-04 (vigencia escalonada con reglamentos CMF)
vigencia: vigente con escalonamiento (Sistema Financiero Abierto desde 2025)
materia:
  - servicios financieros tecnológicos (Fintec)
  - sistema financiero abierto (open finance)
  - crowdfunding
  - asesoría automatizada
  - intermediación de instrumentos financieros
capa: 3
relacionada_per:
  - ley-18045-mercado-valores
  - ley-19913-lavado-activos
  - ley-19628-proteccion-datos
estado_revision: borrador-no-validado
validador: null
fecha_validacion: null
---
# Ley 21.521 — Ley Fintec

> **Borrador no validado.** Pendiente de revisión por abogado financiero.

## Resumen

La Ley 21.521 (2023), conocida como **"Ley Fintec"**, crea el marco regulatorio
para los **servicios financieros tecnológicos** en Chile. Introduce categorías
de licencia ante la **CMF**, establece el **Sistema Financiero Abierto (SFA /
open finance)** y moderniza el régimen aplicable a fintechs.

Vigencia escalonada: licencias desde 2024; SFA pleno desde 2025; régimen
sancionatorio en transición.

## Estructura

| Título | Materia |
|---|---|
| I | Disposiciones generales (definiciones, ámbito) |
| II | Servicios financieros tecnológicos (categorías y licencias) |
| III | Sistema Financiero Abierto (SFA) |
| IV | Modificaciones a otras leyes |
| V | Sanciones y disposiciones varias |

## Conceptos clave

| Concepto | Definición operativa |
|---|---|
| Servicio financiero tecnológico | Servicios financieros prestados con uso intensivo de TIC |
| CMF | Comisión para el Mercado Financiero (autoridad reguladora) |
| Licencia Fintec | Autorización específica según categoría |
| Sistema Financiero Abierto (SFA) | Compartir datos financieros del cliente con su consentimiento entre entidades |
| Proveedor de información | Quien tiene los datos (banco, AFP, etc.) |
| Proveedor de servicios basados en información | Quien los procesa con consentimiento |
| Cliente financiero | Usuario de los servicios |
| Iniciador de pago | Proveedor que origina pago en nombre del cliente |

## Categorías de servicios Fintec (Título II)

Cada categoría tiene **licencia CMF** específica, requisitos de capital,
conducta, transparencia, prevención LAFT.

### 1. Plataformas de financiamiento colectivo (crowdfunding)

- **Crowdlending**: préstamos colectivos.
- **Crowdequity**: inversión colectiva en sociedades.
- Capital mínimo + procedimientos.

### 2. Sistemas alternativos de transacción

- Plataformas de transacción de valores no listados.
- Cripto-activos (con régimen específico).

### 3. Asesoría crediticia y de inversión

- Robo-advisors automatizados.
- Asesoría algorítmica con o sin intervención humana.

### 4. Custodia de instrumentos financieros

- Custodia digital de activos.

### 5. Enrutamiento de órdenes

- Conexión de cliente con mercado vía API.

### 6. Iniciación de pagos

- Originar transferencias en nombre del cliente, vía SFA.

### 7. Provisión de información financiera (account info)

- Agregación de datos financieros del cliente desde múltiples entidades.

## Sistema Financiero Abierto (SFA — Título III)

Régimen análogo al **Open Banking** europeo / brasilero.

### Principios

- **Portabilidad** de datos: el cliente puede llevar sus datos a otra
  entidad.
- **Consentimiento explícito**, granular y revocable.
- **Interoperabilidad técnica** (APIs estandarizadas).
- **Seguridad** (autenticación, encriptación).

### Datos involucrados

- Datos de productos contratados (cuenta, créditos, AFP, seguros).
- Movimientos transaccionales.
- Información de identificación.
- Información sobre solicitudes y precios.

### Iniciación de pagos

Permite a tercero iniciar un pago desde la cuenta del cliente bajo
consentimiento (sin intermediación de redes de tarjetas o efectivo).

### Coexistencia con LPDP

- **Ley 21.521** + **Ley 19.628 / 21.719** rigen en conjunto.
- El consentimiento bajo SFA es un sub-tipo del consentimiento LPDP, con
  exigencias adicionales.

## Obligaciones de los proveedores

- **Licencia CMF** vigente.
- **Capital mínimo** según categoría.
- **Gobierno corporativo** robusto.
- **Conoce a tu cliente (KYC)** + diligencia debida.
- **Prevención lavado de activos** (cumple Ley 19.913).
- **Continuidad operacional** + ciberseguridad (Ley 21.663).
- **Transparencia y deber de información** al cliente.
- **Custodia segura** de datos y activos.
- **Reporte regular** a CMF.

## Sanciones

| Infracción | Sanción |
|---|---|
| Operar sin licencia | Multa hasta UF 100.000 + clausura |
| Incumplimiento operativo | Multa proporcional |
| Falla en protección de datos / SFA | Multa + revocación de licencia |
| Reincidencia | Revocación + acciones penales si aplican |

Procedimiento: sumario CMF. Recurso de reclamación ante Corte de
Apelaciones.

## Conexiones con otras normas

- [`ley-18045-mercado-valores`](ley-18045-mercado-valores.md) — interacción
  con LMV; muchos servicios Fintec son variaciones de intermediación.
- [`ley-19628-proteccion-datos`](ley-19628-proteccion-datos.md) +
  [`ley-21719-modificacion-lpd`](ley-21719-modificacion-lpd.md) — datos
  personales en SFA.
- [`ley-19913-lavado-activos`](ley-19913-lavado-activos.md) — sujetos
  obligados ampliados.
- [`ley-21663-ciberseguridad`](ley-21663-ciberseguridad.md) — fintechs
  pueden calificar como OIV.
- **Ley 21.314** — gobierno corporativo SA abierta (aplica a fintechs SA).
- **NCG CMF** específicas para Fintec.

## Cuándo invocar esta norma

- Diseño / lanzamiento de fintech en Chile.
- Tramitación de licencia CMF.
- Operación bajo SFA: rol como proveedor, iniciador, agregador.
- Compliance combinado: LPDP + AML + ciberseguridad + LMV + LPC.
- Defensa frente a sumario CMF.
- Análisis de operaciones cripto en zona Fintec.

## Disclaimers

- Borrador no validado.
- Reglamentación CMF se publicó y publica progresivamente; verificar NCG
  Fintec más recientes.
- Sistema en construcción operativa; varias APIs y estándares aún se
  consolidan.
- Para estructuración real de fintech, consultar abogados especializados +
  CMF.
