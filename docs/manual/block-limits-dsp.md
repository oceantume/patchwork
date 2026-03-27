# Block Limits & DSP Rules

## Hard Block Limits Per Preset

| Block Type | Limit |
|---|---|
| Processing blocks (amps, effects, etc.) | Max 8 |
| Amp+Cab, Amp, or Preamp blocks | Any combination, up to 2 |
| Cab blocks (includes Amp+Cab blocks) | Up to 2 Single Cab blocks, or 1 Dual Cab block |
| IR blocks | Up to 2 × 1024-point Single IR, up to 2 × 2048-point Single IR, or 1 Dual IR block |
| Polyphonic / high-DSP effects | 1 per preset (see list below) |
| Looper block | 1 per preset |

Every preset also has an Input block, an Output block, and (if using parallel routing) a Split block and a Mixer block — these do not count toward the 8-block limit.

## Polyphonic / High-DSP Effects (one per preset)

- Feedbacker (Dynamics)
- Poly Sustain (Delay)
- Poly Detune (Modulation)
- Poly Pitch (Pitch/Synth)
- Poly Wham (Pitch/Synth)
- Poly Capo (Pitch/Synth)
- 12 String (Pitch/Synth)

## DSP Budget Rules

- Amps, IRs, Reverbs, and polyphonic pitch-shifting models consume the most DSP.
- Stereo version of an effects block uses roughly 2× the DSP of its mono version.
- Dual Cab or Dual IR block uses roughly 2× the DSP of a Single version.
- Legacy effects (from classic Line 6 pedals) generally use less DSP than Mono/Stereo HX models.
- IR-based Cab blocks and IR blocks (firmware 3.50+) use significantly less DSP than original Legacy Cab blocks.
- Some categories have "Simple" blocks that use less DSP than others.

## Non-Bypassable Blocks

Input, Output, Split, and Mixer blocks cannot be bypassed individually (they are structural to the signal path).

## DSP Optimization Strategies

- Use a Preamp block instead of a full Amp block when feeding a real amp (less DSP, no power-amp stage).
- Use a single Amp block followed by a Dual Cab block instead of two separate Amp+Cab blocks on a parallel path.
- Choose Mono over Stereo effect variants when stereo imaging is not needed.
- Choose Single Cab/IR over Dual when possible.
- Use Legacy or Simple effect variants when full HX fidelity is not required.
- Avoid stacking multiple polyphonic effects — only one is allowed per preset.
- Use snapshots or controllers to switch parameter values within a single block instead of duplicating blocks with different settings.
- Grayed-out models in the model list indicate insufficient DSP to accommodate them.
