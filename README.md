# claude-motion-film

**A motion-design skill for coding agents.** Give it a topic, get a short film back —
warm near-black, one terracotta accent, a single motif doing every job, no cuts,
a 120 BPM cue sheet and a fully synthesized score.

`v0.1.0 (beta)` · 1920×1080 · 30 fps · built by agents, rendered by code.

![the swap](media/stills/formation.png)

---

## What this actually is

Not a video template. It is a **set of constraints** — a style card, a director's brief, a
pipeline and an acceptance gate — that makes an agent produce portfolio-grade motion design
instead of a slide deck.

The rule that does most of the work: **one motif, reused as cursor, punctuation, icon,
transition and data marker**, and **zero hard cuts** — every boundary is the same object
changing state.

```
a dot  →  a full stop  →  a filled disc  →  a 16:9 window  →  900 bars  →  a hairline
       →  a point  →  9,000 particles  →  a flowing ribbon  →  the word, in dots
       →  [white flash on the frame the last particle lands]  →  the word, in ink
```

## Install (for another agent)

A skill is just a folder of instructions. Put it where your agent looks for skills.

**DeepSeek Harness / Claude-style skill directory**
```bash
git clone https://github.com/<you>/claude-motion-film.git
cp -r claude-motion-film/skills/claude-motion-film ~/.dsh/skills/
```
Windows:
```powershell
git clone https://github.com/<you>/claude-motion-film.git
Copy-Item -Recurse claude-motion-film\skills\claude-motion-film "$env:USERPROFILE\.dsh\skills\"
```
Or just run `./install.sh` / `.\install.ps1`.

**Any other agent with a skill/plugin mechanism** — copy `skills/claude-motion-film/`
into its skills folder. The frontmatter is standard `name` / `description`.

**An agent with no skill mechanism at all** — paste this into the conversation:
```
Read skills/claude-motion-film/SKILL.md and skills/claude-motion-film/references/style-card.md
from <repo path>, then follow them exactly.
```

After installing, the trigger is one sentence:

> 用 claude-motion-film 这支 skill 做一支 30 秒的 XX 宣传片

## Using it

| You want | Load |
|---|---|
| A film in this style | `claude-motion-film` (routes to everything) |
| Exact values — palette, type scale, easing, transitions | `references/style-card.md` |
| A fill-in director's brief for a specific topic | `references/brief-template.md` |

Ready-to-paste prompts live in `docs/`:
- `docs/01-审美与工作方式总结.md` — the aesthetic and working method, dissected
- `docs/02-复现提示词.md` — the full director's brief (edit the header, reuse)
- `docs/03-通用风格提示词.md` — the style layer alone; append it to any video brief

## The demo film

`media/claude-motion-film.mp4` — **16.000 s / 480 frames**, generated entirely from
`film/` by this repo's own pipeline, as a test of the skill against itself.

```
h264 High · 1920x1080 · 30/1 fps · yuv420p · 480 frames · 16.000000 s
aac 48 kHz stereo · I = -15.4 LUFS · True peak = -1.3 dBFS
100 ms windows: 160, minimum -33.58 dBFS, none below -45 (no dropouts)
decoded with 0 errors
```

Rebuild it:
```bash
cd film
python -c "import numpy, PIL"        # needs numpy + Pillow only; no cv2, no scipy
python particles.py                  # precompute the flow field + glyph targets (~0.2 s)
python render.py all                 # 480 frames, ~70 s on 12 cores
ffmpeg -i out/video_silent.mp4 -i out/soundtrack.wav \
       -c:v copy -af "volume=-0.45dB" -c:a aac -b:a 320k -ar 48000 -ac 2 \
       -shortest -movflags +faststart out/film.mp4
```
The `-0.45dB` is not decorative — see "what the gates catch" below.

## Still frames

| | |
|---|---|
| ![formation](media/stills/formation.png) | ![lockup](media/stills/lockup.png) |
| the swarm, fully assembled, one frame before the swap | the lockup, after the flash |
| ![swap](media/stills/swap_01.png) | ![impact](media/stills/impact_01.png) |
| the swap, frame by frame | the impact beat |

## What the gates catch

The skill's acceptance list is why the film looks the way it does. Three examples of
things it caught **only** because they were measured, not looked at:

- **AAC overshoot.** The wav measured −1.40 dBTP; the encoded mp4 measured −0.7 dBTP,
  failing the −1.0 gate. Master for the delivered codec, not the wav.
- **A flash with an attack ramp.** The white was rising over 3 frames while particles were
  still in flight, so the merge never visibly completed. A real flash cut is a **+200 jump
  in one frame** — measurable by averaging each frame at 160×90.
- **A filter that ignored the argument.** `volume=-0.45` without a unit is a linear
  factor (≈ −10.5 dB), not dB. It produced a gain sweep that looked like a broken meter.

## Repo layout

```
skills/claude-motion-film/     the skill itself — SKILL.md + references/
docs/                          the aesthetic write-up and the two prompts
film/                          full source of the 16 s demo (9 files, pure numpy+PIL)
media/                         the rendered film and stills
```

`film/timeline.py` is the single source of truth: picture and audio both import it,
so sync is guaranteed by construction rather than checked afterwards.

## Status — v0.1.0 beta

Working and verified: the style system, the particle pipeline, the flash-cut swap,
the audio mastering chain, the acceptance gates.

Known gaps, honestly:
- The audio was never listened to — every claim about it is a measurement.
- Fonts are hard-coded to Windows paths. `film/timeline.py` `FONTS` is the one place to change.
- No mobile/small-screen adaptation of the type scale.
- The demo's type span is 27.8× against a 30× target.
- `audio.py` assumes numpy only; it has no fallback for a missing output device.

Issues and forks welcome. If you build something with it, open an issue with a link —
the whole point is that the style transfers.

## License

MIT — see `LICENSE`.
