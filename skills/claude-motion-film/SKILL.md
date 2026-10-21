---
name: claude-motion-film
description: Produce a short, code-rendered motion-design video in the Claude/Anthropic visual language - warm near-black and paper cream, a single terracotta accent, one motif doing every job, cutless transitions, a 120 BPM cue sheet, and a fully synthesized score. Load before planning, scripting, or rendering any such video, or when asked to make a promo/explainer that "looks like Claude made it".
---

# Claude Motion Film

A production skill for 15–60 second code-rendered films with a specific, reproducible
aesthetic: **restraint as spectacle.** One motif, one accent colour, no cuts, deliberate silence.

The whole point is grammar over effects. Build a tiny visual language, then tell the story
with it. If you find yourself adding a second effect to make a moment feel bigger, you have
already lost.

## When this applies

- A promo, self-introduction, product explainer, or manifesto film rendered by code.
- Anything the user wants to look like an Anthropic / Claude motion piece.
- Any short film where the brief says "stylish, rhythmic, smooth transitions, portfolio-grade".

Not for: long-form video, talking-head editing, or anything that needs stock footage or
image/video generation models. This style is drawn, not sampled.

## Non-negotiables

1. **Pick one motif before writing code.** It must be reusable as cursor, punctuation, icon,
   transition centre, and data marker — and it must survive without any numbers.
2. **Warm near-black `#141413`, never `#000000`.** Paper cream `#F0EEE6`. Exactly one
   accent: `#D97757`, never covering more than 3% of a frame.
3. **Zero hard cuts.** Every boundary is carried by the motif moving, morphing, or the same
   element changing state. The audience may hear a cut; they must never see one.
4. **Whitespace ≥ 88%.** Ink coverage never exceeds 12% of the frame.
5. **Type scale spans ≥ 30×.** Hierarchy comes from orders of magnitude, not from bold.
6. **Write the cue sheet before the first frame.** Video and audio both import the same
   timeline module, so sync is guaranteed by construction rather than checked afterwards.
7. **120 BPM.** One beat 0.5s, one bar 2s. Section boundaries land on bar lines.
8. **At least three *suspensions*, never a silence.** The score ducks to about −18 dB and
   filters down; it never gates to zero. Any 100 ms window below −45 dBFS is a dropout the
   audience hears as broken music, not as a beat of rest.
9. **Ease with out_expo and smooth. Never elastic.** A confident brand does not wobble.
10. **Never invent numbers.** Anything unverified is omitted; anything illustrative is
    labelled *illustrative* inside the frame, not only in the README.

## Pipeline

**Step 0 — Verify (cap this at ~3% of your time).** Search primary sources. Write the result
as one closable sentence: `Verified: <facts> / source <domain> / <date>`. Turn every
"forbidden claim" into a final `grep` with zero hits as evidence.

**Step 1 — Probe the environment in one command.** Cores, RAM, GPU, canvas/skia/chromium/
moviepy, available CJK fonts, ffmpeg, disk. Let the probe choose the stack, not preference.
On 1 core / 3 GB, a browser renderer is the wrong answer.

**Step 2 — Choose the motif.** Score at least three candidates against reuse, number-
independence, being inherent to the name, morphability, and silence-ability. Once chosen it
never changes; every asset derives from it.

**Step 3 — Write `timeline.py`.** A flat table of cue constants (scalar / range / list forms).
Nothing else exists yet. Then build scenes.

**Step 4 — Build the toolbox before the scenes.** Easing, text, glow, primitives, grid,
post-processing. Each scene is then a shallow composition of toolbox calls.

**Step 5 — Preview with contact sheets.** One sheet of 20–30 cells with burned-in timecodes
beats ten single-frame renders.

**Step 6 — Compose audio.** Fully synthesized, minor key, measured loudness, silence gates
written as literal zeroes.

**Step 7 — Render in segments through a pipe to ffmpeg.** Measure single-frame cost on a
handful of samples before estimating total time. Detach background jobs from the session.

**Step 8 — QA, then fix at source and re-render.** Never patch an encoded output.

## Verification gates

Never declare the film finished without all four passing:

| Gate | Threshold |
|---|---|
| Spec | exact frame count, duration, resolution, fps, 48kHz stereo |
| Sync | 8 sampled hit points, each within ±2 frames of the audio transient |
| Loudness | −15 LUFS **and** true peak ≤ −1 dBTP — both, not either |
| Continuity | slide a 100 ms window across the whole mix: **no window below −45 dBFS** |
| Cutlessness | every frame scored >0.90 must be a flash bloom, verified by eye, not assumed |
| Legibility | **full-resolution** frame crops, every text element inspected |

Additionally: 0 hard cuts, ink ≤ 12%, largest-to-smallest type ≥ 30×, no copy line above
6 characters per second, opening and closing mirror each other, and the film reads with the
sound off.

Ship an honest "what I did not do" page. It belongs in the deliverable.

## Anti-patterns

- A second accent colour, or accent used as a background fill.
- Elastic/ease-out-back bounces on meaningful motion.
- Fade-to-black between sections, or any dissolve that hides a cut.
- Stacking three or more visual elements at once.
- Paragraphs on screen. Two lines is already a paragraph.
- Particle effects for their own sake.
- Ending on a wall of logos and URLs instead of one memorable line.
- Loudness normalised but true peak left over −1 dBTP.
- Claiming "全部通过" while a self-check script silently returns early.

## References

- `references/style-card.md` — the complete token set: palette, type roles, type scale,
  layout/HUD, post-processing layers, easing statistics, transition taxonomy, audio spec,
  copy voice, and the forbidden list. Load it when you need exact values.
- `references/brief-template.md` — a fill-in director's brief that carries the constraints
  and the final self-check list. Load it when the user hands you a topic rather than a spec.

When a shot looks flat, the fix is almost always more empty space and fewer elements —
not another effect.
