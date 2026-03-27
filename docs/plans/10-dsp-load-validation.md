# Plan: DSP load validation

## ⚠ Blocked — investigation required before implementation

Two questions must be answered on real hardware before the thresholds in this plan can be
set with confidence:

1. **What is the hard DSP limit?**
   The `load` field in `.models` files is documented only as "DSP CPU load in mono" — no
   units or scale are given anywhere in the codebase or the manual. The highest observed
   value across all 645 models with load data is **40.0** (polyphonic pitch effects). The
   manual says these effects use "up to half of a preset's available DSP", which implies a
   total budget somewhere around 80–100. But 80 and 100 are meaningfully different
   thresholds for validation purposes, and no source confirms which is correct.

2. **Is the DSP budget global or per-path?**
   The manual says polyphonic effects use "up to half of all DSP available for Path 1 or
   Path 2". This phrasing was initially read as per-path budgets, but on closer reading it
   more likely means "half of the total budget that would otherwise be available to
   whichever path it's placed on" — i.e. a single shared pool. The manual's "DSP full!"
   message and the Dynamic DSP section treat DSP as a single global resource. However,
   the `.models` schema doc shows `@topology0` / `@topology1` parameters, which may point
   to separate DSP processors. This needs confirmation.

**How to investigate:** build a preset on the HX Stomp using known-load models (e.g.
several amps + a polyphonic effect) and find the exact total load at which the device
refuses to add another block and shows "DSP full!". Also test whether a preset with blocks
split across Path 1 and Path 2 has a higher total load ceiling than a single-path preset,
which would confirm per-path budgeting.

---

## Context

The HX Stomp has a fixed DSP budget. Each model carries `load` (mono) and `load_stereo`
fields in the SQLite cache. The goal is to surface DSP usage in `validate()` as a
`warning` when load approaches the limit and as an `error` when it would exceed it,
giving the LLM (and users) actionable feedback before deploying a preset to hardware.

Two preconditions must land first:

1. **Severity levels on `ValidationIssue`** — currently `severity` is a plain `str`
   hardcoded to `"error"`. DSP load warnings need a distinct `"warning"` level.
2. **DSP load check in `validate()`** — sum load across enabled blocks, compare to a
   threshold and the hard limit.

Both changes are small and contained to `hxlib/preset.py` and `tests/test_preset.py`.

## What we know about `load` values

- Sourced from `.models` asset files shipped with HX Edit.
- Field description in `docs/schemas/models.md`: "DSP CPU load in mono" / "DSP CPU load
  in stereo". No unit or scale specified.
- Range across all 645 models with data: **0.35 – 40.0**.
- The heaviest models are polyphonic pitch effects (40.0), followed by high-gain amps
  (31–37), then reverbs (10–23).
- The manual states polyphonic effects use "up to half of a preset's available DSP".
  Their actual values (36–40) are consistent with "up to half" if the total budget is
  roughly 80–100.
- A `capEdge` field exists on cab/IR models (0.32–0.55 scale) but is unrelated to `load`
  — it appears to be a separate capacity concept, not a DSP percentage.
- No value in any `.models` file exceeds 40.0. This means validation using a 100%
  threshold would never fire on a single-block preset, but could fire with 3–4 heavy
  blocks combined (e.g. two amps at 37% + one polyphonic at 40% = 114%).

## Design decisions

### Severity

Change `ValidationIssue.severity` from `str` to a `Literal["error", "warning"]` type
annotation (no runtime overhead, just tighter typing). The field stays a plain string so
existing callsites that compare `i.severity == "error"` continue to work unchanged.

### DSP budget

**Placeholder thresholds — to be revised after hardware investigation (see top of plan).**

Assuming a single shared budget and a 100% hard limit:

| Threshold | Severity | Message |
|-----------|----------|---------|
| `> 100%` | `error` | `"DSP overloaded: {total:.1f}% (limit ~100%)"` |
| `> 80%` | `warning` | `"DSP load is high: {total:.1f}%"` |

The warning threshold is set conservatively at 80% rather than 90%, given that the true
limit may be as low as 80. Constants go at the top of `preset.py` alongside `MAX_BLOCKS`:

```python
DSP_WARN_THRESHOLD = 80.0   # percent — unconfirmed, see plan notes
DSP_MAX = 100.0             # percent — unconfirmed, see plan notes
```

### Which load figure to use

Each block stores `@stereo: bool`. Use `model.load_stereo` when the block's `@stereo` is
`True` and `model.load_stereo is not None`; otherwise fall back to `model.load`. If both
are `None`, skip that block (no data — don't fabricate a load figure).

The manual confirms: "The stereo version of an effects block will use roughly twice as
much DSP as a mono version."

### Scope of the check

Only count **enabled** blocks (`@enabled: True`). Disabled blocks are assumed to not
consume DSP on hardware.

Skip the DSP check entirely if every enabled block in the preset is missing load data
(DB built from incomplete asset files). A partial-data scenario — some blocks have load,
others don't — emits the issue with a `" (partial — some blocks have no load data)"`
suffix indicating the total is a lower bound.

## Files

| File | Change |
|------|--------|
| `hxlib/preset.py` | Add constants, update `ValidationIssue` annotation, add DSP check in `validate()` |
| `tests/test_preset.py` | New `TestDSPValidation` class |
| `tests/fixtures/assets/res/distortion.models` | Add `load_stereo` to `HD2_DistCigaretteFuzz` for stereo test |

## Implementation

### 1. `hxlib/preset.py` — constants

```python
# After MAX_BLOCKS = 6
DSP_WARN_THRESHOLD = 80.0   # percent — warning threshold (unconfirmed scale, see plan)
DSP_MAX = 100.0             # percent — hard limit (unconfirmed scale, see plan)
```

### 2. `hxlib/preset.py` — `ValidationIssue` annotation

```python
from typing import Literal

@dataclass(frozen=True)
class ValidationIssue:
    severity: Literal["error", "warning"]
    location: str
    message: str
```

No change to construction sites — the string literals `"error"` and `"warning"` already
satisfy `Literal["error", "warning"]`.

### 3. `hxlib/preset.py` — `validate()` DSP check

Append after the existing per-block loop (before `return issues`):

```python
# --- DSP load check ---
total_load = 0.0
has_any_data = False
missing_data = False

for key, blk in existing.items():
    if not blk.get("@enabled", False):
        continue
    model_id = blk.get("@model", "")
    model = db.get_model(model_id)
    if model is None:
        continue  # already reported as unknown model above
    stereo = blk.get("@stereo", False)
    load = (model.load_stereo if stereo and model.load_stereo is not None else model.load)
    if load is None:
        missing_data = True
        continue
    has_any_data = True
    total_load += load

if has_any_data:
    suffix = " (partial — some blocks have no load data)" if missing_data else ""
    if total_load > DSP_MAX:
        issues.append(
            ValidationIssue(
                severity="error",
                location="preset",
                message=f"DSP overloaded: {total_load:.1f}% (limit ~{DSP_MAX:.0f}%){suffix}",
            )
        )
    elif total_load > DSP_WARN_THRESHOLD:
        issues.append(
            ValidationIssue(
                severity="warning",
                location="preset",
                message=f"DSP load is high: {total_load:.1f}%{suffix}",
            )
        )
```

### 4. `tests/fixtures/assets/res/distortion.models` — add `load_stereo`

`HD2_DistCigaretteFuzz` already has `"load": 15.5`. Add `"load_stereo": 25.0` so the
stereo fallback path can be exercised in tests.

### 5. `tests/test_preset.py` — `TestDSPValidation`

Use `monkeypatch` to lower the thresholds for boundary tests, keeping fixture load values
small and tests independent of the real (unconfirmed) threshold values:

```python
class TestDSPValidation:
    def test_no_dsp_issue_on_clean_preset(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        issues = p.validate(db)
        assert not any(i.location == "preset" and "DSP" in i.message for i in issues)

    def test_dsp_total_uses_enabled_blocks_only(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        k1 = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        k2 = p.add_block("HD2_DelayMagneticTape", 1, [], db)
        p._dsp0()[k2]["@enabled"] = False  # disable second block
        issues = p.validate(db)
        assert not any("DSP" in i.message for i in issues)

    def test_dsp_warning_issued_above_threshold(
        self, db: ModelDB, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import hxlib.preset as pm
        monkeypatch.setattr(pm, "DSP_WARN_THRESHOLD", 10.0)
        monkeypatch.setattr(pm, "DSP_MAX", 100.0)
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)  # load=15.5 > 10.0
        issues = p.validate(db)
        assert any(
            i.severity == "warning" and "DSP load is high" in i.message
            for i in issues
        )

    def test_dsp_error_issued_above_max(
        self, db: ModelDB, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import hxlib.preset as pm
        monkeypatch.setattr(pm, "DSP_WARN_THRESHOLD", 5.0)
        monkeypatch.setattr(pm, "DSP_MAX", 10.0)
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)  # load=15.5 > 10.0
        issues = p.validate(db)
        assert any(
            i.severity == "error" and "DSP overloaded" in i.message for i in issues
        )

    def test_dsp_uses_stereo_load_when_stereo_enabled(
        self, db: ModelDB, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import hxlib.preset as pm
        # load_stereo=25.0 > load=15.5; threshold at 20.0 means mono passes, stereo warns
        monkeypatch.setattr(pm, "DSP_WARN_THRESHOLD", 20.0)
        monkeypatch.setattr(pm, "DSP_MAX", 100.0)
        p = Preset.new("Test")
        key = p.add_block("HD2_DistCigaretteFuzz", 0, [], db)
        p._dsp0()[key]["@stereo"] = True
        issues = p.validate(db)
        assert any("DSP load is high" in i.message for i in issues)

    def test_dsp_partial_data_adds_suffix(
        self, db: ModelDB, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import hxlib.preset as pm
        monkeypatch.setattr(pm, "DSP_WARN_THRESHOLD", 10.0)
        monkeypatch.setattr(pm, "DSP_MAX", 100.0)
        p = Preset.new("Test")
        p.add_block("HD2_DistCigaretteFuzz", 0, [], db)   # load=15.5
        p.add_block("HD2_DistCobaltDrive", 1, [], db)     # load=None
        issues = p.validate(db)
        dsp_issues = [i for i in issues if "DSP" in i.message]
        assert len(dsp_issues) == 1
        assert "partial" in dsp_issues[0].message

    def test_dsp_skipped_when_no_load_data(self, db: ModelDB) -> None:
        p = Preset.new("Test")
        p.add_block("HD2_DistCobaltDrive", 0, [], db)  # load=None
        issues = p.validate(db)
        assert not any("DSP" in i.message for i in issues)
```

## Verification

```
uv run check
```

All existing tests must pass. The seven new `TestDSPValidation` tests should pass.

Manual smoke-test after hardware investigation confirms thresholds:

```
hx preset validate my.hlx   # clean preset → exit 0
```

Add multiple high-load blocks and re-validate to observe warning/error output. JSON
`--json` output will include issues with `severity: "warning"` or `severity: "error"`.
