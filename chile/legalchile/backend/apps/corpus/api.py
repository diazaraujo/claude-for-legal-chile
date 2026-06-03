from ninja import Router

from . import service

router = Router(tags=["corpus"])


@router.get("/search")
def search(request, q: str, limit: int = 20, source: str = "new-sources"):
    """Búsqueda full-text sobre el corpus jurídico chileno (legislación, jurisprudencia,
    dictámenes). source: 'new-sources' (default) o 'corpus'."""
    return {"query": q, "source": source, "results": service.search(q, limit, source)}


@router.get("/stats")
def stats(request):
    """Conteo de documentos por índice del corpus."""
    return service.stats()
