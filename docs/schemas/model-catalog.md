# Line6 HX Edit `HX_ModelCatalog.json` Schema

Reference documentation for `C:\Program Files (x86)\Line6\HX Edit\res\HX_ModelCatalog.json`.

**File stats:** ~11,759 lines, ~527 KB, 900+ models across 24 categories.

---

## Root Structure

The file is a single JSON object with one top-level key:

```json
{
  "categories": [ /* array of category objects */ ]
}
```

---

## Category Object

Each element of `categories` describes one effect/signal-chain category.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | number | Yes | Unique category identifier (0–23) |
| `name` | string | Yes | Display name (e.g. `"Distortion"`) |
| `shortName` | string | Yes | Abbreviated name (e.g. `"Dist"`) |
| `image` | string \| null | Yes | Category icon filename; `null` for Connected Devices |
| `color` | string | Yes | UI accent color as `"0xRRGGBB"` |
| `subcategories` | array | Conditional | Present when the category groups models into subcategories |
| `models` | array | Conditional | Present when models are listed directly (no subcategories) |

Categories either contain `subcategories` **or** `models` directly — never both.
Category 23 (Favorites) has neither.

### Example — category with subcategories

```json
{
  "id": 1,
  "name": "Distortion",
  "image": "FX_HX_Category_Distortion.png",
  "shortName": "Dist",
  "color": "0xf5901e",
  "subcategories": [ /* ... */ ]
}
```

### Example — category with direct models

```json
{
  "id": 18,
  "name": "Input",
  "image": "icon-input-category.png",
  "shortName": "Input",
  "color": "0x989898",
  "models": [ /* ... */ ]
}
```

---

## Category Enumeration

| `id` | `name` | `shortName` | `color` | Structure |
|------|--------|-------------|---------|-----------|
| 0 | None | None | `0xffffff` | direct models |
| 1 | Distortion | Dist | `0xf5901e` | subcategories |
| 2 | Dynamics | Dyn | `0xffffff` | subcategories |
| 3 | EQ | EQ | `0xffffff` | subcategories |
| 4 | Modulation | Mod | `0xffffff` | subcategories |
| 5 | Delay | Delay | `0x00CC00` | subcategories |
| 6 | Reverb | Reverb | `0x38A696` | subcategories |
| 7 | Pitch | Pitch | `0xA844DB` | subcategories |
| 8 | Filter | Filter | `0xAD46E2` | subcategories |
| 9 | Inverter | Inv | `0xDDCC00` | subcategories |
| 11 | Amp | Amp | `0xDD1111` | subcategories |
| 12 | Preamp | Pre | `0xDD1111` | subcategories |
| 13 | Cab | Cab | `0xDD1111` | subcategories |
| 14 | Cab Match | Cab M | `0xDD1111` | subcategories |
| 15 | IR | IR | — | direct models |
| 16 | Mic | Mic | — | direct models |
| 17 | Legacy | Legacy | — | direct models |
| 18 | Input | Input | `0x989898` | direct models |
| 19 | Output | Output | `0x989898` | direct models |
| 20 | Split | Split | `0x989898` | direct models |
| 21 | Merge | Merge | `0x989898` | direct models |
| 22 | Connected Devices | Devices | `0x989898` | direct models |
| 23 | Favorites | Favorites | `0xF0F0F0` | none |

> ID 10 is not present in the catalog (gap reserved for future use).

---

## Subcategory Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | Yes | Subcategory display name |
| `id` | number | Yes | Subcategory identifier (contextual, typically 1–10) |
| `models` | array | Yes | Models within this subcategory |

**Common subcategory names:**

| Name | Used in |
|------|---------|
| Mono | Distortion, EQ, Modulation, Delay, … |
| Stereo | Distortion, EQ, Modulation, Delay, … |
| Guitar | Amp, Dynamics, … |
| Bass | Amp, Dynamics, … |
| Legacy | Most effect categories |
| Single | Cab |
| Dual | Cab |
| Quick | Cab |
| Dual Plus | Cab |
| Double | Cab |

### Example

```json
{
  "name": "Mono",
  "id": 4,
  "models": [ /* ... */ ]
}
```

---

## Model Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | string | Yes | Unique model identifier (see [ID Prefixes](#model-id-prefixes)) |
| `name` | string | Yes | Display name (e.g. `"Kinky Boost"`) |
| `image` | string | Yes | Model icon filename |
| `image_native` | string | No | Alternative icon for native-mode devices |
| `params` | array | Usually | Parameter list (see [Params Array](#params-array)) |

### Example

```json
{
  "id": "HD2_DistKinkyBoost",
  "name": "Kinky Boost",
  "image": "FX_HX_DIST_KinkyBoost.png",
  "params": [
    { "Drive": null },
    { "Boost": null },
    { "Bright": null }
  ]
}
```

---

## Model ID Prefixes

| Prefix | Source / type |
|--------|--------------|
| `HD2_` | Standard Helix effect or model (most common) |
| `VIC_` | Victory amplifier / module |
| `HelixFx_` | Internal application / DSP flow model |
| `@` | External connected device (Variax, Powercab, DT amp) |

**Examples:**
- `HD2_DistKinkyBoost` — Helix distortion effect
- `VIC_FlexoVibe` — Victory modulation
- `HelixFx_AppDSPFlowInput` — App-internal input block
- `@variax` — Line 6 Variax guitar
- `@powercab` — Line 6 Powercab speaker
- `@dt` — DT 25 / DT 50 amplifier

---

## Params Array

`params` is an ordered array where each element is either:

- A **parameter object** `{ "ParamID": null | "Display Label" }`, or
- A **tempo-sync group** (a nested array — see below).

### Parameter Object

Each parameter object has exactly one key-value pair:

| Key | Type | Description |
|-----|------|-------------|
| key | string | Parameter identifier — camelCase or with underscores |
| value | null \| string | `null` uses the key as the label; a string overrides the display label |

```json
{ "Drive": null }            // label = "Drive"
{ "Bass": "Bass Cut" }       // label = "Bass Cut"
{ "Gate_Range": "Gate Range" }
{ "@trails": "Trails" }
```

### Tempo-Sync Group

When a parameter supports BPM sync, it is represented as a **nested array** (always the first element of `params`):

```json
[
  { "TempoSync1": null },
  { "SyncSelect1": "Note Sync" },
  { "Time": null }
]
```

The group always contains three entries in order:
1. Tempo-sync toggle (`TempoSync1`)
2. Note-sync selector (`SyncSelect1`) — value is the display label, may vary (e.g. `"Note Sync (Chorus)"`)
3. The underlying time parameter that gets synced (e.g. `"Time"`, `"Speed"`, `"Rate"`)

### Full example — Delay with tempo sync

```json
{
  "id": "HD2_DelaySimpleDelay",
  "name": "Simple Delay",
  "image": "FX_HX_DELAY_Simple.png",
  "params": [
    [ { "TempoSync1": null }, { "SyncSelect1": "Note Sync" }, { "Time": null } ],
    { "Feedback": null },
    { "Mix": null },
    { "Level": null },
    { "@trails": "Trails" }
  ]
}
```

---

## Special (`@`-prefixed) Parameters

Parameters prefixed with `@` refer to external device controls or internal system values.

### `@trails`

| Param | Description |
|-------|-------------|
| `@trails` | Allow signal trail on bypass (delay / reverb blocks) |

### Variax parameters (`@variax_*`)

| Param | Description |
|-------|-------------|
| `@variax_model` | Guitar model selection |
| `@variax_volumeknob` | Volume knob |
| `@variax_toneknob` | Tone knob |
| `@variax_lockctrls` | Lock controls |
| `@variax_customtuning` | Custom tuning preset |
| `@variax_str[1-6]tuning` | Per-string tuning (6 params) |
| `@variax_str[1-6]level` | Per-string level (6 params) |

### Powercab parameters (`@powercab_*`)

| Param | Description |
|-------|-------------|
| `@powercab_speaker` | Speaker model selection |
| `@powercab_mic` | Mic selection |
| `@powercab_distance` | Mic distance |
| `@powercab_userir` | Use IR toggle |
| `@powercab_lowcut` | Low-cut frequency |
| `@powercab_hicut` | High-cut frequency |
| `@powercab_flatlevel` | Flat mode output level |
| `@powercab_speakerlevel` | Speaker mode output level |
| `@powercab_irlevel` | IR mode output level |
| `@powercab_color` | UI color |

### DT amp parameters (`@dt_*`)

| Param | Description |
|-------|-------------|
| `@dt_channel` | Channel selection |
| `@dt_topology` | Power amp topology |
| `@dt_poweramp` | Power amp class |
| `@dt_tubeconfig` | Tube configuration |
| `@dt_reverb` | Reverb toggle |
| `@dt_revmix` | Reverb mix |
| `@dt_12ax7boost` | 12AX7 boost |
| `@dt_feedbackcap` | Feedback capacitor |
| `@dt_bplusvoltage` | B+ voltage |

### Input parameters

| Param | Description |
|-------|-------------|
| `@guitarinputZ` | Guitar input impedance |
| `@guitarpad` | Guitar input pad |
| `@mic` | Microphone selection |

---

## Image File Naming Patterns

All paths are filenames only (no directory prefix).

### Category icons

| Pattern | Example |
|---------|---------|
| `FX_HX_Category_[Name].png` | `FX_HX_Category_Distortion.png` |
| `icon-[name]-category.png` | `icon-input-category.png` |

### Model icons

| Pattern | Example |
|---------|---------|
| `FX_HX_[CAT]_[ModelName].png` | `FX_HX_DIST_KinkyBoost.png` |
| `AMP_HX_[TYPE]_[ModelName].png` | `AMP_HX_GTR_WhoWatt100.png` |
| `PRE_HX_[ModelName].png` | `PRE_HX_SoupPro.png` |
| `CABMICIR_HX_[Name].png` | `CABMICIR_HX_SoupProEllipse.png` |
| `icon-[device].png` | `icon-variax.png`, `icon-powercab.png` |

Some images carry a parametric variant suffix: `_%[number]`
(e.g. `icon-inputs_%18.png`, `icon-inputs-native_%3.png`).
`image_native` uses the same convention with a `_native` infix.

---

## Color Values

The `color` field on category objects is always a hex string `"0xRRGGBB"`.

| Color | Hex | Used by |
|-------|-----|---------|
| White | `0xffffff` | None, Dynamics, EQ, Modulation |
| Orange | `0xf5901e` | Distortion |
| Green | `0x00CC00` | Delay |
| Teal | `0x38A696` | Reverb |
| Purple | `0xA844DB` | Pitch |
| Purple | `0xAD46E2` | Filter |
| Yellow | `0xDDCC00` | Inverter |
| Red | `0xDD1111` | Amp, Preamp, Cab, Cab Match |
| Gray | `0x989898` | Input, Output, Split, Merge, Connected Devices |
| Light gray | `0xF0F0F0` | Favorites |

---

## Complete Field Reference

| Level | Field | Type | Required |
|-------|-------|------|----------|
| Root | `categories` | array | Yes |
| Category | `id` | number | Yes |
| Category | `name` | string | Yes |
| Category | `shortName` | string | Yes |
| Category | `image` | string \| null | Yes |
| Category | `color` | string (`"0xRRGGBB"`) | Yes |
| Category | `subcategories` | array | Conditional |
| Category | `models` | array | Conditional |
| Subcategory | `id` | number | Yes |
| Subcategory | `name` | string | Yes |
| Subcategory | `models` | array | Yes |
| Model | `id` | string | Yes |
| Model | `name` | string | Yes |
| Model | `image` | string | Yes |
| Model | `image_native` | string | No |
| Model | `params` | array | Usually |
| Parameter | key (single) | string | Yes |
| Parameter | value | null \| string | Yes |
| Tempo-sync group | array of 3 parameter objects | — | — |
