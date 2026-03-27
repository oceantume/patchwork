# Plan: Extract HX Stomp Manual Metadata into Agent-Friendly Docs

## Context

The project builds an AI agent that creates and edits HX Stomp presets (`.hlx` files). The manual
(`assets/manual_single.html`) contains essential knowledge for that agent — signal chain concepts,
effect categories, parameter semantics, constraints, etc. — buried in 68 pages of PDF-converted
HTML. The goal is to extract the relevant bits into focused, succinct markdown files under
`docs/manual/` so future agents can load only what they need.

## Source

- Manual: `assets/manual_single.html`
  - Converted from PDF via `pdftohtml`. Content is in `<p>` tags with absolute positioning.
  - Pages are delimited by `<!-- Page N -->` comments and `<a name="N">` anchors.
  - Sections are bold text (no semantic headings). Use page ranges below to navigate.

## Output Directory

`docs/manual/` (create if absent)

## Agent Style Guide

Each stage is designed to be handed to a single agent. When running a stage, instruct the agent:

> Read pages [X–Y] of `assets/manual_single.html` (delimited by `<!-- Page N -->` comments).
> Extract only what's described below and write it to `docs/manual/<file>`.
> Style: plain markdown, no fluff. Use short tables where data is tabular. One sentence per
> concept. No introductory paragraphs. Don't include hardware setup, UI navigation, MIDI
> implementation, or firmware update content.

---

## Stages

### Stage 1 — Glossary
**Output:** `docs/manual/glossary.md`
**Pages:** 4–5 (section "Common Terminology"), plus any term definitions found inline in pages 13–22
**Extract:**
- Every bolded term that is defined in the manual (Block, Model, Preset, Snapshot, Path, DSP, IR,
  Cab, Amp, Preamp, Amp+Cab, Send/Return, FX Loop, Split, Mixer, Looper, Controller, Bypass,
  Mix/Blend, TAP Tempo)
- One-sentence definition per term, in the manual's own words where possible
- Format: definition list (`**Term** — definition`)

---

### Stage 2 — Effect Categories
**Output:** `docs/manual/effect-categories.md`
**Pages:** 2 (table of contents for section list), 22–42 (The Blocks section)
**Extract:**
- All top-level effect categories (Distortion, Dynamics, EQ, Modulation, Delay, Reverb, Filter,
  Pitch/Synth, Amp, Preamp, Amp+Cab, Cab, IR, Send/Return, Looper)
- For each: one-sentence description of what it does / when to use it
- Note which categories are DSP-heavy (flag with ⚠ DSP)
- Note which have Mono / Stereo / Legacy subcategory variants
- Format: table with columns: Category | What it does | Variants | Notes

---

### Stage 3 — Block Limits & DSP Rules
**Output:** `docs/manual/block-limits-dsp.md`
**Pages:** 19–21 (Dynamic DSP, Block Order and Stereo Imaging)
**Extract:**
- Hard per-preset block limits (max 8 processing blocks, max 2 amps, max 2 single cabs or 1 dual
  cab, IR count limits, 1 looper, 1 send/return)
- DSP budget rules: polyphonic effects consume up to 50% DSP alone (list which ones), stereo
  variants ≈ 2× mono, dual cab/IR ≈ 2× single, Legacy effects cost less
- Blocks that cannot be bypassed (Input, Output, Split, Mixer)
- DSP optimization strategies (Preamp < Amp, Simple/Legacy variants, avoid stacking poly effects,
  use single not dual when possible)
- Format: sections with bullet lists; a table for the hard limits is helpful

---

### Stage 4 — Signal Chain & Routing
**Output:** `docs/manual/signal-chain.md`
**Pages:** 17–21 (Serial vs. Parallel Routing, Setting Path B's Output, Block Order)
**Extract:**
- Serial path: what it is, when to use it
- Parallel path: what Split and Mixer blocks do, Path A vs Path B
- Split block types: Y, A/B, Crossover, Dynamic — one sentence each plus key parameters
- Mixer block parameters: A/B levels, panning, polarity invert, Path B output routing
- Path B independent output: routing Path B to Send L/R
- Block order impact: why order matters (e.g., delay → reverb ≠ reverb → delay)
- Mono block behavior in a stereo chain (collapses to mono)

---

### Stage 5 — Snapshots
**Output:** `docs/manual/snapshots.md`
**Pages:** 43–45
**Extract:**
- What a snapshot is: 3 per preset, stores parameter values + bypass states
- What snapshots CAN store: block bypass states, up to 64 parameter values, pitch/key values, IR
  selections
- What snapshots CANNOT do: change block models, change block positions, control the Looper
- The 64-parameter limit per snapshot
- Snapshot Edits global setting: Recall vs. Discard — what each means for an agent writing params
- Snapshot copy/swap/rename capabilities (brief)

---

### Stage 6 — Common Parameters
**Output:** `docs/manual/parameters-common.md`
**Pages:** 13–15 (parameter adjustment), throughout effect sections (22–42)
**Extract:**
- Universal parameters present on most blocks: Mix/Blend (0% dry → 100% wet), Level (dB), Tone
- Time-based parameters: can be set in ms OR note divisions (1/4, dotted 1/8, 1/16, etc.);
  note divisions sync to TAP Tempo / MIDI clock
- Rate/speed parameters: Hz vs. note divisions, typical range
- Compressor/gate parameters: Threshold, Ratio, Attack, Release, Makeup Gain — brief definition each
- Delay parameters: Time, Feedback (100%+ = self-oscillation), Tone, multi-tap Scale
- Reverb parameters: Decay/Time, Pre-Delay, Diffusion, Mix
- Modulation parameters: Rate, Depth, typical behavior note
- Return block Mix gotcha: 0% = no external signal (bypass), 100% = wet only

---

### Stage 7 — Amp & Cab/IR Parameters
**Output:** `docs/manual/parameters-amp-cab.md`
**Pages:** 29–36 (Amp+Cab models, Amp models, Cab models, IR blocks)
**Extract:**
- Amp parameters: Drive, Bass, Mid, Treble, Presence, Master, Sag, Bias — one sentence each
  explaining what each controls and typical effect of high vs. low values
- Preamp vs. full Amp: what's different (no power amp stage = less DSP, use when feeding real amp)
- Cab parameters: Low Cut, High Cut, Distance, Delay (0–50ms, used for dual-cab time alignment),
  Pan, and which have Mic selection
- Dual Cab: two cabs in one block, independent pan — note 2× DSP cost
- IR block parameters: Mix, Pan, Delay, Low/High Cut; IR index (1–128 user slots)
- IR block limits combined with Cab limits (re-state concisely from block-limits-dsp.md)

---

### Stage 8 — Preset Design Patterns
**Output:** `docs/manual/preset-patterns.md`
**Pages:** Throughout — primarily 17–21 (routing), 43–45 (snapshots), plus all "TIP:" callouts
  across the whole manual (search for bold "TIP:")
**Extract:**
- Named design patterns with a one-line description and the key blocks/settings involved:
  - Parallel reverb/delay (keep reverb on Path B, dry+delay on A)
  - Dry signal bypass (Path A dry, Path B wet, recombine with Mixer)
  - Multi-amp setup (Amp + Cab separately vs Amp+Cab; Preamp for second amp)
  - Stereo widening (Dual Cab with independent pan L/R)
  - Song-section snapshots (Intro/Verse/Chorus, one snapshot each)
  - Tempo-synced effects (note divisions over fixed ms)
  - Expression pedal blend (assign Mix + another param to same pedal)
- Any "TIP:" callouts in the manual that relate to preset construction (not hardware setup)
- Any explicit "don't do this" warnings related to signal chain or DSP

---

### Stage 9 — Output Configurations
**Output:** Appended to `docs/manual/signal-chain.md` as a new `## Output Configurations` section
**Pages:** 6–12 (connectivity and hookup diagrams), 29 (Preamp vs. Amp note), any other references
  to 4CM, front-of-amp, or studio/direct hookup scattered through the manual
**Extract:**
- For each named output scenario: what blocks to use or avoid, and where Send/Return sits in the chain
  - **Direct to PA / audio interface** — full Amp+Cab (or Amp + Cab/IR) required; no real amp in the chain
  - **Front of amp (instrument input)** — skip all Amp and Cab blocks; HX Stomp acts as effects-only
  - **4-Cable Method (4CM)** — effects before the Send block hit the amp's preamp; the Send/Return
    block inserts the real amp preamp into the chain; effects after the Return block run in the amp's
    FX loop; Amp and Cab blocks are typically omitted
  - **Power-amp return (amp FX loop return / effects loop)** — use Preamp block (no power-amp stage,
    no cab); omit Cab/IR blocks if the real cab is being mic'd or the amp colours the sound
- One-sentence rule for each scenario: what to include, what to skip, where Send/Return goes if used
- Omit connector pinouts, cable diagrams, and physical port descriptions

---

## Invocation Template

When directing an agent to run a stage, use this prompt:

```
Read pages [X] to [Y] of `assets/manual_single.html`.
Pages are delimited by `<!-- Page N -->` HTML comments.
Extract the following and write to `docs/manual/<file>.md`:

[paste Stage N extract instructions]

Style rules:
- No introduction paragraph. Start with the first piece of content.
- Short tables for tabular data.
- One sentence per concept.
- Omit hardware setup, physical controls, MIDI CC tables, firmware update steps.
- Use **bold** for term names, plain text for definitions.
- Don't add headings not warranted by the content.
```

## Verification

After all stages are complete:
- `docs/manual/` should contain 8 `.md` files (stage 9 appends to `signal-chain.md`, no new file)
- Each file should be readable in isolation — no cross-file references required to understand it
- An agent with only `block-limits-dsp.md` + `effect-categories.md` should have enough info to
  determine whether a proposed preset is valid
- An agent with all 8 files should be able to construct a coherent, musically meaningful preset
  from a natural-language description
