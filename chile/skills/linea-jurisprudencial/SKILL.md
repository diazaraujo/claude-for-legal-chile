---
name: linea-jurisprudencial
description: >
  Construye la línea jurisprudencial/administrativa sobre un punto de derecho
  chileno: agrupa fallos y dictámenes recuperados del corpus, ordena por fecha,
  identifica el criterio dominante, los matices y los quiebres. Usar cuando el
  usuario pide "cómo ha evolucionado el criterio sobre X", "línea de la Corte
  Suprema en Y", "está consolidada la jurisprudencia sobre Z".
argument-hint: "[punto de derecho]"
---

# /linea-jurisprudencial

## Cuándo corre
El usuario quiere una síntesis evolutiva, no un fallo aislado.

## Qué hacer
1. **Recolectar** con [[buscar-jurisprudencia]] y [[buscar-dictamen]] todo lo
   que el corpus tenga sobre el punto (over-fetch: 20-50 resultados, modo hybrid).
2. **Ordenar** cronológicamente por fecha de cada fallo/dictamen.
3. **Sintetizar**:
   - **Criterio dominante** actual (con los roles/números que lo sostienen).
   - **Matices** por sala/tribunal/materia.
   - **Quiebres o cambios** de criterio (un fallo que se aparta), si el corpus lo evidencia.
   - **Estado**: ¿consolidada, dividida, en formación?
4. **Citar** cada eslabón con su rol/número exacto (vía [[verificar-cita]]).

## Reglas
- Solo afirmar "línea consolidada" si hay varios fallos concordantes recuperados.
  Si son pocos o contradictorios, decir "criterio no uniforme / en desarrollo".
- NO inventar evolución: si el corpus solo tiene fallos recientes, no afirmar qué
  decía la Corte hace 20 años sin respaldo.
- Separar holding de obiter; la línea se construye sobre holdings.
- Marcar explícitamente "NO verificado" cualquier inferencia que no tenga fallo de respaldo.
