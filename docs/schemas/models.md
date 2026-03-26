# Line6 HX Edit `.models` File Schema

Reference documentation for the JSON schema used in `.models` files located in
`C:\Program Files (x86)\Line6\HX Edit\res`.

---

## Files

19 `.models` files cover all effect categories:

| File | Category |
|------|----------|
| `amp.models` | Amplifier models |
| `cab.models` | Cabinet models |
| `cabmicirs.models` | Cabinet mic IR models |
| `cabmicirswithpan.models` | Cabinet mic IR with pan |
| `compressor.models` | Compressor effects |
| `delay.models` | Delay effects |
| `distortion.models` | Distortion effects |
| `eq.models` | EQ effects |
| `filter.models` | Filter effects |
| `fixed.models` | Global / system parameters |
| `gate.models` | Gate effects |
| `io.models` | Input / Output models |
| `modulation.models` | Modulation effects |
| `pitch-synth.models` | Pitch / Synth effects |
| `preamp.models` | Preamp models |
| `reverb.models` | Reverb effects |
| `sendreturn.models` | Send / Return FX loop |
| `volumepan.models` | Volume / Pan models |
| `wah.models` | Wah effects |

---

## Root Structure

Every `.models` file is a JSON **array** of model objects:

```json
[
  { /* model object */ },
  { /* model object */ }
]
```

---

## Top-Level Model Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `symbolicID` | string | Yes | Unique model identifier (e.g. `"HD2_AmpGermanMahadeva"`) |
| `name` | string | Yes | Display name (e.g. `"German Mahadeva"`) |
| `category` | number | Yes | Category code — see [Category Codes](#category-codes) |
| `mono` | boolean | No | Supports mono operation |
| `stereo` | boolean | No | Supports stereo operation |
| `load` | number | No | DSP CPU load in mono |
| `load_stereo` | number | No | DSP CPU load in stereo |
| `cablink` | string | No | `symbolicID` of the linked cabinet model |
| `ircablink` | string | No | `symbolicID` of the linked IR cabinet model |
| `capEdge` | number | No | Capacity edge value |
| `devices` | array | No | Device / firmware compatibility list — see [`devices`](#devices-array) |
| `params` | array | Yes | Parameter definitions — see [`params`](#params-array) |
| `meterChannels` | number | No | Number of meter channels |
| `meterMin` | number | No | Meter minimum level (dB) |
| `meterMax` | number | No | Meter maximum level (dB) |

### Example

```json
{
  "symbolicID": "HD2_AmpGermanMahadeva",
  "name": "German Mahadeva",
  "category": 1,
  "mono": true,
  "stereo": true,
  "load": 4.60,
  "load_stereo": 8.28,
  "cablink": "HD2_Cab1x12Lead80",
  "ircablink": "HD2_CabMicIr_4x12UberV30",
  "params": [ /* ... */ ]
}
```

---

## Category Codes

| Value | Category |
|-------|----------|
| 1 | Amp |
| 2 | Cabinet |
| 3 | Distortion |
| 4 | Compressor / Gate |
| 6 | Filter |
| 7 | Pitch / Synth |
| 8 | Modulation |
| 9 | Delay |
| 10 | Reverb |
| 11 | Wah |
| 12 | FX Loop / Send-Return |
| 13 | Preamp |
| 14 | EQ |
| 17 | Volume / Pan |
| 19 | Cabinet Mic IR (with Position) |

---

## `devices` Array

Specifies hardware device and minimum firmware version compatibility.

```json
"devices": [
  { "id": 2162944, "version": "0x03190100" },
  { "id": 2162945 }
]
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | number | Yes | Hardware device identifier |
| `version` | string | No | Minimum firmware version as a hex string |

---

## `params` Array

An ordered array of parameter definition objects.

### Parameter Object

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `symbolicID` | string | Yes | Parameter identifier (e.g. `"Drive"`, `"@enabled"`) |
| `name` | string | Yes | Display name shown in the UI |
| `valueType` | number | Yes | Data type — see [Value Types](#value-types) |
| `displayType` | string | No | UI display format — see [Display Types](#display-types) |
| `min` | number \| boolean | Yes | Minimum value |
| `max` | number \| boolean | Yes | Maximum value |
| `default` | number \| boolean | Yes | Default value |
| `assign` | number | No | MIDI assignment slot (1–8) |
| `displayType_stereo` | string | No | Overrides `displayType` when in stereo mode |
| `max_stereo` | number | No | Overrides `max` when in stereo mode |
| `stereo-only` | boolean | No | When `true`, parameter is only available in stereo mode |

### Example

```json
{
  "symbolicID": "Drive",
  "name": "Drive",
  "valueType": 1,
  "displayType": "generic_knob",
  "min": 0.0,
  "max": 1.0,
  "default": 0.5,
  "assign": 1
}
```

---

## Value Types

| Value | Type | `min` / `max` form |
|-------|------|--------------------|
| `0` | Integer | numbers |
| `1` | Float | numbers |
| `2` | Boolean | `false` / `true` |
| `3` | String | `""` (empty strings) |

---

## Display Types

Display types control how a parameter value is rendered in the UI.

### Volume / Level

| `displayType` | Description |
|---------------|-------------|
| `volume` | dB volume scale (typically −60.0 to +12.0) |
| `volume_eq` | EQ gain scale (typically −15.0 to +15.0) |
| `percent` | Normalised percentage (0.0–1.0) |
| `percent_braced` | Percentage with bracket notation |

### Frequency

| `displayType` | Description |
|---------------|-------------|
| `frequency` | Generic frequency in Hz |
| `eq_low_cut` | EQ low-cut frequency |
| `eq_high_cut` | EQ high-cut frequency |
| `cab_low_cut` | Cabinet low-cut frequency |
| `cab_high_cut` | Cabinet high-cut frequency |
| `mod_low_cut` | Modulation low-cut frequency |
| `mod_high_cut` | Modulation high-cut frequency |

### Knobs

| `displayType` | Description |
|---------------|-------------|
| `generic_knob` | Standard normalised knob (0.0–1.0) |
| `q_knob` | Q factor (typically 0.1–10.0) |
| `tilt` | Tilt control (0.0–1.0) |

### Time

| `displayType` | Description |
|---------------|-------------|
| `time_ms_0_8000` | Time in ms, range 0–8000 |
| `time_ms_0_4000` | Time in ms, range 0–4000 |
| `time_ms_10_2000` | Time in ms, range 10–2000 |
| `time_ms_input` | Input timing |
| `time_ms_reverb` | Reverb timing |
| `comp_decay_10_1000` | Compressor decay, range 10–1000 ms |
| `comp_hold_time` | Gate / compressor hold time |

### Selectors

| `displayType` | Description |
|---------------|-------------|
| `mic` | Microphone selection (0–15) |
| `cabMICir` | Cabinet mic IR selection (0–11) |
| `CabMicIr_Position` | Mic position slider |
| `CabMicIrs_Angle` | Mic angle control |
| `pitch` | Pitch in semitones (typically −24 to +24) |
| `key_voice` | Musical key selection |
| `scale_voice` | Scale selection |
| `sync_note` | Note sync (BPM subdivision) |
| `chorus_mode` | Chorus mode selector |
| `comp_mode` | Compressor mode selector |
| `volume_curve` | Volume taper curve selector |
| `off_on` | Off / On toggle display |
| `pan` | Stereo pan (0.0 = full left, 1.0 = full right) |

### I/O

| `displayType` | Description |
|---------------|-------------|
| `guitar_input_z` | Guitar input impedance selector |
| `guitar_pad` | Guitar input pad selector |
| `powercab_select` | Powercab model selection |

---

## System / Meta Parameters

Parameters whose `symbolicID` begins with `@` are system or meta parameters and
are not directly associated with an effect algorithm.

| `symbolicID` | `valueType` | Typical Range | Description |
|---|---|---|---|
| `@enabled` | 2 (bool) | `false`–`true` | Enable / disable the block |
| `@stereo` | 2 (bool) | `false`–`true` | Toggle stereo mode |
| `@trails` | 2 (bool) | `false`–`true` | Allow signal trail on bypass (delay / reverb) |
| `@bypassvolume` | 1 (float) | 0.0–1.0 | Output level during bypass |
| `@mic` | 0 (int) | varies | Microphone selection |
| `@input` | 0 (int) | 0–16 | Input source selection |
| `@tempo` | 1 (float) | 20.0–240.0 | Global BPM |
| `@topology0` | 3 (string) | `""` | DSP 0 topology |
| `@topology1` | 3 (string) | `""` | DSP 1 topology |
| `@pedalstate` | 0 (int) | 0–2 | Pedal state |
| `@cursor_dsp` | 0 (int) | 0–1 | Cursor DSP position |
| `@cursor_group` | 3 (string) | `""` | Cursor group |
| `@cursor_path` | 0 (int) | 0–1 | Cursor path |
| `@cursor_position` | 0 (int) | 0–7 | Cursor position in the signal chain |
| `@current_snapshot` | 0 (int) | 0–7 | Active snapshot index |
| `@guitarinputZ` | 0 (int) | 0–8 | Guitar input impedance |
| `@guitarpad` | 0 (int) | 0–2 | Guitar input pad |
| `@PowercabSelect` | 0 (int) | varies | Powercab model selection |

### Standard tail pattern

Most effect blocks end with these two parameters:

```json
{
  "symbolicID": "@enabled",
  "name": "Enabled",
  "valueType": 2,
  "min": false,
  "max": true,
  "default": true
},
{
  "symbolicID": "@stereo",
  "name": "Stereo",
  "valueType": 2,
  "min": false,
  "max": true,
  "default": false
}
```

---

## File-Specific Notes

### `amp.models`
- Includes `cablink` and `ircablink` pointing to associated cabinet models.
- Effect parameters use `generic_knob` display type with a 0.0–1.0 range.

### `preamp.models`
- Same structure as `amp.models` but without `cablink` / `ircablink`.

### `cab.models`
- Includes `@mic` parameter for microphone selection.
- Standard parameters: Distance, LowCut, HighCut, Level.

### `cabmicirs.models` / `cabmicirswithpan.models`
- `cabmicirswithpan.models` extends the base IR cabinet schema with additional pan parameters.
- Uses `capEdge` field.

### `compressor.models` / `gate.models`
- Include `meterChannels`, `meterMin`, and `meterMax` fields for level metering.

### `delay.models`
- Uses `displayType_stereo` and `max_stereo` to provide different parameter ranges depending on mono/stereo mode.

### `reverb.models`
- Models are stereo-only: `"mono": false, "stereo": true`.
- Includes `@trails` parameter.

### `modulation.models`
- Many parameters carry `"stereo-only": true`.
- Frequent use of `sync_note` display type for BPM-synced rate controls.

### `eq.models`
- Multiple models with different band counts.
- Per-band parameters: Frequency, Q, Gain.
- Includes Low/High shelf controls.

### `fixed.models`
- Unique file — contains a single model entry with `symbolicID: "@global_params"`.
- Holds only system/global parameters (topology, cursor state, snapshot, etc.).
- String-type parameters use empty strings for `min`, `max`, and `default`.

### `io.models`
- Covers both Input and Output definitions.
- Input models include noise gate threshold and decay parameters.

### `volumepan.models`
- Minimal parameter sets (Gain, Pan, or Pedal only).
- Lowest CPU load values across all files (0.35–0.52).

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 19 |
| Total effect models | 100+ |
| Typical parameters per model | 5–14 |
| CPU load range (mono) | 0.35–28.27 |
| CPU load range (stereo) | ~0.51–12.8 |
| `valueType` categories | 4 |
| `displayType` formats | 25+ |
