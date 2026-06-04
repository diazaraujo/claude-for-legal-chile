from ninja import Router

from . import semantic, service

router = Router(tags=["corpus"])


@router.get("/search")
def search(request, q: str, limit: int = 20, source: str = "new-sources"):
    """Búsqueda full-text (keyword) sobre el corpus jurídico chileno (legislación,
    jurisprudencia, dictámenes). source: 'new-sources' (default) o 'corpus'."""
    return {"query": q, "source": source, "results": service.search(q, limit, source)}


@router.get("/semantic")
def semantic_search(request, q: str, limit: int = 20):
    """Búsqueda semántica (vectorial, bge-m3) sobre new-sources. Devuelve los docs
    más cercanos por significado, no por coincidencia exacta de palabras."""
    return {"query": q, "mode": "semantic", "results": semantic.semantic_search(q, limit)}


@router.get("/stats")
def stats(request):
    """Conteo de documentos por índice del corpus + disponibilidad de búsqueda semántica."""
    return {**service.stats(), "semantic": semantic.available()}
