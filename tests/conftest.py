from pathlib import Path

import pytest

from hxlib.models import ModelDB

FIXTURES = Path(__file__).parent / "fixtures" / "assets"


@pytest.fixture()
def db() -> ModelDB:
    instance = ModelDB(Path(":memory:"), assets_dir=FIXTURES)
    instance.build(force=True)
    return instance
