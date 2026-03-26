# Line6 HX Edit `.hlx` Preset File Schema

Reference documentation for the `.hlx` preset format used by HX Edit.
The format is JSON with a `.hlx` extension.

Template files are located in `C:\Program Files (x86)\Line6\HX Edit\res`:

| File | Device |
|------|--------|
| `default_preset.hlx` | Helix |
| `default_preset_hfx.hlx` | Helix FX |
| `default_preset_hxs.hlx` | Helix Stomp |
| `empty_preset.hlx` | Helix (blank template) |

---

## Root Structure

```json
{
  "version": 6,
  "schema": "L6Preset",
  "data": { ... }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `version` | number | Preset format version. Always `6`. |
| `schema` | string | Always `"L6Preset"`. |
| `data` | object | All preset content — see below. |

---

## `data` Object

| Key | Type | Description |
|-----|------|-------------|
| `meta` | object | Preset metadata — see [`meta`](#meta-object) |
| `device` | number | Hardware device ID — see [Device IDs](#device-ids) |
| `device_version` | number | Firmware version at save time (encoded integer); `0` in blank templates |
| `tone` | object | Signal chain and snapshot state — see [`tone`](#tone-object) |

---

## `meta` Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | Yes | Preset display name |
| `application` | string | No | Saving application (`"Helix Edit"` or `"HX Edit"`) |
| `build_sha` | string | No | Git SHA of the application build |
| `modifieddate` | number | No | Last-modified timestamp (Unix epoch) |
| `appversion` | number | No | Encoded application version integer |

`application`, `build_sha`, `modifieddate`, and `appversion` are absent from blank template files.

---

## Device IDs

| `device` value | Hardware |
|----------------|----------|
| `2162689` | Helix |
| `2162693` | Helix FX |
| `2162694` | Helix Stomp |

---

## `tone` Object

| Key | Type | Description |
|-----|------|-------------|
| `dsp0` | object | Primary DSP chain — see [DSP Object](#dsp-object) |
| `dsp1` | object | Secondary DSP chain; empty object `{}` on single-DSP devices |
| `global` | object | Global / session state — see [`global`](#global-object) |
| `snapshot0`–`snapshot7` | object | Per-snapshot state — see [Snapshot Object](#snapshot-object); count varies by device |

### Snapshot count by device

| Device | Snapshots present |
|--------|------------------|
| Helix | `snapshot0`–`snapshot7` (8) |
| Helix FX | `snapshot0`–`snapshot3` (4) |
| Helix Stomp | `snapshot0`–`snapshot2` (3) |

---

## DSP Object

Each DSP object (`dsp0`, `dsp1`) contains the signal routing components for
that processor. On single-DSP devices `dsp1` is an empty object.

| Key | Type | Description |
|-----|------|-------------|
| `inputA` | object | Primary input block — see [`inputA` / `inputB`](#inputa--inputb) |
| `inputB` | object | Secondary input block |
| `split` | object | Signal path splitter — see [`split`](#split) |
| `join` | object | Signal path joiner — see [`join`](#join) |
| `outputA` | object | Primary output block — see [`outputA` / `outputB`](#outputa--outputb) |
| `outputB` | object | Secondary output block |

Effect blocks placed on the signal chain are stored as additional keys in the
DSP object alongside these fixed routing components.

### `inputA` / `inputB`

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `@model` | string | Yes | Input model ID — see [Model IDs](#model-ids) |
| `@input` | number | Yes | Input path index (`0` or `1`) |
| `noiseGate` | boolean | No | Enable input noise gate (absent on Helix FX) |
| `threshold` | number | No | Noise gate threshold in dB; default `-48` |
| `decay` | number | No | Noise gate decay time; default `0.5` |

### `split`

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `@model` | string | Yes | Always `"HD2_AppDSPFlowSplitY"` |
| `@enabled` | boolean | Yes | Split active state |
| `@position` | number | Yes | Position index in the signal chain |
| `bypass` | boolean | No | Bypassed state |
| `BalanceA` | number | No | Level balance for path A (0.0–1.0; `0.5` = equal) |
| `BalanceB` | number | No | Level balance for path B (0.0–1.0; `0.5` = equal) |

### `join`

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `@model` | string | Yes | Always `"HD2_AppDSPFlowJoin"` |
| `@enabled` | boolean | Yes | Join active state |
| `@position` | number | Yes | Position index in the signal chain (`8` on Helix, `0` on FX/Stomp) |
| `A Level` | number | Yes | Level of path A into the mix (dB offset; `0` = unity) |
| `A Pan` | number | Yes | Pan of path A (0.0–1.0; `0.5` = centre) |
| `B Level` | number | Yes | Level of path B into the mix |
| `B Pan` | number | Yes | Pan of path B |
| `Level` | number | Yes | Master output level of the join block |
| `B Polarity` | boolean | Yes | Invert polarity of path B |

### `outputA` / `outputB`

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `@model` | string | Yes | Output model ID — see [Model IDs](#model-ids) |
| `@output` | number | Yes | Output path index (`0` or `1`) |
| `pan` | number | Yes | Stereo pan (0.0–1.0; `0.5` = centre) |
| `gain` | number | Yes | Output gain offset in dB (`0` = unity) |
| `Type` | boolean | No | Output type flag; present only on Helix Stomp `outputB` |

---

## `global` Object

Stores the active session state shared across all snapshots.
`@model` is always `"@global_params"`.

| Key | Type | Description |
|-----|------|-------------|
| `@model` | string | Always `"@global_params"` |
| `@pedalstate` | number | Pedal connection state (`2` = Helix, `0` = FX / Stomp) |
| `@tempo` | number | Global BPM; default `120` |
| `@topology0` | string | DSP 0 signal topology (`"A"` = series, `""` = parallel/none) |
| `@topology1` | string | DSP 1 signal topology (same values; `""` on single-DSP devices) |
| `@current_snapshot` | number | Index of the active snapshot (0-based) |
| `@cursor_dsp` | number | UI cursor: active DSP (`0` or `1`) |
| `@cursor_path` | number | UI cursor: active signal path (`0` or `1`) |
| `@cursor_position` | number | UI cursor: position in the chain |
| `@cursor_group` | string | UI cursor: group identifier (empty string by default) |
| `@guitarinputZ` | number | Guitar input impedance selection |
| `@variax_model` | number | Variax guitar model selection |
| `@variax_customtuning` | boolean | Variax custom tuning enabled |
| `@variax_lockctrls` | number | Variax lock controls state |
| `@variax_magmode` | boolean | Variax magnetic pickup mode |
| `@variax_str1tuning`–`@variax_str6tuning` | number | Per-string tuning offset in semitones (0 = standard) |
| `@variax_toneknob` | number | Variax tone knob position |
| `@variax_volumeknob` | number | Variax volume knob position |

---

## Snapshot Object

Each `snapshotN` key holds the state for that snapshot slot.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `@name` | string | Yes | Snapshot display name (e.g. `"SNAPSHOT 1"`) |
| `@tempo` | number | Yes | Snapshot-specific BPM; default `120` |
| `@pedalstate` | number | No | Pedal state at save time; absent in blank templates |
| `@ledcolor` | number | No | Scribble strip LED colour index; absent in blank templates |

---

## Model IDs

`@model` values in DSP routing components follow the pattern
`[Prefix]_AppDSPFlow[Component]`.

| `@model` | Device | Component |
|----------|--------|-----------|
| `HD2_AppDSPFlow1Input` | Helix | Primary input |
| `HD2_AppDSPFlow2Input` | Helix | Secondary input |
| `HD2_AppDSPFlowOutput` | Helix | Output (A and B) |
| `HD2_AppDSPFlowSplitY` | All | Split |
| `HD2_AppDSPFlowJoin` | All | Join |
| `HelixFx_AppDSPFlowInput` | Helix FX | Input (A and B share model) |
| `HelixFx_AppDSPFlowOutput` | Helix FX | Output (A and B) |
| `HelixStomp_AppDSPFlowInput` | Helix Stomp | Input (A and B share model) |
| `HelixStomp_AppDSPFlowOutputMain` | Helix Stomp | Main output (outputA) |
| `HelixStomp_AppDSPFlowOutputSend` | Helix Stomp | Send / aux output (outputB) |
| `@global_params` | All | Global parameters block |

---

## Variant Comparison

| Property | Helix | Helix FX | Helix Stomp | Empty template |
|----------|-------|----------|-------------|----------------|
| `device` | `2162689` | `2162693` | `2162694` | `2162689` |
| `device_version` | `33620327` | `37814625` | `37814625` | `0` |
| `dsp1` | Populated | `{}` | `{}` | Populated |
| Snapshot count | 8 | 4 | 3 | 8 |
| `@pedalstate` | `2` | `0` | `0` | `2` |
| `@topology1` | `"A"` | `""` | `""` | `"A"` |
| `@variax_magmode` | `true` | `false` | `false` | `false` |
| Input noise gate fields | Yes | No | Yes | Yes |
| Join `@position` | `8` | `0` | `0` | `8` |
| `outputB.Type` field | No | No | Yes | No |
| Snapshot `@ledcolor` / `@pedalstate` | Yes | Yes | Yes | No |
| `meta` build fields | Yes | Yes | Yes | No |

---

## Numeric Value Conventions

| Field | Range / default | Notes |
|-------|-----------------|-------|
| `pan` | 0.0–1.0 | `0.5` = centre |
| `gain` | dB offset | `0` = unity |
| `threshold` | dB | Default `−48` |
| `decay` | 0.0–1.0 | Default `0.5` |
| `BalanceA` / `BalanceB` | 0.0–1.0 | `0.5` = equal balance |
| `A Level` / `B Level` | dB offset | `0` = unity |
| `A Pan` / `B Pan` | 0.0–1.0 | `0.5` = centre |
| `@tempo` | BPM | Default `120` |
| `@variax_str*tuning` | semitones | `0` = standard pitch |
| `modifieddate` | Unix epoch seconds | e.g. `1478293021` |
