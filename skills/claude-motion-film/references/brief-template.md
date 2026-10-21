# Director's Brief Template

Fill the block at the top, then hand the rest to the executing agent verbatim.
This is the generic form of the brief that produced the reference film.

## Fill in

- **Subject**: <product / concept / self-introduction>
- **Duration**: 30.000s / 900 frames / 30fps / 1920×1080
- **Language**: <copy language; score has no dialogue>
- **Deliverables**: playable MP4 + full source + one-page build notes

## The brief

You are simultaneously the creative director, motion designer, composer, and the engineer
who writes it. Your output is a finished 30-second film worthy of a top motion designer's
portfolio — not a treatment, not a storyboard, not a still.

### 0. Three things first

**0.1 Verify facts (≤ 3% of your time).** Search primary sources only. Write the result as
one closable sentence: `Verified: <facts> / source <domain> / <date>`. Every unverifiable
number — benchmarks, prices, competitor comparisons — is omitted. Turn the forbidden-claims
list into a final `grep` and cite zero hits as evidence. Anything illustrative is marked
inside the frame.

**0.2 Probe the environment in a single command.** Cores, RAM, GPU, canvas/skia/chromium/
moviepy, CJK fonts, ffmpeg, disk. The probe chooses the stack.

**0.3 Choose the motif — this decides quality, so do not rush it.** Draft at least three
candidates and score them:

| Test | Question |
|---|---|
| Reuse | can one primitive serve as cursor, punctuation, icon, transition centre, and data marker? |
| Number-independence | with all comparisons forbidden, can it still prove competence? |
| Inherence | is it already inside the subject's name, so no separate mark is needed? |
| Morphability | can it continuously become five or more shapes? |
| Silence-ability | can it make a 0.4s silence read as punctuation rather than as a fault? |

All five pass = the motif is real. It never changes afterwards.

### 1. Creative constraints

1. First person. Identity inside two seconds; capability seen, not claimed, inside eight.
2. Show **2–3 capabilities** as concrete task → concrete result. No slogans.
3. The opening must be an information vacuum followed by a single burst.
4. The ending must rhyme with the opening — same line, same element.
5. Forbidden: paginated slides, paragraphs, unrelated effects, "we are the best".
6. Humour is allowed if it comes from reduction, not from excitement.

### 2. Visual specification

Use the exact tokens, type scale, layout, HUD furniture, and four-layer post-processing in
`references/style-card.md`. No substitutions.

### 3. Motion

Zero hard cuts; only the six permitted transition classes; out_expo and smooth;
never elastic; stagger 0.08–0.18s. Include all three required flourishes.

### 4. Rhythm

120 BPM, boundaries on bar lines, sections 4/4/4/6/4/8 seconds, at least three real
silences, reading speed under 6 chars/sec everywhere.

### 5. Audio

Fully synthesized, minor i–VI–III–VII, −15 LUFS **and** true peak ≤ −1 dBTP, every effect
within ±60ms of its visual, silences written as literal zeroes.

### 6. Architecture

**Write `timeline.py` first, then the first shot.** One flat cue table; picture and audio
both import it, so desync becomes impossible rather than detectable.

Every frame must be a pure function of time — no cross-frame state. Trails are computed from
`positions(t - 0.022)`; typing is a count of timestamps; flicker is a modulo; randomness is a
fixed seed or a continuous function. Any frame can then be pulled out and audited alone.

```
timeline.py   absolute cue sheet (single source of truth)
gfx.py        easing, text, glow, primitives, grid, post
common.py     HUD, gradients, iris, dot, streak, slam
scenes_a.py   opening + demo 1
scenes_b.py   demo 2
scenes_c.py   burst + data + lockup
audio.py      synthesis and mastering
render.py     segmented render, piped to ffmpeg (supports `seg a b`)
qa.py         export checks
build.sh      one-command build
```

No horizontal dependencies between scene files.

Smoke-test each module the moment it is written. Preview with contact sheets that have
timecodes burned in. Measure single-frame cost on a few samples before estimating the full
render, and detach long jobs from the session.

### 7. Delivery and acceptance

Check four things on export: **spec** (exact frames, duration, fps, 48kHz stereo);
**sync** (8 sampled hits within ±2 frames); **loudness** (−15 LUFS **and** true peak
≤ −1 dBTP); **legibility** (full-resolution crops, never thumbnails).

When something is wrong, fix the source and re-render. Never patch the encoded file.

Ship the MP4, the full source with a one-command build, a one-page README (motif in one
sentence, cue table, verified-facts list, stack, rebuild steps), and **a page listing what
you did not do**. Honesty is part of the deliverable.

### 8. Final self-check

```
[ ] facts sourced; forbidden-claim grep returns 0
[ ] one motif, present in the final frame
[ ] at least one light/dark inversion, via iris, not a cut
[ ] zero hard cuts
[ ] ink <= 12%
[ ] type span >= 30x
[ ] accent <= 3% of any frame
[ ] at least three silences >= 0.07s
[ ] all section boundaries on 2s bar lines
[ ] no line above 6 chars/sec
[ ] 8 sampled hits within +/-2 frames
[ ] -15 LUFS and TP <= -1 dBTP
[ ] full-resolution legibility pass
[ ] ending rhymes with the opening
[ ] readable with sound off
[ ] "what I did not do" page present
```

Now begin. Write `timeline.py` first.
