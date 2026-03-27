# Amp, Cab, and IR Block Parameters

## Amp Parameters

These tonestack and power-amp parameters are common across Amp, Amp+Cab, and Preamp blocks, though the exact controls available vary by amp model.

**Drive** controls the amount of preamp overdrive, distortion, or fuzz; higher values produce more gain and saturation, lower values give a cleaner, more transparent tone.

**Bass** adjusts the low-frequency level of the amp's tonestack; higher values add warmth and weight, lower values thin out the low end.

**Mid** adjusts the midrange level of the tonestack; higher values push the mids forward for a more present or honky sound, lower values scoop them for a scooped modern tone.

**Treble** adjusts the high-frequency level of the tonestack; higher values add bite and clarity, lower values darken the tone.

**Presence** controls upper-midrange and high-frequency content in the power amp stage; higher values add definition and edge, lower values produce a smoother, less aggressive sound.

**Master** adjusts overall amp output level and power-amp distortion; it is highly interactive with all other power-amp parameters — the lower Master is set, the less effect those controls have.

**Sag** simulates power-supply sag in the amp's rectifier; lower values give a tighter, more controlled response suited to fast metal playing, higher values add touch dynamics and sustain suited to blues and classic rock.

**Bias** changes the operating bias of the power tubes; lower values produce "colder" Class AB biasing, and at maximum the amp operates in Class A.

## Preamp vs. Full Amp

An **Amp** block is identical to an **Amp+Cab** block except it contains no matched cab model; a **Preamp** block models only the preamp stage of the amp with no power-amp simulation, uses less DSP than a full Amp block, and is recommended when feeding HX Stomp into the power-amp input of a real amplifier.

## Cab Parameters

The following parameters are available on **Cab – Single** and **Cab – Dual** blocks, as well as when editing the cab portion of an **Amp+Cab** block.

### Single & Dual Cab Parameters

| Parameter | Description |
|---|---|
| **Mic** | Selects the guitar or bass mic model used on the cabinet. |
| **Distance** | Sets the mic-to-speaker distance from 1 to 12 inches; farther distances produce a darker, more diffuse tone. |
| **Position** | Sets the mic's left/right position from the center of the cone to its edge; off-center positions soften the high-end response. |
| **Angle** | Selects the mic angle: 0° (on-axis) for a brighter, more direct sound or 45° (off-axis) for a softer, more rounded tone. |
| **Low Cut** | High-pass filter (Off to 500 Hz) that removes low-frequency rumble from the cab output. |
| **High Cut** | Low-pass filter (Off down to 500 Hz) that removes high-end harshness from the cab output. |
| **Level** | Adjusts the overall output level of the cab block. |

### Dual Cab-Only Parameters

**Pan** adjusts the left/right stereo balance independently for each cab in a Dual Cab block; panning the two cabs opposite creates a wider stereo image.

**Delay** adds up to 50 ms of delay to the selected cab; use it to time-align the two cabs when they are also panned opposite, simulating the effect of two microphones at different distances; the "Auto" option derives the delay automatically from the cab's Distance setting.

## Dual Cab

A **Dual Cab** block contains two independent cab models in a single block, each with its own Mic, Distance, Position, Angle, Low Cut, High Cut, Level, Pan, and Delay settings, with stereo output; it uses approximately 2× the DSP of a Single Cab block.

## IR Block Parameters

HX Stomp stores up to 128 custom or third-party IRs; each preset may use a **Single IR** block (1024-sample or 2048-sample, mono) or a **Dual IR** block (two IRs in one stereo block).

### Per-IR Parameters (both Single and Dual)

| Parameter | Description |
|---|---|
| **IR Select** | Loads an IR by index (1–128) from the IR Library. |
| **Low Cut** | High-pass filter that removes low-frequency rumble from the IR output. |
| **High Cut** | Low-pass filter that removes high-end harshness from the IR output. |
| **Mix** | Blends dry and IR-processed (wet) signals; 0% = fully dry, 100% = fully wet. |
| **Level** | Adjusts the overall output level of the IR. |

### Dual IR-Only Parameters

**Pan** positions the output of each IR independently up to 100% left or 100% right.

**Polarity** sets each IR's phase to Normal or Inverted; if audible phasing occurs when combining two IRs, try inverting one.

## IR and Cab Block Limits

The IR block limit is shared with the v3.50 Cab and Amp+Cab block types.

| Configuration | Limit |
|---|---|
| Amp+Cab, Amp, or Preamp blocks | Any combination, up to 2 per preset |
| Single Cab blocks | Up to 2 per preset |
| Dual Cab block | Up to 1 per preset |
| Single IR blocks (1024-point) | Up to 2 per preset |
| Single IR blocks (2048-point) | Up to 2 per preset |
| Dual IR block | Up to 1 per preset |
