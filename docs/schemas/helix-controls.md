# Line6 HX Edit `HelixControls.json` Schema

Reference documentation for `C:\Program Files (x86)\Line6\HX Edit\res\HelixControls.json`.

This file is a UI/UX specification that defines how each DSP parameter value is
scaled, stepped, and formatted for display in the HX Edit interface.

**File stats:** ~7,028 lines, ~134 KB, ~300 root entries.

---

## Root Structure

The file is a single flat JSON object. Each key is a parameter type name; each
value is either a **control definition** or an **alias**.

```json
{
  "time_ms": { /* control definition */ },
  "frequency": { /* control definition */ },
  "amp_fac_type": { "alias": "integer_slider_1based" },
  ...
}
```

---

## Entry Types

### Control Definition

Describes how a parameter is displayed and edited.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `format` | string \| array | Usually | Printf-style format string, array of range-based format objects, or array of strings for discrete values |
| `step` | object \| array | Usually | Fine/coarse increment values, optionally split by value range |
| `isDiscrete` | boolean | No | When `true`, `format` is an enumerated list of display strings |
| `controlType` | string | No | UI widget override; observed value: `"segmented"` |
| `minimumValue` | number | No | Hard minimum (only on a few params, e.g. `pan`, `blend`) |
| `maximumValue` | number | No | Hard maximum |
| `zeroValue` | number | No | Explicit zero/center point (e.g. `pan`) |
| `dspToDisplayScale` | number | No | Multiplier from raw DSP value to display value |
| `displayToWidgetScale` | number | No | Scale factor between display value and widget units |
| `dspToDisplayIntegerOffset` | number | No | Integer offset applied after scaling (e.g. `−1`, `+1`) |
| `canDisplayHigherRes` | boolean | No | Whether the UI supports sub-unit display resolution |
| `unitsMultiplier` | number | No | Per-range multiplier used inside range-based format arrays |

### Alias

A single-key object that points to another entry, indicating the parameter
reuses that entry's definition.

```json
"amp_fac_type": { "alias": "integer_slider_1based" }
```

---

## `format` Field

### Simple string

A printf-style format specifier applied uniformly across all values.

```json
"format": "%.1f"
```

**Observed format specifiers:**

| Specifier | Display style |
|-----------|---------------|
| `"%.0f"` | Integer |
| `"%.1f"` | One decimal place |
| `"%.2f"` | Two decimal places |
| `"%+.0f"` | Signed integer |
| `"%+.1f"` | Signed one decimal |
| `"%f"` | Default float |
| `"%d"` | Integer (explicit) |
| `"%03d"` | Zero-padded 3-digit integer |

Format strings may include literal text: `"%.1f Hz"`, `"%.0f %%"`, `"%+.0f cents"`, `"%.1f sec"`.

### Array of strings (discrete)

When `isDiscrete: true`, `format` is an ordered list of display labels indexed
by the integer parameter value.

```json
"wave_shape": {
  "isDiscrete": true,
  "format": ["Saw Up", "Saw Down", "Triangle", "Sine", "Square", "Inverse Sine", "Random"]
}
```

### Array of range objects (continuous)

Different format rules apply in different value ranges.

```json
"format": [
  {
    "lowerBound": 0,
    "upperBound": 1000,
    "format": "%.0f",
    "formatUnits": "%.0f ms"
  },
  {
    "lowerBound": 1000,
    "upperBound": 999999,
    "unitsMultiplier": 0.001,
    "format": "%.0f",
    "formatUnits": "%.1f kHz"
  }
]
```

**Range object keys:**

| Key | Type | Description |
|-----|------|-------------|
| `lowerBound` | number | Inclusive lower bound of this range |
| `upperBound` | number | Exclusive upper bound of this range |
| `format` | string | Printf format for the numeric portion |
| `formatUnits` | string | Full display string (may embed `format`) |
| `unitsMultiplier` | number | Multiplier applied to value before inserting into `formatUnits` |

Ranges intentionally overlap slightly at boundaries to handle floating-point
edge cases. Sentinel values (`−999999`, `999999`) are used where a range has no
natural bound.

---

## `step` Field

Defines the fine and coarse increment amounts when editing a parameter.

### Simple object

```json
"step": { "fine": 0.1, "coarse": 1.0 }
```

### Array of range objects

Different step sizes apply in different parts of the value range — common for
parameters like `frequency` or `time_ms` where resolution requirements change.

```json
"step": [
  { "lowerBound": 0.0,    "upperBound": 20.0,    "fine": 0.1,  "coarse": 1   },
  { "lowerBound": 20.0,   "upperBound": 1000.0,  "fine": 1,    "coarse": 10  },
  { "lowerBound": 1000.0, "upperBound": 99999.0, "fine": 100,  "coarse": 1000 }
]
```

**Range object keys:**

| Key | Type | Description |
|-----|------|-------------|
| `lowerBound` | number | Lower bound of this step range |
| `upperBound` | number | Upper bound of this step range |
| `fine` | number | Increment for fine (single-unit) adjustment |
| `coarse` | number | Increment for coarse (accelerated) adjustment |

Coarse is typically 2–10× the fine value.

---

## Discrete Parameter Examples

Parameters with `isDiscrete: true` use `format` as an enumerated label list.

| Parameter | Values |
|-----------|--------|
| `Shimmer_Mode` | `Luster`, `Sheen` |
| `amp_voice` | `1` `2` `3` `4` `5` |
| `attack` | `Cut`, `Flat`, `Boost` |
| `bypass_behavior` | `Toggle`, `Heel Down`, `Toe Down` |
| `clipping_dist` | `Overdrive`, `Boost`, `Distortion` |
| `comp_mode` | *(mode names)* |
| `comp_ratio` | `2:1`, `3:1`, `4:1`, `6:1`, `10:1`, `20:1` |
| `voltage` | `9V`, `18V` |
| `vowel_start` / `vowel_end` | `A`, `E`, `I`, `O`, `U` |
| `wave_shape` | `Saw Up`, `Saw Down`, `Triangle`, `Sine`, `Square`, `Inverse Sine`, `Random` |
| `ashville_pattern` | `Off`, `Stair`, `Cascade`, `Cross`, `Brownian`, `Random`, `Band Expansion`, `Down/Up`, `Pulsar`, `Grow/Shrink`, `Double Cascade`, `Rhythmicon`, `Double X`, `Perpetual`, `Pyramid`, `Double Dip`, `Inverted`, `Prime`, `Folded`, `Breakbeat`, `Big Beat` |
| `variax_str[1-6]tuning` | 25 semitone labels per string, e.g. `"-12 (E)"` … `"+12 (E)"` (note name varies by string) |

---

## Parameter Naming Conventions

Root keys follow recognisable patterns:

| Pattern | Meaning |
|---------|---------|
| `eq_*`, `mod_*`, `cab_*`, `amp_*`, `comp_*` | Category-scoped variant (e.g. `eq_low_cut`) |
| `dualCab_*`, `dualIR_*` | Dual-cab / dual-IR specific variant |
| `ashville_*`, `tubepre_*`, `CabMicIr_*`, `Shimmer_*`, `FlexoVibe_*` | Model-specific parameter |
| `variax_str[1-6]*` | Per-string Variax control |
| `*_old` | Legacy / deprecated variant |
| `*_1based` | Integer parameter indexed from 1 |
| `*_0_2000`, `*_10_1000` | Name encodes the min–max range |

---

## Directional / Balance Display Pattern

Several parameters use range-based formatting to display a negative/zero/positive
value as a named direction:

```json
"pan": {
  "minimumValue": -100,
  "maximumValue": 100,
  "zeroValue": 0.0,
  "format": [
    { "lowerBound": -99999, "upperBound": -0.5,   "formatUnits": "Left %.0f",  "unitsMultiplier": -1 },
    { "lowerBound": -0.5,   "upperBound": 0.5,    "formatUnits": "Center" },
    { "lowerBound": 0.5,    "upperBound": 999999, "formatUnits": "Right %.0f" }
  ],
  "step": { "fine": 1.0, "coarse": 10.0 }
}
```

The same pattern appears on `split_ab_route_to`, `tilt`, and other
centre-zero parameters. `unitsMultiplier: -1` negates the value so the left
side displays as a positive number.

---

## Unit Conversion Pattern

When a parameter crosses a unit boundary (e.g. ms → s, Hz → kHz), the upper
range object applies `unitsMultiplier` and switches `formatUnits`:

```json
"time_ms": {
  "format": [
    { "lowerBound": 0,    "upperBound": 9.999,  "formatUnits": "%.1f ms" },
    { "lowerBound": 9.999,"upperBound": 1000,   "formatUnits": "%.0f ms" },
    { "lowerBound": 1000, "upperBound": 99999,  "unitsMultiplier": 0.001, "formatUnits": "%.3f s" }
  ]
}
```

---

## Special Display Values

Some parameters use sentinel ranges to display non-numeric labels:

| Parameter | Sentinel | Displayed as |
|-----------|----------|--------------|
| `time_sec_DynamicHall` | value ≥ 45.1 | `"Infinity"` |
| `dualCab_time_ms_withauto` | negative values | `"Auto"` |
| `dualIR_time_ms` | negative values | `"A XXms"` (pre-delay) |
| `rochester_ratio` | very high values | `"∞:1"` |
| `dynamic_ambience_shape` | ranges 0–1.0 | `"Early 100"` … `"Even"` … `"Late 100"` (200 named steps) |

---

## Scale Fields

| Field | Purpose | Example values |
|-------|---------|----------------|
| `dspToDisplayScale` | Converts raw DSP integer to display float | `1`, `10`, `100`, `1000`, `0.001` |
| `displayToWidgetScale` | Scales display value for widget resolution | `2`, `4`, `5`, `10`, `20`, `100`, `200`, `1000`, `2500`, `5000` |
| `dspToDisplayIntegerOffset` | Integer offset after scaling | `−1`, `+1` (for 1-based index params) |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total root entries | ~300 |
| Control definition entries | ~150 |
| Alias entries | ~150 |
| Discrete parameters | ~80 |
| Continuous parameters | ~70 |
| Params with range-based steps | ~40 |
| Params with range-based formats | ~100 |
| Longest format array | 200+ entries (`dynamic_ambience_shape`) |
| Maximum nesting depth | 4 levels |
