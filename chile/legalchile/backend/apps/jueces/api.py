from ninja import Router
from ninja_jwt.authentication import JWTAuth

from . import service

# Toda la app requiere sesión autenticada (JWT). La capa de comportamiento
# judicial (pública) va por JSON estático del frontend; esto es SOLO la capa
# sensible (identidad/patrimonio/familia).
router = Router(tags=["jueces"], auth=JWTAuth())


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
