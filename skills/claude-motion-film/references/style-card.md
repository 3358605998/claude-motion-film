# Style Card — Claude Motion

Exact values. Copy these; do not approximate them.

## Palette

```
BG        #141413   warm near-black (never #000000)
PANEL     #1F1F1D   PANEL2 #2A2926
CREAM     #F0EEE6   primary text / light-scene ground
GREY      #B0AEA5   secondary      DIM #686760  tertiary
ORANGE    #D97757   the only accent, <= 3% of any frame
HOT       #FFA880   cursor, glow core
GREEN     #7AC478   pass / success
RED       #EC5450   fail
BLUE      #6A9BCC   link
AMBER     #E8B25A   caution
Light scene: LBG #F0EEE6  CARD #FCFBF7  BORDER #DEDBD0  LGREEN #409654
```

Light is not an inversion of dark; it is a swap of paper. Card, border and ink all change.

## Type roles

| Role | Face | Used for | Tracking |
|---|---|---|---|
| CJK headline | Noto Sans CJK SC **Black** | the few lines that matter | 0 |
| Body | same family Bold/Medium/Regular | secondary | 0 |
| Machine vocabulary | Noto Sans **Mono** CJK SC | HUD, code, section numbers, timecode | **+0.22em** |
| Latin numerals / short words | **Poppins** Bold/Medium | "30%", "2026", "Bug" | slight |
| Brand word | **Lora Italic** 600 | only the Latin word inside the product name | 0 |

CJK + Latin mixing means **same size, same baseline, different face** — never scale the
Latin down, never italicise it, never break the line.

Wide tracking is the fingerprint: it says "instrument panel". Zero tracking says "human
voice". Alternating between them is what makes the frame feel designed.

## Type scale (px at 1080p) — span must be ≥ 30×

`560` giant single glyph · `250` brand serif · `150 / 140 / 132` display · `100 / 96 / 84`
manifesto · `72 / 68` subhead · `46 / 44 / 38 / 34` list · `40` code (mono, 20px advance) ·
`30 / 28` section number · `22` annotation · `20` HUD · `18` frame counter.

## Layout & HUD

- Side margins **76px**. Top bar baseline **y=71**. Frame counter **y=1030**.
  Progress bar **y=1052**, width 1768, 2px, accent.
- Persistent corners: `● <BRAND>` top-left (dot + wide-tracked small caps); `00:00:00`
  timecode top-right; `FRAME 0000 / 0900` bottom-left; `illustrative` bottom-right.
- Two-column split: one side carries the *demonstration* (panel / card / code, roughly
  (120,210)–(1080,810)), the other carries the *conclusion* (section number, display headline,
  three-item checklist).
- Section numbers read `01 / FIX A BUG` — mono, accent, wide tracking, a hairline rule under.
- **The HUD shares the same post-processing as the picture.** It shakes, it chromatically
  separates, it grains. A HUD that sits still looks like a watermark.
- Ink coverage ≤ 12%. Empty is the default state.

## Post-processing stack (four layers, all four required)

1. **Glow** — accumulate at 1/4 resolution, dual gaussian σ 2.2 and 7.0, weights 0.45 / 0.62.
2. **Vignette** — elliptical, clipped to [0.55, 1.0].
3. **Grain** — five pre-generated noise fields cycled, σ = 2.2.
4. **Shake + chromatic aberration** — shake is a transient only: 7–26px at 34Hz, gone in
   0.24s. Chroma is different: it is *texture*, and it should be **continuously present** at a
   low base (2.4px, relaxing to 1.2px under the final lockup so type stays crisp) with spikes to
   8–11px on impacts. Removing chroma entirely does not look cleaner, it looks like a flat
   render; leaving it at 8px constantly looks like a broken decoder. Base plus spike.

Drop any layer and the frame instantly reads as a slideshow render.

## Motion

**Zero hard cuts.** Allowed transitions, and only these six:

| Class | Method | Parameters |
|---|---|---|
| Motif morph | one radius variable interpolated: dot ↔ caret ↔ panel ↔ circle | 60×60 → 960×600, corner radius 30 |
| Iris | R = 36 + 2400·inout_cubic; **12px accent rim + 64-point halo** around the circumference | 0.5s |
| Particle reflow | minimum-displacement (Hungarian) assignment to glyph targets; per-particle delay 0–0.18s; vertical path bowed ±230px | 0.8s |
| Impact | ring 30→1540px + white flash + chroma + shake **simultaneously** | 0.2s |
| Light sweep | 12–16 horizontal streaks at 3500–6000px/s, 300–900px long, 2px wide | 0.4–0.5s |
| Typographic slam | scale 1.25–2.3 → 1 with vertical blur 26–70px → 0 | 0.24–0.30s |

**Easing, by observed frequency in the reference film:** smooth 34 · out_expo 22 ·
out_cubic 15 · inout_cubic 8 · out_back 4 · spring 3 · **out_elastic 0**.

out_expo is the signature: fast out, slow settle. Decisive, unhurried, never cute.

**Stagger** items in a group by 0.08–0.18s. Never all at once.

**Three required flourishes:** a slamming headline; ghost trails on the hero element
(8–26 historical positions, alpha ∝ k²); and accent punctuation — an orange full stop or
comma used as free emphasis.

## Swarm vocabulary (the thing that stops a film looking monotonous)

A film built only from bars, panels and type reads as a slide deck however well it is animated.
Add one continuous body of particles and let it change role. The full chain, in order:

1. **punctuation → solid → window** — one radius variable: the full stop grows into a filled
   disc, the disc flattens into a rounded rect, the rect becomes the 16:9 frame the film plays
   inside. Never a cut; always the same object.
2. **burst** — the object collapses to a point and explodes into ~900 dots, radial velocity
   decaying from >1800 px/s to a cruising <640 px/s within 0.3s.
3. **flow** — the swarm rides a travelling spine (an analytic undulating band) rather than a
   free-running force simulation. Free-running boids + speed clamping finds limit cycles and
   settles into an obvious **ring**; an analytic spine cannot. Give every particle its own
   flutter phase so the band has thickness and life.
4. **give it a roost slower than it can fly.** If the attractor moves faster than the swarm's
   speed cap, the swarm orbits the attractor forever and reads as a ring. This is the single
   most common failure of hand-rolled murmurations.
5. **reflow to glyphs** — greedy minimum-travel assignment, every path bowed by a
   perpendicular arc (`perp * amp * sin(πu)`), per-particle delay 0–0.30s. That arc is what
   makes it look gravity-driven instead of teleported.
6. **ink resolve** — let the real type fade in on top of the settled dots at the same
   coordinates, then dissolve the dots. Dots alone are too sparse to read a word; ink alone
   loses the payoff. The hand-off is the effect.

### Rendering mechanics that decide whether the swarm reads at all

These five decide it; get any one wrong and the formation is mush.

- **Density is the whole game.** Sample the glyph on a regular **4 px lattice** (one particle
  per cell), which for a full-width word is *thousands*, not hundreds. With 900 particles over
  a 140k-pixel glyph you get one dot per 150 px - the word cannot read no matter how you
  animate it. Budget roughly `glyph_ink_pixels / 15` particles.
- **Dot radius is about half the sampling step**, so neighbouring dots just touch and tile the
  cell: a ~4 px disc for a 4 px lattice. Bigger dots merge into a slab; smaller leave holes.
- **The trail is not optional.** Canvas implementations never clear - they fill with
  `rgba(bg, 0.18)` each frame, leaving a decaying smear that makes motion read as smooth.
  A pure-function-of-time renderer has no framebuffer, so reconstruct it from **4 time taps**
  (0, 22, 44, 70 ms) at decreasing weight. Without taps, particles teleport.
- **Tone-map the accumulation** (`a / (1 + k*a)`) before applying colour. Point accumulation
  clips in the dense interior and the formation instantly becomes a flat white slab with a
  dotted edge - the classic tell of an untonemapped particle field.
- **Mind the buffer's own scale when multiplying by a colour token.** A renderer whose
  `finish()` does `clip(0,1)*255` works in 0..1; multiplying by a 0..255 palette tuple
  saturates every particle to white. This one bug cost a full render cycle and looked exactly
  like 'too many particles'.

### The hand-off: a flash-cut swap, never a cross-fade

Any dissolve between the swarm and the type leaves a visible seam, because the dots and the
ink have different edges and the eye catches the moment they trade places. Do not blend.
**Cut, and hide the cut inside a white hit.**

1. **assemble** - the swarm reflows onto the glyph targets and settles (jitter decays so the
   edge hardens). Gate this on completion, not on the clock.
2. **bloom** - ramp particle gain to about 2.2x over ~0.22s so the dots are as bright as they
   will ever be right before the swap. The word reads as solid, not as grey dust.
3. **flash** - a full-frame warm-white hit with **no attack at all**: the first flash frame
   is already pure white (0 -> 1 in one frame), held for 2-3 frames, then an eased decay
   (tau ~75 ms). An attack ramp ruins it twice over: the audience sees the white rising
   while particles are still in flight, so the merge never visibly completes before the
   swap. Only the decay may have a transition.

   Verify numerically rather than by eye - "all particles at their target" is measurable:
   `max(norm(positions(t) - targets)) < 2 px` and zero particles moving. If that is not true
   on the frame before the flash, shorten the per-particle delay; do not soften the flash.

   **Pin the peak to a frame index and prove it.** Two cheap measurements settle the whole
   question, and both beat looking at it:

   - completion: per frame, `max(||positions(t) - targets||)` and the count of particles
     still moving. The first frame with residual < 2 px and zero moving is the completion frame.
   - the flash itself: decode the delivered file at 160x90 greyscale and average each frame.
     The plateau shows up as identical peak values on consecutive frames; read the jump size
     between the last formation frame and the first peak frame - a real flash cut is a jump of
     about +200 in one frame. If you see it rising across 2-3 frames, an attack ramp has crept
     back into the code.

   State the result as a timecode in the delivery notes (`12s25f`, not "about 12.8"), so the
   exact frame can be checked later. The picture flash and the audio hit may sit one frame
   apart; that is inside the +/-60 ms sync budget and is not worth another pass.
4. **swap on the peak frame** - particles hard OFF, ground truth type hard ON, same frame.
   No fade, no blur-in, no slide, no stagger: **the real type must have zero entrance
   animation**, because any motion on arrival is exactly what the eye reads as a seam.
5. **decay** - the white falls away over ~0.25s and the finished word is simply there.

Pick the peak on an integer frame boundary (at 30 fps, 331/30 s) so the white frame and the
swap frame are the same frame. If they are half a frame apart the seam comes back.

**Easing decides whether it reads as gravity or as a slide.** Particle convergence is almost
always written as an ease-**OUT** (fast start, slow settle), which makes the swarm look like
it is gliding to a stop - the classic 'hard move'. Use an accelerating ease-**IN** instead so
the swarm hangs, gets pulled, and slams:

`cubic-bezier(0.71, 0.00, 0.99, 0.52)` - at u=0.5 only 11% of the distance is covered, at
u=0.90 it is 54%, and the last 10% of time covers 46% of the path. Implement it as a real
cubic-bezier (bisect x to recover t, then evaluate y), not as `u**n`: a plain power curve
does not have the late cliff and reads soft.

Then put the white flash **on the arrival frame**, not on a beat after it: the impact and the
swap are the same event. With per-particle delay d and duration D, arrival is `t_agg + d_max +
D`; set the flash peak one frame later.

Keep the arc shallow (about 40 px perpendicular) once the curve is accelerating - a big bow
fights the gravity read.

Two constants decide whether the dots read at all, and both must be measured, not guessed:
total gain (aim for the 90th-percentile dot at about 0.7 of full scale) and dot radius. Note
that a box-approximated gaussian quantises its radius: sigma 1.15 and 1.30 can produce the
identical image because both round to the same box radius. Check which radius you actually
got before concluding the dots are 'too small' - it is usually brightness.


## Rhythm

- 120 BPM: beat 0.5s, bar 2s, 30s = 15 bars.
- Section lengths **4 / 4 / 4 / 6 / 4 / 8** seconds — lift, demo, demo, burst, data, rest.
- Roughly 26 composition states in 30s, averaging 1.15s each. Fewer than 20 feels sluggish;
  more than 40 feels shredded.
- **Three suspensions minimum** — the music must never stop. Duck to about −18 dB, close the
  low-pass from 8k to 400 Hz, hold a sub drone, and feed a reverse-reverb swell into the next
  hit. There is no 0.07s vacuum and no vacuum before the lockup: a hard gate reads as a broken
  file. End on a 200–300 ms cosine release, never a truncation.
- First two seconds are an information vacuum — almost nothing on screen but the motif.

## Reading budget

Comfort is 8–10 characters/second; this style runs at **2.6–4.6** for demonstration copy and
**1.0–1.6** for the closing lockup. No line may exceed 6 chars/sec. The opening hook may be
fast, but keep it to six characters or fewer.

## Audio

- Fully synthesized — no samples, no library music. Kick, snare, clap, hat, bass, pluck,
  marimba, FM bell, pad, impact, sweep, chirp, keyclick, blip, buzz, thump, skitter, chime.
- Minor key, i–VI–III–VII; melody from the pentatonic. **The single bright major colour is
  reserved for the success/reply moment.**
- Master to **−15 LUFS with true peak ≤ −1 dBTP**. Measure with `ffmpeg ebur128` on a temp
  wav, back out the gain, then soft-clip with tanh (knee 0.62, ceiling 0.84).
- **Master for the delivered codec, not for the wav.** AAC overshoots: a wav at −1.4 dBTP
  measured −0.7 dBTP after encoding, which fails the −1.0 gate. Render the mp4, measure the
  mp4, and if it fails re-encode with about 0.45 dB of headroom (`-af volume=-0.45dB`). Lands
  around −15.4 LUFS / −1.3 dBTP, which passes both gates.
- **ffmpeg trap:** `volume=-0.45` with no unit is a LINEAR factor (≈ −10.5 dB), not dB.
  Write `volume=-0.45dB`. This silently wrecked a gain sweep that looked like a measurement bug.
- Every sound effect lands within ±60ms of its visual. The cheap way to guarantee this is to
  have picture and audio read the same timeline module.

## Copy voice

- First person. Short sentences ending in periods. No sentence longer than 18 characters.
- One request line opens the film and the same request line closes it. Ring composition is
  the memory hook.
- Humour by **reduction**, not by excitement: draw the complex thing small and silly.
- Self-reference instead of self-praise. "Every frame you are watching is code I wrote"
  converts a brag into something the viewer can verify.
- Daring brevity: a two-character line is a legitimate scene.
- Numbers carry a source or they do not appear.

## Forbidden

```
pure #000000
a second accent colour, or accent as background fill
three or more simultaneous visual elements
any hard cut, fade-to-black, or dissolve that hides a cut
elastic / jelly / bounce easing on meaningful motion
effects stacked for their own sake
paragraphs of text (two lines is already a paragraph)
endless paginated slides
unsourced benchmarks, prices, or competitor comparisons
continuous sound with no silence
"strongest / leading / revolutionary" without proof
image or video generation models passing as design
```

## Ten-line minimum checklist

```
1  one motif, all the way to the last frame
2  #141413 ground, #F0EEE6 text, #D97757 the only colour
3  type span >= 30x, ink <= 12%
4  four-corner HUD + bottom progress bar, sharing post-processing
5  zero hard cuts, only the six transition classes
6  out_expo first, never elastic, stagger 0.08-0.18s
7  120 BPM, boundaries on bar lines
8  at least one iris light/dark inversion centred on a meaningful point
9  at least three real silences, longest >= 0.4s
10 -15 LUFS AND TP <= -1 dBTP, sound within +/-60ms, data labelled illustrative
```
