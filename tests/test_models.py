from pathlib import Path

from hxlib.models import ModelDB

FIXTURES = Path(__file__).parent / "fixtures" / "assets" / "res"

# 3 models in distortion.models + 2 in delay.models
_MODEL_COUNT = 5
# Drive (float) + Enabled (bool) + Time (float)
_PARAM_COUNT = 3


class TestBuild:
    def test_returns_counts(self, db: ModelDB) -> None:
        result = db.build(force=True)
        assert result == (_MODEL_COUNT, _PARAM_COUNT)

    def test_second_build_idempotent(self, db: ModelDB) -> None:
        first = db.build(force=True)
        second = db.build(force=True)
        assert first == second == (_MODEL_COUNT, _PARAM_COUNT)


class TestIsFresh:
    def test_memory_db_not_fresh(self) -> None:
        db = ModelDB(Path(":memory:"), assets_dir=FIXTURES)
        assert db.is_fresh() is False

    def test_nonexistent_not_fresh(self) -> None:
        db = ModelDB(Path("/nonexistent/path/x.db"), assets_dir=FIXTURES)
        assert db.is_fresh() is False

    def test_fresh_after_build(self, tmp_path: Path) -> None:
        db = ModelDB(tmp_path / "test.db", assets_dir=FIXTURES)
        db.build(force=True)
        assert db.is_fresh() is True


class TestListCategories:
    def test_returns_all_categories(self, db: ModelDB) -> None:
        cats = db.list_categories()
        assert len(cats) == 2

    def test_model_counts(self, db: ModelDB) -> None:
        cats = db.list_categories()
        dist = next(c for c in cats if c.id == 1)
        dly = next(c for c in cats if c.id == 2)
        assert dist.model_count == 3
        # HD2_DlyOrphan has no category so only HD2_DlyTape counts
        assert dly.model_count == 1

    def test_ordered_by_id(self, db: ModelDB) -> None:
        cats = db.list_categories()
        assert [c.id for c in cats] == [1, 2]


class TestFindCategory:
    def test_exact_by_name(self, db: ModelDB) -> None:
        result = db.find_category("Distortion")
        assert len(result) == 1
        assert result[0].name == "Distortion"

    def test_exact_by_short_name(self, db: ModelDB) -> None:
        result = db.find_category("dist")
        assert len(result) == 1
        assert result[0].id == 1

    def test_case_insensitive(self, db: ModelDB) -> None:
        result = db.find_category("DISTORTION")
        assert len(result) == 1
        assert result[0].id == 1

    def test_like_fallback(self, db: ModelDB) -> None:
        result = db.find_category("stor")
        assert len(result) == 1
        assert result[0].id == 1

    def test_no_match(self, db: ModelDB) -> None:
        result = db.find_category("xyz_no_match")
        assert result == []


class TestListModels:
    def test_returns_models_for_category(self, db: ModelDB) -> None:
        models = db.list_models(1)
        assert len(models) == 3

    def test_category_name_joined(self, db: ModelDB) -> None:
        models = db.list_models(1)
        assert all(m.category_name == "Distortion" for m in models)

    def test_unknown_category_empty(self, db: ModelDB) -> None:
        assert db.list_models(999) == []


class TestGetModel:
    def test_known_model(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCigaretteFuzz")
        assert model is not None
        assert model.symbolic_id == "HD2_DistCigaretteFuzz"
        assert model.name == "Cigarette Fuzz"
        assert model.category_id == 1
        assert model.category_name == "Distortion"
        assert model.load == 15.5

    def test_name_fallback_to_symbolic_id(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCobaltDrive")
        assert model is not None
        assert model.name == "HD2_DistCobaltDrive"

    def test_no_category_fields_are_none(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DelayWanderer")
        assert model is not None
        assert model.category_id is None
        assert model.category_name is None

    def test_mono_stereo_are_bool(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCigaretteFuzz")
        assert model is not None
        assert model.mono is True
        assert model.stereo is False
        assert type(model.mono) is bool
        assert type(model.stereo) is bool

    def test_unknown_id_returns_none(self, db: ModelDB) -> None:
        assert db.get_model("HD2_NonExistent") is None


class TestGetParams:
    def test_params_in_sort_order(self, db: ModelDB) -> None:
        params = db.get_params("HD2_DistCigaretteFuzz")
        assert len(params) == 1
        assert params[0].symbolic_id == "Drive"

    def test_all_fields_present(self, db: ModelDB) -> None:
        param = db.get_params("HD2_DistCigaretteFuzz")[0]
        assert param.name == "Drive"
        assert param.value_type == 1
        assert param.display_type == "generic_knob"
        assert param.min_val == "0.0"
        assert param.max_val == "1.0"
        assert param.default_val == "0.5"

    def test_bool_default_encoding(self, db: ModelDB) -> None:
        params = db.get_params("HD2_DistIronGate")
        assert len(params) == 1
        assert params[0].default_val == "true"

    def test_no_params_returns_empty(self, db: ModelDB) -> None:
        assert db.get_params("HD2_DistCobaltDrive") == []


class TestSearchModels:
    def test_substring_match(self, db: ModelDB) -> None:
        results = db.search_models("cigarette")
        assert len(results) == 1
        assert results[0].symbolic_id == "HD2_DistCigaretteFuzz"

    def test_case_insensitive(self, db: ModelDB) -> None:
        results = db.search_models("CIGARETTE")
        assert len(results) == 1
        assert results[0].symbolic_id == "HD2_DistCigaretteFuzz"

    def test_no_match(self, db: ModelDB) -> None:
        assert db.search_models("xyz_no_match") == []

    def test_category_filter(self, db: ModelDB) -> None:
        results = db.search_models("magnetic", category_id=2)
        assert len(results) == 1
        assert results[0].symbolic_id == "HD2_DelayMagneticTape"

    def test_no_category_filter_searches_all(self, db: ModelDB) -> None:
        results = db.search_models("magnetic")
        assert any(m.symbolic_id == "HD2_DelayMagneticTape" for m in results)

    def test_search_by_based_on(self, db: ModelDB) -> None:
        results = db.search_models("fuzz face")
        assert len(results) == 1
        assert results[0].symbolic_id == "HD2_DistCigaretteFuzz"

    def test_search_by_based_on_case_insensitive(self, db: ModelDB) -> None:
        results = db.search_models("FUZZ FACE")
        assert len(results) == 1
        assert results[0].symbolic_id == "HD2_DistCigaretteFuzz"


class TestBasedOn:
    def test_based_on_populated(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCigaretteFuzz")
        assert model is not None
        assert model.based_on == "Fuzz Face Mk I"

    def test_based_on_none_when_absent(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCobaltDrive")
        assert model is not None
        assert model.based_on is None
