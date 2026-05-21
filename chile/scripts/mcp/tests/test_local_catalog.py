"""Tests offline de LocalCatalog usando SQLite temporal.

Construye una BD mini in-memory para aislar de la BD del repo.
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Permitir imports sin instalación
THIS_DIR = Path(__file__).resolve().parent
SRC = THIS_DIR.parent / "src"
sys.path.insert(0, str(SRC))

from mcp_bcn_leychile.local_catalog import LocalCatalog  # noqa: E402


def _seed_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE normas (
            slug TEXT PRIMARY KEY,
            tipo TEXT,
            numero TEXT,
            titulo TEXT,
            publicacion TEXT,
            promulgacion TEXT,
            organismo TEXT,
            leychile_code TEXT,
            bcn_uri TEXT,
            capa INTEGER,
            md_path TEXT
        );
        CREATE TABLE relaciones (
            src_uri TEXT,
            rel TEXT,
            dst_uri TEXT
        );
        """
    )
    cur.executemany(
        "INSERT INTO normas VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "ley-21643",
                "ley",
                "21643",
                "MODIFICA EL CÓDIGO DEL TRABAJO ... acoso laboral",
                "2024-01-15",
                "2024-01-05",
                "ministerio-del-trabajo",
                "1200096",
                "http://datos.bcn.cl/recurso/cl/ley/21643",
                1,
                "chile/normativa/catalogo/ley/21643.md",
            ),
            (
                "ley-21212-femicidio-gabriela",
                "ley",
                "21212",
                "Ley Gabriela — femicidio",
                "2020-03-04",
                None,
                None,
                "1143040",
                None,
                3,
                "chile/normativa/leyes/ley-21212-femicidio-gabriela.md",
            ),
            (
                "ley-20005-acoso-sexual",
                "ley",
                "20005",
                "TIPIFICA Y SANCIONA EL ACOSO SEXUAL",
                "2005-03-18",
                None,
                None,
                "236425",
                None,
                2,
                "chile/normativa/catalogo/ley/20005.md",
            ),
        ],
    )
    cur.executemany(
        "INSERT INTO relaciones VALUES(?,?,?)",
        [
            (
                "http://datos.bcn.cl/recurso/cl/ley/21643",
                "modifiesTo",
                "http://datos.bcn.cl/recurso/cl/ley/20005",
            ),
            (
                "http://datos.bcn.cl/recurso/cl/ley/21643",
                "modifiesTo",
                "http://datos.bcn.cl/recurso/cl/codigo-del-trabajo",
            ),
        ],
    )
    conn.commit()
    conn.close()


class LocalCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        tmp.close()
        self.db = Path(tmp.name)
        _seed_db(self.db)
        self.cat = LocalCatalog(self.db)

    def tearDown(self) -> None:
        self.cat.close()
        self.db.unlink()

    def test_available(self) -> None:
        self.assertTrue(self.cat.available)

    def test_lookup_by_slug(self) -> None:
        n = self.cat.lookup_by_slug("ley-21643")
        self.assertIsNotNone(n)
        self.assertEqual(n.numero, "21643")
        self.assertEqual(n.leychile_code, "1200096")
        self.assertEqual(
            n.fuente_oficial,
            "https://www.bcn.cl/leychile/navegar?idNorma=1200096",
        )

    def test_lookup_by_leychile_code(self) -> None:
        n = self.cat.lookup_by_leychile_code("1143040")
        self.assertIsNotNone(n)
        self.assertEqual(n.slug, "ley-21212-femicidio-gabriela")
        self.assertEqual(n.capa, 3)

    def test_lookup_by_numero_prefiere_capa_alta(self) -> None:
        # Sólo hay ley 21643 con capa 1. Si hubieran varios, capa
        # mayor gana — lo probamos con ley 21212 que sólo está capa 3.
        n = self.cat.lookup_by_numero("ley", "21212")
        self.assertEqual(n.capa, 3)

    def test_search_ordena_por_capa_desc(self) -> None:
        results = self.cat.search("acoso")
        self.assertGreaterEqual(len(results), 2)
        # Capa más alta debe venir primero
        self.assertEqual(results[0].slug, "ley-20005-acoso-sexual")  # capa 2
        capas = [r.capa for r in results]
        self.assertEqual(capas, sorted(capas, reverse=True))

    def test_lookup_inexistente(self) -> None:
        self.assertIsNone(self.cat.lookup_by_slug("no-existe"))
        self.assertIsNone(self.cat.lookup_by_leychile_code("999999999"))
        self.assertIsNone(self.cat.lookup_by_numero("ley", "999999"))
        self.assertIsNone(self.cat.lookup_by_uri("http://x.invented/y"))

    def test_lookup_by_uri(self) -> None:
        n = self.cat.lookup_by_uri("http://datos.bcn.cl/recurso/cl/ley/21643")
        self.assertIsNotNone(n)
        self.assertEqual(n.slug, "ley-21643")
        self.assertEqual(n.leychile_code, "1200096")

    def test_relaciones_outgoing(self) -> None:
        rels = self.cat.relaciones(
            "http://datos.bcn.cl/recurso/cl/ley/21643", direction="outgoing"
        )
        self.assertEqual(len(rels), 2)
        rels_set = {r.rel for r in rels}
        self.assertEqual(rels_set, {"modifiesTo"})

    def test_relaciones_incoming(self) -> None:
        rels = self.cat.relaciones(
            "http://datos.bcn.cl/recurso/cl/ley/20005", direction="incoming"
        )
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0].rel, "modifiesTo")

    def test_stats(self) -> None:
        s = self.cat.stats()
        self.assertEqual(s["total_normas"], 3)
        self.assertEqual(s["total_edges"], 2)
        self.assertEqual(s["by_tipo"]["ley"], 3)

    def test_catalogo_no_disponible(self) -> None:
        cat2 = LocalCatalog("/tmp/_does_not_exist_xyz.sqlite3")
        self.assertFalse(cat2.available)
        self.assertIsNone(cat2.lookup_by_slug("ley-1"))
        self.assertEqual(cat2.search("foo"), [])
        self.assertEqual(cat2.stats(), {"available": 0})


if __name__ == "__main__":
    unittest.main()
