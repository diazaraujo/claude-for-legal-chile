import os

from ninja import Router
from ninja.security import APIKeyHeader

from . import arbol, semantic, service


class CorpusApiKey(APIKeyHeader):
    """Auth por header X-API-Key. Las keys válidas vienen de CORPUS_API_KEYS
    (lista separada por comas). Si no hay ninguna configurada → abierto (dev)."""
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        valid = {k.strip() for k in os.environ.get("CORPUS_API_KEYS", "").split(",") if k.strip()}
        if not valid:
            return "open"
        return key if key in valid else None


router = Router(tags=["corpus"], auth=CorpusApiKey())


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
    return {**service.stats(), "semantic": semantic.available(), "arbol": arbol.available()}


@router.get("/arbol/normas")
def arbol_normas(request, q: str = "", limit: int = 50):
    """Normas del árbol normativo de interpretaciones, ordenadas por nº de sentencias
    que las citan. q filtra por título o número."""
    return {"normas": arbol.normas(q, limit)}


@router.get("/arbol/norma/{id_norma}")
def arbol_articulos(request, id_norma: int):
    """Artículos de una norma con conteo de sentencias que los interpretan."""
    return arbol.articulos(id_norma)


@router.get("/arbol/norma/{id_norma}/articulo")
def arbol_articulo(request, id_norma: int, art: str, muestras: int = 3):
    """Detalle de un artículo: serie temporal (sentencias/año) + tesis interpretativas
    (clusters etiquetados) con sentencias de ejemplo."""
    return arbol.articulo_detalle(id_norma, art, muestras)


@router.get("/arbol/concepto")
def arbol_concepto(request, q: str, limit: int = 15):
    """Entrada semántica: pregunta en lenguaje natural → artículos más relevantes
    (del problema jurídico al articulado que lo gobierna, vía índice semántico)."""
    return {"query": q, "articulos": arbol.concepto_a_articulos(q, limit)}


@router.get("/arbol/admin")
def arbol_admin_ejemplos(request, id_norma: int, art: str, source: str, n: int = 3):
    """Dictámenes/oficios de ejemplo de un organismo que citan el artículo, con extracto."""
    return {"ejemplos": arbol.admin_ejemplos(id_norma, art, source, n)}


@router.get("/considerando/{chunk_id}")
def considerando_fuente(request, chunk_id: int):
    """Texto completo del considerando (fuente verificable de la tesis) + identificador
    canónico de la sentencia (rol, tribunal, fecha, carátula)."""
    return arbol.considerando_fuente(chunk_id)


@router.get("/considerandos/semantic")
def considerandos_semantic(request, q: str, limit: int = 20):
    """Búsqueda semántica granular sobre 5,16M considerandos individuales (bge-m3 +
    faiss). Devuelve el considerando, su sentencia, fecha, rol y carátula."""
    return {"query": q, "results": arbol.considerandos_semantic(q, limit)}
