"""Integration tests for hxlib.preset."""

from pathlib import Path

import pytest

from hxlib.db import ModelDB
from hxlib.preset import (
    MAX_BLOCKS,
    BlockRow,
    Preset,
    PresetError,
    ValidationIssue,
)

PRESET_DIR = Path(__file__).parent.parent / "assets" / "presets"
MUSE = PRESET_DIR / "MusePlugInBaby.hlx"


# ---------------------------------------------------------------------------
# TestLoad
# ---------------------------------------------------------------------------


class TestLoad:
    def test_meta_name(self) -> None:
        p = Preset.load(MUSE)
        assert p.meta.name == "MusePlugInBaby"

    def test_meta_application(self) -> None:
        p = Preset.load(MUSE)
        assert p.meta.application == "HX Edit"

    def test_meta_modifieddate(self) -> None:
        p = Preset.load(MUSE)
        assert p.meta.modifieddate == 1774491631

    def test_block_count(self) -> None:
        p = Preset.load(MUSE)
        assert len(p.list_blocks()) == 3

    def test_block_fields(self) -> None:
        p = Preset.load(MUSE)
        blocks = {b.key: b for b in p.list_blocks()}
        b0 = blocks["block0"]
        assert b0.model_id == "HD2_CompressorDeluxeComp"
        assert b0.enabled is True
        assert b0.position == 0
        assert b0.path == 0
        assert b0.block_type == 0

    def test_amp_block_type(self) -> None:
        p = Preset.load(MUSE)
        blocks = {b.key: b for b in p.list_blocks()}
        assert blocks["block2"].block_type == 1

    def test_param_value(self) -> None:
        p = Preset.load(MUSE)
        blocks = {b.key: b for b in p.list_blocks()}
        assert blocks["block1"].params["Sustain"] == pytest.approx(0.83, abs=1e-4)


# ---------------------------------------------------------------------------
# TestNew
# ---------------------------------------------------------------------------


class TestNew:
    def test_name_set(self) -> None:
        p = Preset.new("My Patch")
        assert p.meta.name == "My Patch"

    def test_no_blocks(self) -> None:
        p = Preset.new("Empty")
        assert p.list_blocks() == []

    def test_valid_schema(self) -> None:
        p = Preset.new("X")
        assert p._data["schema"] == "L6Preset"

    def test_snapshots_present(self) -> None:
        p = Preset.new("X")
        tone = p._data["data"]["tone"]
        for i in range(3):
            assert f"snapshot{i}" in tone


# ---------------------------------------------------------------------------
# TestListBlocks
# ---------------------------------------------------------------------------


class TestListBlocks:
    def test_sorted_by_position(self) -> None:
        p = Preset.load(MUSE)
        blocks = p.list_blocks()
        positions = [b.position for b in blocks]
        assert positions == sorted(positions)

    def test_all_fields_present(self) -> None:
        p = Preset.load(MUSE)
        for b in p.list_blocks():
            assert isinstance(b, BlockRow)
            assert b.key
            assert b.model_id


# ---------------------------------------------------------------------------
# TestGetBlock
# ---------------------------------------------------------------------------


class TestGetBlock:
    def test_found(self) -> None:
        p = Preset.load(MUSE)
        b = p.get_block("block0")
        assert b is not None
        assert b.model_id == "HD2_CompressorDeluxeComp"

    def test_not_found(self) -> None:
        p = Preset.load(MUSE)
        assert p.get_block("block99") is None

    def test_fixed_key_returns_none(self) -> None:
        p = Preset.load(MUSE)
        assert p.get_block("inputA") is None


# ---------------------------------------------------------------------------
# TestAddBlock
# ---------------------------------------------------------------------------


class TestAddBlock:
    def test_block_appears_in_list(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0, 1, 2], db)
        keys = [b.key for b in p.list_blocks()]
        assert key in keys

    def test_snapshot_state_written(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0, 2], db)
        tone = p._data["data"]["tone"]
        assert tone["snapshot0"]["blocks"]["dsp0"][key] is True
        assert tone["snapshot2"]["blocks"]["dsp0"][key] is True
        assert key not in tone["snapshot1"].get("blocks", {}).get("dsp0", {})

    def test_defaults_populated(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0], db)
        b = p.get_block(key)
        assert b is not None
        assert "Drive" in b.params
        assert b.params["Drive"] == pytest.approx(0.5)

    def test_returns_block_key(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        assert key.startswith("block")

    def test_first_free_slot(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        k1 = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        k2 = p.add_block("HD2_DistCobaltDrive", 1, [], db)
        assert k1 == "block0"
        assert k2 == "block1"


# ---------------------------------------------------------------------------
# TestAddBlockErrors
# ---------------------------------------------------------------------------


class TestAddBlockErrors:
    def test_unknown_model(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        with pytest.raises(PresetError, match="unknown model"):
            p.add_block("HD2_NoSuchModel", 0, [], db)

    def test_position_conflict(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        with pytest.raises(PresetError, match="already occupied"):
            p.add_block("HD2_DistCobaltDrive", 0, [], db)

    def test_exceeding_max_blocks(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        for i in range(MAX_BLOCKS):
            p.add_block("HD2_DistCigaretteFuzz", i, [], db)
        with pytest.raises(PresetError):
            p.add_block("HD2_DistCobaltDrive", 6, [], db)

    def test_position_out_of_range(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        with pytest.raises(PresetError, match="out of range"):
            p.add_block("HD2_DistCigaretteFuzz", 9, [], db)


# ---------------------------------------------------------------------------
# TestRemoveBlock
# ---------------------------------------------------------------------------


class TestRemoveBlock:
    def test_block_gone_from_list(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0], db)
        p.remove_block(key)
        assert p.get_block(key) is None

    def test_block_gone_from_snapshots(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0, 1], db)
        p.remove_block(key)
        tone = p._data["data"]["tone"]
        for i in range(3):
            dsp0 = tone.get(f"snapshot{i}", {}).get("blocks", {}).get("dsp0", {})
            assert key not in dsp0

    def test_raises_on_unknown_key(self) -> None:
        p = Preset.new("Test")
        with pytest.raises(PresetError, match="block not found"):
            p.remove_block("block99")


# ---------------------------------------------------------------------------
# TestMoveBlock
# ---------------------------------------------------------------------------


class TestMoveBlock:
    def test_position_updated(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0], db)
        p.move_block(key, 3)
        b = p.get_block(key)
        assert b is not None
        assert b.position == 3

    def test_path_updated(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0], db)
        p.move_block(key, 2, path=1)
        b = p.get_block(key)
        assert b is not None
        assert b.path == 1

    def test_path_unchanged_when_not_specified(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0], db, path=1)
        p.move_block(key, 3)
        b = p.get_block(key)
        assert b is not None
        assert b.path == 1

    def test_params_preserved(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0], db)
        params_before = p.get_block(key).params.copy()  # type: ignore[union-attr]
        p.move_block(key, 4)
        assert p.get_block(key).params == params_before  # type: ignore[union-attr]

    def test_snapshot_state_preserved(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0, 2], db)
        p.move_block(key, 5)
        tone = p._data["data"]["tone"]
        assert tone["snapshot0"]["blocks"]["dsp0"][key] is True
        assert tone["snapshot2"]["blocks"]["dsp0"][key] is True

    def test_raises_on_unknown_key(self) -> None:
        p = Preset.new("Test")
        with pytest.raises(PresetError, match="block not found"):
            p.move_block("block99", 0)

    def test_raises_on_position_conflict(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        k2 = p.add_block("HD2_DistCobaltDrive", 1, [], db)
        with pytest.raises(PresetError, match="already occupied"):
            p.move_block(k2, 0)

    def test_raises_on_position_out_of_range(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        with pytest.raises(PresetError, match="out of range"):
            p.move_block(key, 9)


# ---------------------------------------------------------------------------
# TestSetParam
# ---------------------------------------------------------------------------


class TestSetParam:
    def test_value_updated(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        p.set_param(key, "Drive", 0.9)
        b = p.get_block(key)
        assert b is not None
        assert b.params["Drive"] == pytest.approx(0.9)

    def test_raises_out_of_range_with_db(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        with pytest.raises(ValueError, match="out of range"):
            p.set_param(key, "Drive", 2.0, db=db)

    def test_no_raise_without_db(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        p.set_param(key, "Drive", 2.0)  # no db → no validation
        b = p.get_block(key)
        assert b is not None
        assert b.params["Drive"] == pytest.approx(2.0)

    def test_raises_on_at_param(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        with pytest.raises(ValueError):
            p.set_param(key, "@enabled", True)


# ---------------------------------------------------------------------------
# TestValidate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_clean_preset_returns_empty(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        issues = p.validate(db)
        assert issues == []

    def test_unknown_model_produces_issue(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p._dsp0()["block0"] = {
            "@model": "HD2_NotReal",
            "@enabled": True,
            "@position": 0,
            "@path": 0,
            "@type": 0,
            "@stereo": False,
        }
        issues = p.validate(db)
        assert any(
            i.location == "block0" and "unknown model" in i.message for i in issues
        )

    def test_bad_param_produces_issue(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        p._dsp0()[key]["BadParam"] = 0.5
        issues = p.validate(db)
        assert any("BadParam" in i.location for i in issues)

    def test_out_of_range_produces_issue(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        p._dsp0()[key]["Drive"] = 99.0  # bypass set_param validation
        issues = p.validate(db)
        assert any("Drive" in i.location for i in issues)

    def test_all_issues_are_validation_issue(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p._dsp0()["block0"] = {"@model": "HD2_NotReal", "@position": 0, "@path": 0}
        for i in p.validate(db):
            assert isinstance(i, ValidationIssue)
            assert i.severity == "error"


# ---------------------------------------------------------------------------
# TestSave
# ---------------------------------------------------------------------------


class TestSave:
    def test_roundtrip(self, db: ModelDB, tmp_path: Path) -> None:
        p = Preset.new("RoundTrip")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [0, 1, 2], db)
        p.set_param(key, "Drive", 0.75)
        out = tmp_path / "test.hlx"
        p.save(out)

        p2 = Preset.load(out)
        assert p2.meta.name == "RoundTrip"
        blocks = {b.key: b for b in p2.list_blocks()}
        assert key in blocks
        assert blocks[key].params["Drive"] == pytest.approx(0.75)

    def test_schema_preserved(self, tmp_path: Path) -> None:
        p = Preset.new("X")
        out = tmp_path / "x.hlx"
        p.save(out)
        p2 = Preset.load(out)
        assert p2._data["schema"] == "L6Preset"
