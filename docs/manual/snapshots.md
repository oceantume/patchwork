**Snapshot** — one of three variations stored per preset, each recording the state of certain elements so the entire preset can shift character instantly.

## What Snapshots Store

| Element | Detail |
|---|---|
| **Effect Bypass** | The on/off state of every processing block |
| **Parameter Control** | Up to 64 parameter values per preset (assigned to the Snapshots controller) |
| **Pitch/Key values** | Keys in Harmony Delay blocks and intervals in Pitch blocks, set per snapshot |
| **Tempo** | Current system tempo, when Global Settings > MIDI/Tempo > Tempo Select is "Per Snapshot" |

## What Snapshots Cannot Do

Snapshots cannot change block models, change block positions within the signal chain, or directly control the Looper's record/play/stop state (the 1 Switch Looper bypass state is not stored or recalled via snapshot).

## 64-Parameter Limit

Each preset supports at most 64 parameters assigned to the Snapshots controller; parameters are enrolled by pressing-and-turning their knob in Edit view, which assigns the Snapshots controller and makes the value white.

## Snapshot Edits Global Setting

**Global Settings > Preferences > Snapshot Edits** controls what happens to unsaved snapshot edits when switching between snapshots.

| Value | Behavior |
|---|---|
| **Recall** (default) | Edits made in a snapshot are retained when leaving and returning to it — the snapshot appears as you last left it. |
| **Discard** | Edits are thrown away when leaving a snapshot — returning to it shows the state from the last save. |

When writing parameters from an agent, **Recall** means in-memory edits persist across snapshot switches within the same session; **Discard** means any written values are lost the moment a different snapshot is selected unless the preset is saved first.

## Copy, Swap, and Rename

Snapshots can be **copied** to another snapshot slot (touch-hold the source footswitch, then tap the destination), **swapped** between two slots (simultaneously touch-hold both footswitches), and **renamed** with a custom label and LED color from the Preset List > ACTION menu.
