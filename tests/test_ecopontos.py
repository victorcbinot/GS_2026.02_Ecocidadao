from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.agent.ecopontos import (
    EcopontoCatalog,
    EcopontoDataError,
)

DATA_PATH = PROJECT_ROOT / "data" / "ecopontos.json"


class EcopontoCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = EcopontoCatalog.load(DATA_PATH)

    def test_loads_all_ecopontos_and_metadata(self) -> None:
        self.assertEqual(self.catalog.municipio, "EcoCidade")
        self.assertEqual(len(self.catalog.ecopontos), 4)
        self.assertEqual(
            {item.nome for item in self.catalog.ecopontos},
            {"Centro", "Parque das Acácias", "Vila Verde", "Industrial"},
        )
        self.assertEqual(len(self.catalog.comunicados), 1)

    def test_original_parque_accepts_batteries_before_interdiction(self) -> None:
        statuses = self.catalog.query(
            nome="Parque das Acácias",
            material="pilhas",
            as_of=date(2026, 3, 14),
        )

        self.assertEqual(len(statuses), 1)
        status = statuses[0]
        self.assertEqual(status.situacao, "em funcionamento")
        self.assertEqual(
            status.horario,
            "segunda a sábado, 07:00 às 19:00",
        )
        self.assertTrue(status.aceita_material)
        self.assertIn("Interdição programada", status.aviso)

    def test_parque_is_closed_during_interdiction(self) -> None:
        status = self.catalog.query(
            nome="Parque das Acácias",
            material="pilhas",
            as_of="2026-04-01",
        )[0]

        self.assertEqual(status.situacao, "interditado")
        self.assertFalse(status.aceita_material)
        self.assertEqual(status.materiais_aceitos, ())
        self.assertIn(
            "pilhas e baterias: Ecoponto Industrial",
            status.alternativas,
        )
        self.assertIn("2026-03-15", status.horario)
        self.assertIn("2026-05-31", status.horario)

    def test_parque_after_reopening_has_new_hours_and_no_batteries(self) -> None:
        status = self.catalog.query(
            nome="Parque das Acácias",
            material="pilhas",
            as_of="2026-06-10",
        )[0]

        self.assertEqual(status.situacao, "em funcionamento")
        self.assertEqual(
            status.horario,
            "segunda a sexta, 08:00 às 17:00; sábado, 08:00 às 12:00",
        )
        self.assertFalse(status.aceita_material)
        self.assertIn("eletrônicos", status.materiais_aceitos)
        self.assertNotIn("pilhas", status.materiais_aceitos)
        self.assertNotIn("baterias", status.materiais_aceitos)
        self.assertIn("Industrial", status.alternativas)

    def test_industrial_accepts_batteries_after_reopening(self) -> None:
        status = self.catalog.query(
            nome="Industrial",
            material="pilhas e baterias",
            as_of="2026-06-10",
        )[0]

        self.assertTrue(status.aceita_material)
        self.assertIn("pilhas", status.materiais_aceitos)
        self.assertIn("baterias", status.materiais_aceitos)

    def test_material_query_marks_accepted_and_rejected_ecopontos(self) -> None:
        statuses = self.catalog.query(
            material="óleo de cozinha",
            as_of="2026-06-10",
        )
        accepted = [
            status.ecoponto.nome
            for status in statuses
            if status.aceita_material
        ]
        rejected = [
            status.ecoponto.nome
            for status in statuses
            if status.aceita_material is False
        ]

        self.assertEqual(accepted, ["Vila Verde"])
        self.assertEqual(
            set(rejected),
            {"Centro", "Parque das Acácias", "Industrial"},
        )

    def test_name_query_ignores_case_and_accents(self) -> None:
        statuses = self.catalog.query(nome="parque das acacias")
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].ecoponto.nome, "Parque das Acácias")

    def test_unknown_name_returns_empty(self) -> None:
        self.assertEqual(self.catalog.query(nome="Ecoponto inexistente"), [])

    def test_invalid_date_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.catalog.query(as_of="31/12/2026")

    def test_invalid_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ecopontos.json"
            path.write_text("{invalido", encoding="utf-8")
            with self.assertRaises(EcopontoDataError):
                EcopontoCatalog.load(path)

    def test_missing_required_field_is_rejected(self) -> None:
        raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        del raw["ecopontos"][0]["endereco"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ecopontos.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(EcopontoDataError):
                EcopontoCatalog.load(path)


if __name__ == "__main__":
    unittest.main()
