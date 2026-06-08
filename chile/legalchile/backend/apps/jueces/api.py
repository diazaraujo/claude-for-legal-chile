from ninja import Router

from . import service

# Capa de jueces PÚBLICA (identidad/patrimonio/red familiar desde fuentes
# públicas + Mallas). Antes gateada por JWT; abierta por decisión de producto.
router = Router(tags=["jueces"])


@router.get("/disponible")
def disponible(request):
    """Indica si la capa enriquecida está cargada (para que el frontend decida
    si muestra las secciones sensibles)."""
    return {"disponible": service.available()}


@router.get("/{juez_key}/perfil")
def perfil(request, juez_key: str):
    """Capa sensible del juez: identidad, patrimonio y red familiar (vía Mallas),
    gateada por confianza de rutificación. Requiere usuario autenticado."""
    data = service.perfil(juez_key)
    if data is None:
        return {"juez_key": juez_key, "identificado": False, "sin_datos": True}
    return data
