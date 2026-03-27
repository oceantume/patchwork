## Serial Path

A serial path is a single stereo signal flow where blocks are processed one after another (e.g., Pitch → Amp → IR → Mod → Delay → Reverb). Suitable for most guitar tones.

## Parallel Path

A parallel path splits the signal into two independent stereo paths (A and B), processes them separately, and merges them back together via the Mixer block. Creating a parallel path adds a Split block (at the split point) and a Mixer block (at the merge point), both visible only when selected.

Advantages of parallel routing:
- Delay and reverb on separate paths won't interact (cleaner, more defined notes vs. serial where delay echoes get reverb or reverb tails get echoed)
- Blocks without Mix/Blend controls can be blended with the dry signal by placing them on one path while the other carries the dry signal — especially effective for clean/distorted bass blending
- A single Amp block can feed two parallel Single Cab or IR blocks (one on each path)
- Each path can be panned independently via the Mixer block for stereo widening (e.g., different delay/reverb models panned hard left and right)

**TIP:** Both paths A and B are stereo, so mono or stereo blocks can be used on either path.

To remove path B, move all blocks from path B (lower) back to path A (upper).

## Path B Independent Output

The Mixer block can be moved to path B, creating a separate Output block. In this configuration path A is sent from Main L/R and path B is sent from Send L/R, allowing completely independent output routing.

## Split Block Types

A Split block appears automatically when a parallel path is created. Four types are available:

| Type | Key Parameters | Behavior |
|------|---------------|----------|
| **Y** | Balnce A, Balnce B | Sends the full signal to both paths; balance controls adjust stereo pan for each path. |
| **A/B** | RoutTo | Controls how much signal goes to Path A vs. Path B; press the knob for an even split. |
| **Crossover** | Freq, Revrse | Sends signal above the frequency to Path A and below to Path B (Revrse swaps this). |
| **Dynamic** | Threshold, Attack, Decay, Reverse | Routes signal below the threshold to Path A and above to Path B; Attack/Decay control transition speed. |

A Split block can be bypassed; when bypassed it sends both left and right signals to both paths equally regardless of type.

**TIP:** With Split > Y moved all the way left, setting BalnceA to L100 and BalnceB to R100 lets you process L/MONO and RIGHT inputs independently. Combined with routing the Mixer to Path B (Send L/R), two instruments can be processed simultaneously with independent I/O.

## Mixer Block Parameters

| Parameter | Description |
|-----------|-------------|
| **A Level** | Output level of Path A (upper). |
| **A Pan** | Left/right stereo balance of Path A. |
| **B Level** | Output level of Path B (lower). |
| **B Pan** | Left/right stereo balance of Path B. |
| **B Polari** | Inverts polarity of Path B. Typically set to "Normal." |
| **Level** | Overall output level of the Mixer block. |

## Block Order

The order of blocks in the signal chain matters: delay → reverb applies reverb to the delay's echoes, while reverb → delay adds distinct echoes to the reverb tail. On a parallel path, effects on separate paths don't affect one another.

## Stereo Imaging

The signal path is stereo, carrying two channels of audio. Whenever a **mono block** is inserted, both channels are combined into mono from that point forward. Stereo blocks display a stereo icon after the model name.

Most effects have both mono and stereo versions. The stereo version uses roughly **2× the DSP** of the mono version.

Legacy effects stereo behavior:
- Legacy Distortion, Dynamics & Pitch/Synth — mono
- Legacy Modulation & Delay — varies (mono, stereo, or mono-in/stereo-out); adjusting Mix can narrow the stereo image
- Legacy Filter and Reverb — stereo

**TIP:** Even with a mono playback system, stereo effects (especially reverbs) can still sound "fuller" than their mono counterparts.
