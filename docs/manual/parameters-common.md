# Common Block Parameters

## Universal Parameters

**Mix** blends the effected "wet" signal against the "dry" signal passed through the block; 0% is completely dry, 100% is completely wet.

**Level** adjusts the overall output level of the effects block in dB; leave at 0.0 dB for most blocks to avoid digital clipping.

**Tone** (or **Treble**) adjusts the treble level of the effect's output.

## Time-Based Parameters

| Parameter | Units | Sync behavior |
|-----------|-------|---------------|
| **Time** | ms or note division | Note division value follows TAP Tempo / MIDI clock |
| **Speed** | Hz or note division | Note division value follows current tempo |
| **Rate** | numeric or note division | Note division value follows current tempo |

Note division values are retained when changing models; not all Rate or Speed parameters support note-value sync because some are non-linear and highly interactive.

## Rate and Speed Parameters

**Speed** adjusts the speed of a modulation effect; higher settings produce faster rates and can be set in Hz (cycles per second) or note divisions.

**Rate** adjusts the rate of an effect; higher settings produce faster rates and can be set in numeric or note-division values.

## Compressor and Gate Parameters

The manual's Common FX Settings section documents the following dynamics-related parameters:

| Parameter | Definition |
|-----------|------------|
| **Thresh[old]** | Sets the input level at which the gate or compressor acts on the signal. |
| **Decay** | Determines how abruptly the gate closes once the signal drops below the threshold level. |
| **Gate** | Turns the Input block's built-in noise gate on or off. |

Compressor models (e.g., Kinky Boost, Xotic SP Compressor-based models) expose model-specific Ratio, Attack, Release, and Makeup Gain knobs whose exact ranges vary by model; the common gate on the Input block exposes only Threshold and Decay.

## Delay Parameters

**Time** sets the delay/repeat time; higher values produce longer delays; can be set in ms or note divisions.

**Feedbk** adjusts the amount of delayed signal fed back into the effect; higher settings produce more dramatic textures and longer echo trails.

**Scale** (multi-tap delays) adjusts each tap's time relative to the main Time value, so all taps scale proportionally when the master Time is changed.

**Spread** adjusts how widely repeats pan left and right in stereo delay models; for modulated stereo delays it controls LFO phase offset between sides.

## Reverb Parameters

**Decay** sets the length of time the reverb effect sustains.

**Predly** (Pre-Delay) determines the time before the reverb effect is heard.

**Diffusion** is not explicitly listed as a universal parameter in this manual section; individual reverb models expose their own diffusion-style controls.

**Mix** at 0% bypasses the reverb completely; at 100% the entire path feeds through the effect with no dry signal.

## Modulation Parameters

**Depth** adjusts the intensity of the modulation; higher settings result in more extreme pitch bending, wobble, or throb depending on the effect.

**Rate** / **Speed** set the oscillation speed of the LFO driving the modulation effect (see Rate and Speed Parameters above).

## Return Block Mix Gotcha

**Mix** on a Return block blends the Return signal against the dry signal passing through the block; when set to 0% the path bypasses the Return completely and no external signal is heard, and when set to 100% the entire signal comes from the Return jack with no dry-through signal.
