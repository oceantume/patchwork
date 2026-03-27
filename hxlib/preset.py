"""HX Stomp preset loading, editing, and validation."""

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hxlib.models import ModelDB

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEVICE_HXS = 2162694
MAX_BLOCKS = 6
SNAPSHOT_COUNT = 3
FIXED_KEYS = frozenset({"inputA", "inputB", "split", "join", "outputA", "outputB"})
_AMP_CATEGORIES = frozenset({"Amp", "Preamp"})

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PresetMeta:
    name: str
    application: str | None
    modifieddate: int | None


@dataclass(frozen=True)
class BlockRow:
    key: str
    model_id: str
    enabled: bool
    position: int
    path: int
    stereo: bool
    block_type: int
    params: dict[str, int | float | bool]


@dataclass(frozen=True)
class ValidationIssue:
    severity: str  # "error"
    location: str  # e.g. "block0", "block0/Sustain", "preset"
    message: str


# ---------------------------------------------------------------------------
# Preset
# ---------------------------------------------------------------------------


class Preset:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def new(cls, name: str) -> Preset:
        d = copy.deepcopy(_HXS_TEMPLATE)
        d["data"]["meta"]["name"] = name
        return cls(d)

    @classmethod
    def load(cls, path: Path) -> Preset:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("schema") != "L6Preset":
            raise PresetError(f"not an L6Preset file: {path}")
        if "data" not in data or "tone" not in data["data"]:
            raise PresetError(f"missing data/tone in preset: {path}")
        return cls(data)

    @property
    def meta(self) -> PresetMeta:
        m: dict[str, Any] = self._data["data"]["meta"]
        return PresetMeta(
            name=m.get("name", ""),
            application=m.get("application"),
            modifieddate=m.get("modifieddate"),
        )

    @property
    def device_id(self) -> int | None:
        return self._data["data"].get("device")  # type: ignore[no-any-return]

    def list_snapshot_states(self) -> list[tuple[int, str, dict[str, bool]]]:
        """Return (index, name, {block_key: enabled}) for each snapshot."""
        tone: dict[str, Any] = self._data["data"]["tone"]
        result: list[tuple[int, str, dict[str, bool]]] = []
        for i in range(SNAPSHOT_COUNT):
            snap: dict[str, Any] = tone.get(f"snapshot{i}", {})
            name: str = snap.get("@name", f"SNAPSHOT {i + 1}")
            dsp0: dict[str, bool] = snap.get("blocks", {}).get("dsp0", {})
            result.append((i, name, dsp0))
        return result

    def _dsp0(self) -> dict[str, Any]:
        return self._data["data"]["tone"]["dsp0"]  # type: ignore[no-any-return]

    def _effect_blocks(self) -> dict[str, Any]:
        return {k: v for k, v in self._dsp0().items() if k not in FIXED_KEYS}

    def list_blocks(self) -> list[BlockRow]:
        rows: list[BlockRow] = []
        for key, blk in self._effect_blocks().items():
            params = {k: v for k, v in blk.items() if not k.startswith("@")}
            rows.append(
                BlockRow(
                    key=key,
                    model_id=blk.get("@model", ""),
                    enabled=blk.get("@enabled", False),
                    position=blk.get("@position", 0),
                    path=blk.get("@path", 0),
                    stereo=blk.get("@stereo", False),
                    block_type=blk.get("@type", 0),
                    params=params,
                )
            )
        return sorted(rows, key=lambda b: b.position)

    def get_block(self, key: str) -> BlockRow | None:
        if key in FIXED_KEYS:
            return None
        blk = self._dsp0().get(key)
        if blk is None:
            return None
        params = {k: v for k, v in blk.items() if not k.startswith("@")}
        return BlockRow(
            key=key,
            model_id=blk.get("@model", ""),
            enabled=blk.get("@enabled", False),
            position=blk.get("@position", 0),
            path=blk.get("@path", 0),
            stereo=blk.get("@stereo", False),
            block_type=blk.get("@type", 0),
            params=params,
        )

    def add_block(
        self,
        model_id: str,
        position: int,
        snapshots: list[int],
        db: ModelDB,
        *,
        path: int = 0,
        stereo: bool = False,
    ) -> str:
        model = db.get_model(model_id)
        if model is None:
            raise PresetError(f"unknown model: {model_id}")

        block_type = 1 if model.category_name in _AMP_CATEGORIES else 0

        if not 0 <= position <= 5:
            raise PresetError(f"position {position} out of range 0–5")

        existing = self._effect_blocks()
        if len(existing) >= MAX_BLOCKS:
            raise PresetError(f"preset already has {MAX_BLOCKS} blocks")

        for blk in existing.values():
            if blk.get("@path", 0) == path and blk.get("@position", 0) == position:
                raise PresetError(
                    f"position {position} on path {path} is already occupied"
                )

        # Find next free slot
        used = set(existing.keys())
        block_key: str | None = None
        for i in range(MAX_BLOCKS):
            candidate = f"block{i}"
            if candidate not in used:
                block_key = candidate
                break
        if block_key is None:
            raise PresetError("no free block slot")

        # Default param values
        params: dict[str, int | float | bool] = {}
        for p in db.get_params(model_id):
            val = _parse_val(p.default_val)
            if val is not None:
                params[p.symbolic_id] = val

        block_dict: dict[str, Any] = {
            "@model": model_id,
            "@enabled": True,
            "@position": position,
            "@path": path,
            "@stereo": stereo,
            "@type": block_type,
            "@no_snapshot_bypass": False,
        }
        block_dict.update(params)
        self._dsp0()[block_key] = block_dict

        tone = self._data["data"]["tone"]
        for snap_idx in snapshots:
            snap = tone.setdefault(f"snapshot{snap_idx}", {})
            dsp0_snap = snap.setdefault("blocks", {}).setdefault("dsp0", {})
            dsp0_snap[block_key] = True

        return block_key

    def move_block(self, key: str, position: int, *, path: int | None = None) -> None:
        if key in FIXED_KEYS or key not in self._dsp0():
            raise PresetError(f"block not found: {key}")

        if not 0 <= position <= 5:
            raise PresetError(f"position {position} out of range 0–5")

        blk = self._dsp0()[key]
        resolved_path = blk.get("@path", 0) if path is None else path

        for other_key, other_blk in self._effect_blocks().items():
            if other_key == key:
                continue
            if (
                other_blk.get("@path", 0) == resolved_path
                and other_blk.get("@position", 0) == position
            ):
                raise PresetError(
                    f"position {position} on path {resolved_path} is already occupied"
                )

        blk["@path"] = resolved_path
        blk["@position"] = position

    def remove_block(self, key: str) -> None:
        if key in FIXED_KEYS or key not in self._dsp0():
            raise PresetError(f"block not found: {key}")
        del self._dsp0()[key]
        tone = self._data["data"]["tone"]
        for i in range(SNAPSHOT_COUNT):
            snap = tone.get(f"snapshot{i}", {})
            snap.get("blocks", {}).get("dsp0", {}).pop(key, None)

    def set_param(
        self,
        block_key: str,
        param: str,
        value: int | float | bool,
        *,
        db: ModelDB | None = None,
    ) -> None:
        blk = self._dsp0().get(block_key)
        if blk is None or block_key in FIXED_KEYS:
            raise PresetError(f"block not found: {block_key}")
        if param.startswith("@"):
            raise ValueError("param name must not start with '@'")

        if db is not None:
            model_id = blk.get("@model", "")
            param_rows = db.get_params(model_id)
            p = next((p for p in param_rows if p.symbolic_id == param), None)
            if p is None:
                raise ValueError(f"unknown param '{param}' for model '{model_id}'")
            min_v = _parse_val(p.min_val)
            max_v = _parse_val(p.max_val)
            if min_v is not None and max_v is not None and not isinstance(value, bool):
                if float(value) < float(min_v) or float(value) > float(max_v):
                    raise ValueError(
                        f"value {value} out of range [{min_v}, {max_v}]"
                        f" for param '{param}'"
                    )

        blk[param] = value

    def validate(self, db: ModelDB) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        existing = self._effect_blocks()

        if len(existing) > MAX_BLOCKS:
            issues.append(
                ValidationIssue(
                    severity="error",
                    location="preset",
                    message=f"too many blocks: {len(existing)} > {MAX_BLOCKS}",
                )
            )

        seen_positions: set[tuple[int, int]] = set()
        for key, blk in existing.items():
            model_id = blk.get("@model", "")
            model = db.get_model(model_id)
            if model is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        location=key,
                        message=f"unknown model: {model_id}",
                    )
                )
                continue

            path = blk.get("@path", 0)
            pos = blk.get("@position", 0)
            pos_key = (path, pos)
            if pos_key in seen_positions:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        location=key,
                        message=f"position conflict at path={path} position={pos}",
                    )
                )
            else:
                seen_positions.add(pos_key)

            param_map = {p.symbolic_id: p for p in db.get_params(model_id)}
            for pname, pval in blk.items():
                if pname.startswith("@"):
                    continue
                p = param_map.get(pname)
                if p is None:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            location=f"{key}/{pname}",
                            message=f"unknown param '{pname}' for model '{model_id}'",
                        )
                    )
                    continue
                min_v = _parse_val(p.min_val)
                max_v = _parse_val(p.max_val)
                if (
                    min_v is not None
                    and max_v is not None
                    and not isinstance(pval, bool)
                ):
                    if float(pval) < float(min_v) or float(pval) > float(max_v):
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                location=f"{key}/{pname}",
                                message=(
                                    f"value {pval} out of range [{min_v}, {max_v}]"
                                    f" for param '{pname}'"
                                ),
                            )
                        )

        return issues

    def save(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=1)
            fh.write("\n")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PresetError(Exception):
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_val(s: str | None) -> int | float | bool | None:
    """Reverse _encode_scalar: 'true'/'false' → bool, numeric → int/float."""
    if s is None:
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if "." in s or ("e" in s.lower() and any(c.isdigit() for c in s)):
        return float(s)
    return int(s)


# ---------------------------------------------------------------------------
# Embedded HX Stomp blank-preset template
# ---------------------------------------------------------------------------

_HXS_TEMPLATE: dict[str, Any] = {
    "version": 6,
    "schema": "L6Preset",
    "data": {
        "meta": {
            "name": "New Preset",
            "application": "HX Edit",
            "build_sha": "050fc4a",
            "modifieddate": 1516632519,
            "appversion": 327680,
        },
        "device": DEVICE_HXS,
        "device_version": 37814625,
        "tone": {
            "dsp1": {},
            "global": {
                "@variax_volumeknob": -0.1,
                "@pedalstate": 0,
                "@variax_customtuning": True,
                "@variax_str1tuning": 0,
                "@variax_str2tuning": 0,
                "@variax_str4tuning": 0,
                "@variax_str6tuning": 0,
                "@variax_model": 0,
                "@model": "@global_params",
                "@topology0": "A",
                "@cursor_dsp": 0,
                "@cursor_path": 0,
                "@guitarinputZ": 0,
                "@tempo": 120,
                "@topology1": "",
                "@cursor_position": 0,
                "@variax_lockctrls": 0,
                "@variax_magmode": False,
                "@variax_str3tuning": 0,
                "@variax_str5tuning": 0,
                "@variax_toneknob": -0.1,
                "@current_snapshot": 0,
                "@cursor_group": "",
            },
            "snapshot0": {
                "@pedalstate": 0,
                "@ledcolor": 0,
                "@name": "SNAPSHOT 1",
                "@tempo": 120,
            },
            "snapshot1": {
                "@pedalstate": 0,
                "@ledcolor": 0,
                "@name": "SNAPSHOT 2",
                "@tempo": 120,
            },
            "snapshot2": {
                "@pedalstate": 0,
                "@ledcolor": 0,
                "@name": "SNAPSHOT 3",
                "@tempo": 120,
            },
            "dsp0": {
                "split": {
                    "BalanceA": 0.5,
                    "@model": "HD2_AppDSPFlowSplitY",
                    "@enabled": True,
                    "bypass": False,
                    "@position": 0,
                    "BalanceB": 0.5,
                },
                "inputA": {
                    "@input": 1,
                    "@model": "HelixStomp_AppDSPFlowInput",
                    "noiseGate": False,
                    "threshold": -48.0,
                    "decay": 0.5,
                },
                "inputB": {
                    "@input": 0,
                    "@model": "HelixStomp_AppDSPFlowInput",
                    "noiseGate": False,
                    "threshold": -48.0,
                    "decay": 0.5,
                },
                "join": {
                    "@model": "HD2_AppDSPFlowJoin",
                    "B Pan": 0.5,
                    "B Level": 0,
                    "A Level": 0,
                    "A Pan": 0.5,
                    "@position": 0,
                    "Level": 0,
                    "@enabled": True,
                    "B Polarity": False,
                },
                "outputA": {
                    "@model": "HelixStomp_AppDSPFlowOutputMain",
                    "@output": 1,
                    "pan": 0.5,
                    "gain": 0,
                },
                "outputB": {
                    "@model": "HelixStomp_AppDSPFlowOutputSend",
                    "@output": 0,
                    "pan": 0.5,
                    "gain": 0,
                    "Type": True,
                },
            },
        },
    },
}
