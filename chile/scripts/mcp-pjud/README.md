# mcp-pjud — STUB

> **Estado: stub.** El portal `juris.pjud.cl` es una SPA con reCAPTCHA
> que invalida scraping HTTP simple.

## Hallazgos investigación 2026-05-22

- URL base: `https://juris.pjud.cl/busqueda`
- App: Vue/SPA — render del lado cliente.
- API endpoint `/api/buscador` también devuelve HTML (no JSON).
- `fetch('https://juris.pjud.cl/biscolab-recaptcha/validate?token_juris=...')`
  visible en HTML — protección reCAPTCHA antes de cada query.

## Vías técnicas para implementar

1. **Playwright/Selenium**: browser headless que ejecute JS + resuelva
   reCAPTCHA (anti-captcha service o token manual).
2. **Reverse engineer del token reCAPTCHA**: el portal genera el token
   client-side; si se identifica el `site_key` se puede usar 2captcha.
3. **API privada CAPJ**: la Corporación Administrativa del Poder
   Judicial puede tener API formal — contacto institucional Unholster.
4. **Datos preprocesados externos**: existen bases comerciales (LexisNexis,
   Westlaw Chile) que ya scrapean PJUD. No public.

## Decisión

Diferido hasta tener canal formal con CAPJ o adoptar Playwright.
Mientras tanto, perfiles capa 3 citan jurisprudencia con disclaimer
"verificar en juris.pjud.cl".

Otros conectores PJUD que SÍ son factibles:
- **Tribunal Constitucional** (`tribunalconstitucional.cl/...`) —
  publicación de fallos en HTML estable.
- **Compendios jurisprudencia DDHH** del Portal — HTML público sin
  reCAPTCHA en algunos paths.

Pendiente investigación de esos.
