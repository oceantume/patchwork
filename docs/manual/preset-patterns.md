## Design Patterns

**Parallel reverb/delay** — Place reverb on Path B and delay on Path A so the two effects do not feed into each other, producing cleaner, more defined notes than a serial arrangement.

| Element | Path A | Path B |
|---------|--------|--------|
| Signal | Dry + Delay block | Reverb block |
| Merge | Mixer block recombines both paths at the Output | |

**Dry signal bypass** — Route the unprocessed signal through Path A and all wet effects through Path B; the Mixer block blends them back together, useful when effect blocks lack a Mix/Blend control, especially for clean/distorted bass blending.

**Multi-amp setup** — Up to two Amp+Cab, Amp, or Preamp blocks (any combination) are allowed per preset; use a single Amp block followed by a Dual Cab block instead of two full Amp+Cab blocks to reduce DSP consumption while still mixing two cabinet colours.

| Block type | Limit |
|-----------|-------|
| Amp+Cab / Amp / Preamp | Any combination, up to 2 per preset |
| Single Cab (or Amp+Cab cab) | Up to 2 per preset |
| Dual Cab | 1 per preset |

**Stereo widening** — In a Dual Cab block, pan Cab A and Cab B in opposite directions using the per-cab Pan parameter; choosing two different cab models and panning them oppositely produces a wider stereo image.

**Song-section snapshots** — Assign Snapshot 1 to Intro, Snapshot 2 to Verse, and Snapshot 3 to Chorus; each snapshot independently stores block bypass states, up to 64 controller-assigned parameter values, Command Center message states, and (optionally) tempo.

**Tempo-synced effects** — Set Delay or Modulation Time/Speed parameters to note-division values (e.g., 1/4, dotted 1/8) instead of fixed ms/Hz values so they follow Tap Tempo or incoming MIDI clock; press the parameter knob to toggle between ms and note-division modes.

**Expression pedal blend** — Assign EXP 1 or EXP 2 to a block's Mix parameter to smoothly blend that effect into the dry signal; multiple parameters on the same block (or across blocks) can share the same pedal assignment, each with its own Min/Max range.

---

## TIP Callouts Relevant to Preset Construction

**Parallel routing — both paths are stereo.** With parallel routing, Paths A and B are each full stereo paths, so mono or stereo blocks can be placed on either path and panned independently via the Mixer block.

**Stereo effects on mono rigs.** Even when running into a single amp or mono playback system, stereo effects—especially stereo reverbs—can still sound fuller than their mono counterparts.

**Snapshots vs. duplicate blocks.** Instead of toggling between two copies of the same amp or effects block with different settings, use controllers or snapshots to adjust parameters within a single block; an amp model's tonestack knobs alone can produce dramatically different tones.

**Dual Cab linking.** When the global "Link Dual Cabs" option is on, selecting a cab model for Cab A automatically selects the same model for Cab B; disable this when the intention is to use two different cabs for stereo widening.

**FX Loop Mix blend.** To smoothly blend a hardware pedal inserted via an FX Loop block into the tone, assign EXP 1 or EXP 2 to control that block's Mix parameter.

**Split > A/B crossfade.** To morph between parallel paths A and B with an expression pedal, assign the Split > A/B block's Route To parameter to EXP 1 or EXP 2; heel-down sends the full signal to Path A, toe-down crossfades fully into Path B.

**Save before changing presets.** Any unsaved edits to the current preset are discarded as soon as a different preset is loaded; save early and save often.

**Snapshot Edits = Discard.** When Global Settings > Preferences > Snapshot Edits is set to "Discard," edits made to a snapshot are lost on switching snapshots unless the preset is saved first.

**Tempo scope per snapshot.** When Global Settings > MIDI/Tempo > Tempo Select is set to "Per Snapshot," each snapshot can store its own BPM value, enabling different tempos for different song sections within one preset.

---

## Warnings: Signal Chain and DSP

**Mono block collapses stereo.** Whenever a mono block appears anywhere in a path, both stereo channels are summed to mono at that point and stay mono for all downstream blocks in that path; place stereo blocks after mono blocks only if a wider image is not required for the rest of the chain.

**Two full Amp+Cab blocks in parallel is expensive.** Running two separate Amp+Cab (or Amp + Cab) combinations in a parallel path consumes roughly twice the DSP of a single Amp followed by one Dual Cab block; use Amp + Dual Cab when DSP headroom is limited.

**Stereo and Dual blocks cost double.** The stereo version of an effects block uses approximately twice the DSP of the equivalent mono block; similarly, a Dual Cab block uses approximately twice the DSP of a Single Cab block.

**One Poly/high-DSP effect per preset.** Polyphonic blocks—Poly Sustain, Poly Detune, Poly Pitch, Poly Wham, Poly Capo, 12-String, and Feedbacker—are limited to one per preset because of their high DSP cost.

**Grayed-out models cannot be added.** When a model appears grayed out in the model list, the current preset cannot accommodate it; reducing the DSP load by removing or swapping other blocks is required before it can be inserted.

**Unsaved snapshot edits are lost on preset change.** Selecting a different preset without saving discards all snapshot edits in the current preset; this applies regardless of the Snapshot Edits (Recall/Discard) setting.
