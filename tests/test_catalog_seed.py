import json
import unittest
from pathlib import Path


class BundledCatalogTests(unittest.TestCase):
    def test_seed_contains_both_known_characters_and_perks(self):
        path = Path(__file__).resolve().parents[1] / "data" / "catalog_seed.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload["values"]
        self.assertEqual(payload["scanned_files"], 8)
        self.assertEqual(set(values["nameKey"]), {"Dirwin", "Jonna"})
        self.assertEqual(set(values["perksList"]), {
            "o_perk_trained_eye", "o_perk_magical_erudition"
        })
        self.assertEqual(set(values["classKey"]), {"Woodward", "RunawaySorceress"})
        self.assertEqual(set(values["raceKey"]), {"Human"})

    def test_every_seed_value_has_source_provenance(self):
        path = Path(__file__).resolve().parents[1] / "data" / "catalog_seed.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        sources = payload["sources"]
        for field, items in payload["values"].items():
            for value in items:
                self.assertTrue(sources.get(f"{field}\t{value}"), (field, value))


if __name__ == "__main__":
    unittest.main()
