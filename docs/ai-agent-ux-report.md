# AI Agent UX Report — Preset Creation Session

Observations from a session where an AI agent built a preset exclusively using the `hx` CLI.
The agent created "Purple Thunder" (a 6-block British hard rock preset with 3 snapshots)
using `hx preset new/add/set/show/validate` and `hx model browse/search/inspect`.

## Issues Found

### 1. Model browse categories are wrong (high priority)

The category mapping in `hx model browse <category>` is shifted. Browsing `Amp` returns Wah
models, `Dist` returns Amp models, `Verb` returns Filter models, and so on. The command is
unusable for discovery. The agent had to abandon it and fall back to `hx model search` for
all model lookups.

### 2. No per-snapshot parameter values (high priority)

The CLI can set which snapshots a block is *active* in (via `--snapshots` on `preset add`),
but there is no way to set different parameter values per snapshot. This is a core HX Stomp
feature — snapshots are specifically designed to store per-snapshot parameter states. The
agent wanted to set different amp Drive values for Clean/Crunch/Lead snapshots and could not.

Proposed addition:

```
hx preset set <file> <block_key> <param> <value> --snapshot <index>
```

### 3. `preset show` does not display parameter values

After building the chain there is no way to review current parameter values without reading
raw `.hlx` JSON. The agent cannot verify its own work. A `--verbose` flag listing current
param values per block would close the loop.

### 4. `preset validate` does not show DSP budget

The command reports `Preset is valid.` or an error, but gives no usage figures. Showing the
actual DSP load (e.g. `DSP: 54.8 / 100`) would let the agent make informed tradeoffs —
knowing whether there is headroom to switch a mono block to stereo, or whether a heavier amp
model will exceed the budget.

### 5. Snapshot names cannot be set via CLI

The HX Stomp supports custom snapshot labels ("Clean", "Crunch", "Lead"). The agent thinks in
those terms naturally, but there is no CLI command to set them. Presets end up with generic
`SNAPSHOT 1/2/3` labels. Proposed addition:

```
hx preset snapshot rename <file> <index> <name>
```

### 6. `model search` omits DSP load

Search results show name, ID, and category but not the DSP load cost. Every candidate model
required a separate `hx model inspect` call to check whether it fit the budget. A `Load`
column in search output would reduce round-trips significantly.

## Summary

| Issue | Priority |
|-------|----------|
| Browse category mapping broken | High |
| No per-snapshot parameter values | High |
| `preset show` hides parameter values | Medium |
| `preset validate` shows no DSP usage | Medium |
| No snapshot renaming command | Low |
| `model search` missing load column | Low |
