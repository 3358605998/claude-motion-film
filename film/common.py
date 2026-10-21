# -*- coding: utf-8 -*-
"""common.py - the instrument panel and the shared screen furniture.

HUD / dot / line / streak / iris / slam / check.  Everything here is drawn BEFORE
post, so the HUD shakes, separates and grains exactly like the picture.
"""
from __future__ import annotations
import math
import numpy as np
import timeline as TL
import gfx
from gfx import (W, H, CREAM, GREY, DIM, ORANGE, HOT, WHITE, BG, mix,
                 clamp01, lerp, smooth, out_expo, in_expo, inout_cubic, out_cubic)

MARGIN = 76.0
TOP_BASE = 71.0
BOT_BASE = 1030.0
PROG_Y = 1052.0
PROG_X0, PROG_X1 = 76.0, 1844.0

LOG = []

def check(name, ok, detail=""):
    LOG.append((name, bool(ok), detail))
    print(("PASS  " if ok else "FAIL  ") + name + ("  | " + str(detail) if detail else ""))
    return bool(ok)

# ------------------------------------------------------------------ text
def text_width(s, key, size, track=0.0, kern=False):
    m, ox, oy, b = gfx.text_ink(s, key, int(round(size)), int(round(track * 100)), kern)
    return m.shape[1]

def place(img, s, key, size, x, base, color, alpha=1.0, track=0.0,
          align="left", kern=False, clip=None):
    m, ox, oy, _ = gfx.text_ink(s, key, int(round(size)), int(round(track * 100)), kern)
    w = m.shape[1]
    if align == "center":
        x = x - w * 0.5
    elif align == "right":
        x = x - w
    gfx.blit(img, m, x + ox, base + oy, color, alpha, clip)
    return w

def column_ramp(bounds, wmask, t, t_in, stag, dur):
    """per-character alpha ramp in mask-column space."""
    cols = np.arange(wmask, dtype=np.float32) + 0.5
    out = np.zeros(wmask, np.float32)
    n = len(bounds) - 1
    for i in range(n):
        a = bounds[i]; b = bounds[i + 1]
        r = out_expo((t - (t_in + i * stag)) / dur)
        if r <= 0.0:
            continue
        lo = int(max(0, math.floor(a))); hi = int(min(wmask, math.ceil(b)))
        if hi > lo:
            out[lo:hi] = np.maximum(out[lo:hi], r)
    return out

def copy_line(img, s, key, size, cx, base, t, t_in, t_out,
              track=0.0, stag=0.09, rev=0.26, slam=1.16, blur0=26.0,
              color=None, alpha=1.0, exit_dur=0.13, accent_last=False,
              clip=None, align="center", dy_in=16.0):
    """one copy line: staggered per-character reveal + typographic slam + soft exit."""
    if t < t_in - 0.02 or t > t_out + 0.02:
        return 0.0
    color = CREAM if color is None else color
    m, ox, oy, bounds = gfx.text_ink(s, key, int(round(size)), int(round(track * 100)), False)
    w0 = m.shape[1]
    g = out_expo((t - t_in) / 0.30)
    sc = 1.0 + (slam - 1.0) * (1.0 - g)
    vb = blur0 * (1.0 - g)
    uo = clamp01((t - (t_out - exit_dur)) / max(1e-4, exit_dur))
    a = alpha * g
    a *= (1.0 - smooth(uo))
    vb += 16.0 * smooth(uo)
    yoff = dy_in * (1.0 - g) - 12.0 * smooth(uo)
    if vb > 0.6:
        m = gfx.vblur(m, vb)
    if abs(sc - 1.0) > 0.004:
        m = gfx.scale_mask(m, sc)
    w = m.shape[1]
    ramp = column_ramp(bounds, w0, t, t_in, stag, rev)
    if uo > 0.001:
        ramp = ramp * (1.0 - smooth(uo))
    x = cx - w * 0.5 if align == "center" else (cx - w if align == "right" else cx)
    if accent_last:
        cut = bounds[-2] if len(bounds) > 1 else w
        body = m.copy(); body[:, int(cut):] = 0.0
        tail = m.copy(); tail[:, :int(cut)] = 0.0
        gfx.blit_cols(img, body, x + ox, base + oy + yoff, color, ramp * a, clip)
        gfx.blit_cols(img, tail, x + ox, base + oy + yoff, ORANGE, ramp * a, clip)
    else:
        gfx.blit_cols(img, m, x + ox, base + oy + yoff, color, ramp * a, clip)
    return w

# ------------------------------------------------------------------ primitives
def hairline(img, x0, x1, y, thick, color, alpha=1.0, clip=None):
    gfx.rect_add(img, x0, x1, y - thick * 0.5, y + thick * 0.5, color, alpha, clip)

def vbar(img, cx, cy, w, h, color, alpha=1.0, clip=None):
    gfx.rect_add(img, cx - w * 0.5, cx + w * 0.5, cy - h * 0.5, cy + h * 0.5, color, alpha, clip)

def dot(img, cx, cy, r, color, alpha=1.0, clip=None):
    gfx.dot_add(img, cx, cy, r, color, alpha, clip)

def ring(img, cx, cy, R, thick, color, alpha=1.0, clip=None):
    gfx.ring_add(img, cx, cy, R, thick, color, alpha, clip)

def impact_ring(img, t, t0, color=None, r0=30.0, r1=1540.0, dur=0.42,
                thick=2.0, alpha=0.9, cx=960.0, cy=486.0):
    u = (t - t0) / dur
    if u < 0.0 or u > 1.0:
        return 0.0
    R = r0 + (r1 - r0) * inout_cubic(u)
    ring(img, cx, cy, R, thick * (1.0 + 0.9 * u), CREAM if color is None else color,
         alpha * (1.0 - u) ** 1.4)

def light_sweep(img, t, t0, dur=0.46, x0=-300.0, x1=2220.0, y0=120.0, y1=960.0,
                n=14, seed=7, gain=0.5, color=None, thick=2.0):
    """12-16 horizontal streaks crossing the frame; the third required flourish."""
    if t < t0 or t > t0 + dur:
        return
    color = WHITE if color is None else color
    rs = np.random.RandomState(seed)
    for k in range(n):
        sp = 0.55 + 1.1 * ((k * 0.37 + seed * 0.13) % 1.0)
        u = (t - t0) / dur
        prog = clamp01(u * sp + (k / max(1, n)) * 0.55)
        x = lerp(x0, x1, prog)
        y = lerp(y0, y1, ((k * 0.618 + seed * 0.21) % 1.0))
        L = 300.0 + 600.0 * ((k * 0.29 + 0.17) % 1.0)
        a = gain * math.sin(math.pi * clamp01(u)) ** 0.8 * (0.45 + 0.55 * ((k * 0.71) % 1.0))
        gfx.rect_add(img, x, x + L, y - thick * 0.5, y + thick * 0.5, color, a)
        gfx.rect_add(img, x + L * 0.72, x + L, y - thick * 1.6, y + thick * 1.6, color, a * 0.35)

def ghost_bar(img, cx, cy, w, h, color, t, energy, n=14, dt=0.011):
    """8-26 historical positions of the hero element, alpha proportional to k^2."""
    if energy <= 0.01:
        return
    for k in range(1, n + 1):
        f = (1.0 - k / float(n + 1)) ** 2
        e = energy * math.exp(-k * dt / 0.16)
        hh = h * (1.0 + 0.13 * e)
        ww = w * (1.0 + 0.55 * e)
        gfx.rect_add(img, cx - ww * 0.5, cx + ww * 0.5, cy - hh * 0.5, cy + hh * 0.5,
                     color, 0.55 * f * e)

# ------------------------------------------------------------------ iris
def iris_white(img, cx, cy, R, rim_a=0.0, halo_a=0.0, soft=1.6):
    """white outside, picture inside - a light/dark inversion centred on a point."""
    if R >= 2600.0:
        return
    d = gfx.disc_mask(cx, cy, R, soft)
    if R <= 0.5:
        img[:] = WHITE
        return
    inv = 1.0 - d
    img *= d[..., None]
    img += inv[..., None] * WHITE
    if rim_a > 0.01:
        gfx.ring_add(img, cx, cy, R, 12.0, ORANGE, rim_a)
        gfx.ring_add(img, cx, cy, R - 9.0, 2.0, HOT, rim_a * 0.8)
    if halo_a > 0.01:
        gfx.halo64(img, cx, cy, R + 20.0, ORANGE, halo_a, len_out=34.0)

# ------------------------------------------------------------------ HUD
_TC = {}
def _tcs(f):
    v = _TC.get(f)
    if v is None:
        s, fr = divmod(f, TL.FPS)
        v = "00:%02d:%02d" % (s, fr)
        _TC[f] = v
    return v

def hud(img, t, f):
    a = 1.0
    # top-left : dot + brand
    dot(img, MARGIN + 5.0, TOP_BASE - 6.0, 5.5, ORANGE, 0.90)
    place(img, "CLAUDE-MOTION-FILM", "mono", 18, MARGIN + 22.0, TOP_BASE, GREY, 0.62, track=0.22)
    # top-right : timecode
    place(img, _tcs(f), "mono", 18, W - MARGIN, TOP_BASE, DIM, 0.72, track=0.22, align="right")
    # bottom-left : frame counter
    place(img, "FRAME %04d / %04d" % (f, TL.NFRAMES), "mono", 18, MARGIN, BOT_BASE, DIM, 0.55, track=0.22)
    # bottom-right : illustrative
    place(img, "illustrative", "mono", 16, W - MARGIN, BOT_BASE, DIM, 0.42, track=0.22, align="right")
    # progress
    p = clamp01(f / float(TL.NFRAMES - 1))
    hairline(img, PROG_X0, PROG_X1, PROG_Y, 2.0, ORANGE, 0.20)
    hairline(img, PROG_X0, PROG_X0 + (PROG_X1 - PROG_X0) * p, PROG_Y, 2.0, ORANGE, 0.85)
    dot(img, PROG_X0 + (PROG_X1 - PROG_X0) * p, PROG_Y, 3.6, HOT, 0.95)
