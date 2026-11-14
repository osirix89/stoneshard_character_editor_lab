import tempfile
import unittest
from pathlib import Path

from stoneshard_lab.core import (
    decode_compressed_json, encode_compressed_json,
    decode_compressed_json_bytes, SaveFormatError,
)


class SaveCodecTests(unittest.TestCase):
    def setUp(self):
        self.character = "character_77"
        self.slot = "autosave_1"
        self.sample = {
            "characterDataMap": {
                "nameKey": "TestSubject",
                "Head": "s_TestHead",
                "BodySprite": "s_human_male",
                "CorpseSprite": "s_Test_dead",
                "raceKey": "Human",
                "perksList": ["o_perk_one", "o_perk_two"],
            },
            "skillsDataMap": {"skillsAllDataList": []},
        }

    def test_save_round_trip_and_checksum(self):
        blob = encode_compressed_json(self.sample, "sav", self.character, self.slot)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "data.sav"
            path.write_bytes(blob)
            decoded = decode_compressed_json(path, "sav", self.character, self.slot)
            self.assertTrue(decoded.checksum_valid)
            self.assertEqual(decoded.data, self.sample)

    def test_checksum_is_bound_to_character_and_slot_names(self):
        blob = encode_compressed_json(self.sample, "sav", self.character, self.slot)
        decoded = decode_compressed_json_bytes(blob, Path("data.sav"), "sav", "character_78", self.slot)
        self.assertFalse(decoded.checksum_valid)

    def test_character_and_save_maps_round_trip(self):
        char_map = {"nameKey": "TestSubject"}
        save_map = {"nameKey": "TestSubject", "avatar": "s_Test"}
        c = encode_compressed_json(char_map, "character_map", self.character)
        s = encode_compressed_json(save_map, "save_map", self.character, self.slot)
        with tempfile.TemporaryDirectory() as td:
            cp = Path(td) / "character.map"; cp.write_bytes(c)
            sp = Path(td) / "save.map"; sp.write_bytes(s)
            self.assertTrue(decode_compressed_json(cp, "character_map", self.character).checksum_valid)
            self.assertTrue(decode_compressed_json(sp, "save_map", self.character, self.slot).checksum_valid)


if __name__ == "__main__":
    unittest.main()
