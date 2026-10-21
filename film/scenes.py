# -*- coding: utf-8 -*-
"""scenes.py - six bars of one motif.

THE BAR is a cursor (B1), a comb (B2/B3), a collapse (B4), a signature (B5)
and an underline (B6).  Nothing else appears in the film.

render_frame is a pure function of the frame index: no state crosses frames.
"""
from __future__ import annotations
import math
import numpy as np
import timeline as TL
import gfx
import common as CM
from gfx import (W, H, CREAM, GREY, DIM, ORANGE, HOT, WHITE, BG, mix,
                 clamp01, lerp, smooth, out_expo, in_expo, inout_cubic, in_cubic,
                 out_cubic)

CX = 960.0
BAR_CY = 486.0
COPY_BASE = 840.0
SPAN_FULL = 1768.0
WIN_W, WIN_H = 1040.0, 585.0
WIN_CX, WIN_CY = 960.0, 372.0
WIN_X1 = WIN_CX + WIN_W * 0.5
WIN_Y1 = WIN_CY + WIN_H * 0.5
UNDER_Y = 734.0
BRAND_BASE = 540.0
NAME_BASE = 670.0
CTA_BASE = 860.0
UNDER_W = 900.0
SERIF_SZ = 500
MONO_SZ = 118

H_MIN, H_MAX = 118.0, 380.0
def h_for(n):
    n = max(1.0, float(n))
    return float(np.clip(360.0 * n ** -0.14, H_MIN, H_MAX))

def w_for(n, span, wmax=2.4):
    if n <= 1:
        return 3.2
    pitch = span / float(n - 1)
    return float(np.clip(pitch * 0.44, 0.34, wmax))

def env_alphas(n, base=0.94):
    """a lens falloff across the array, so a dense comb is a lit band, not a slab."""
    if n < 20:
        return np.full(n, base, np.float32)
    lo = 1.0 - 0.38 * smooth((n - 20) / 320.0)
    u = np.abs(np.linspace(-1.0, 1.0, n))
    return (base * (lo + (1.0 - lo) * (1.0 - u ** 2.4))).astype(np.float32)

def evenly(n, span, cx=CX):
    if n <= 1:
        return np.array([cx], np.float32)
    p = span / float(n - 1)
    return (cx + (np.arange(n, dtype=np.float32) - (n - 1) * 0.5) * p).astype(np.float32)

# per-index height character for the fibonacci signature (B5)
FAC = {
    1:  np.array([1.00]),
    3:  np.array([1.00, 0.55, 0.82]),
    5:  np.array([0.82, 1.00, 0.48, 0.90, 0.62]),
    8:  np.array([0.62, 0.88, 1.00, 0.46, 0.78, 0.55, 0.92, 0.70]),
    13: np.array([1.00, 0.62, 0.88, 0.45, 0.72, 0.96, 0.58, 0.80, 0.40, 0.92, 0.68, 0.86, 0.52]),
}

# ------------------------------------------------------------------ bar field
def draw_field(img, xs, ws, hs, ys, alphas, color, clip=None, gain=1.0):
    n = len(xs)
    if n == 0:
        return
    uni = (float(np.ptp(hs)) < 1e-3) and (float(np.ptp(ys)) < 1e-3) and n > 40
    if uni:
        _fast(img, xs, float(ws[0]), float(hs[0]), float(ys[0]), alphas, color, clip, gain)
    else:
        for i in range(n):
            gfx.rect_add(img, xs[i] - ws[i] * 0.5, xs[i] + ws[i] * 0.5,
                         ys[i] - hs[i] * 0.5, ys[i] + hs[i] * 0.5,
                         color, alphas[i] * gain, clip)

def _fast(img, xs, w, h, cy, alphas, color, clip, gain):
    ix0 = max(0, int(np.floor(xs.min() - w * 0.5)) - 1)
    ix1 = min(W, int(np.ceil(xs.max() + w * 0.5)) + 2)
    if ix1 <= ix0:
        return
    X = (np.arange(ix0, ix1, dtype=np.float32) + 0.5)[None, :]
    x0 = (xs - w * 0.5)[:, None]; x1 = (xs + w * 0.5)[:, None]
    cov = np.clip(np.minimum(X, x1) - np.maximum(X - 1.0, x0), 0.0, 1.0)
    cov *= (alphas * gain)[:, None]
    tx = cov.sum(0)
    Y = (np.arange(H, dtype=np.float32) + 0.5)
    y0, y1 = cy - h * 0.5, cy + h * 0.5
    cyv = np.clip(np.minimum(Y, y1) - np.maximum(Y - 1.0, y0), 0.0, 1.0)
    rows = np.nonzero(cyv > 0.0)[0]
    if rows.size == 0:
        return
    r0, r1 = int(rows[0]), int(rows[-1]) + 1
    layer = np.outer(cyv[r0:r1], tx)
    if clip is not None:
        layer = layer * clip[r0:r1, ix0:ix1]
    img[r0:r1, ix0:ix1] += layer[..., None] * color

def morph(n0, n1, s0, s1, u, cx=CX, f0=None, f1=None, wmax=2.4):
    n = max(int(n0), int(n1))
    i = np.arange(n, dtype=np.float32)
    p0 = evenly(n0, s0, cx); p1 = evenly(n1, s1, cx)
    m0 = np.clip((i * (n0 / float(n))).astype(np.int32), 0, int(n0) - 1)
    m1 = np.clip((i * (n1 / float(n))).astype(np.int32), 0, int(n1) - 1)
    xs = p0[m0] * (1.0 - u) + p1[m1] * u
    w = lerp(w_for(n0, s0, wmax), w_for(n1, s1, wmax), u)
    a = h_for(n0) if f0 is None else h_for(n0) * f0[m0]
    b = h_for(n1) if f1 is None else h_for(n1) * f1[m1]
    hs = np.broadcast_to(a, (n,)).astype(np.float32) * (1.0 - u) + np.broadcast_to(b, (n,)).astype(np.float32) * u
    return xs.astype(np.float32), np.full(n, w, np.float32), hs, m0, m1

# ------------------------------------------------------------------ envelopes
def env(t, t0, attack=0.018, tau=0.155):
    if t < t0 - attack:
        return 0.0
    if t < t0:
        return out_cubic((t - (t0 - attack)) / attack)
    return math.exp(-(t - t0) / tau)

def win_mask(x0, y0, x1, y1):
    m = np.zeros((H, W), np.float32)
    a = max(0, int(x0)); b = min(W, int(x1) + 1)
    c = max(0, int(y0)); d = min(H, int(y1) + 1)
    if b > a and d > c:
        m[c:d, a:b] = 1.0
    return m

_GROUND = [None]
def ground():
    if _GROUND[0] is None:
        X, Y = gfx.grids()
        d2 = ((X - 960.0) / 760.0) ** 2 + ((Y - 500.0) / 520.0) ** 2
        _GROUND[0] = np.exp(-d2 * 1.6).astype(np.float32)[..., None] * 0.010
    return _GROUND[0]

# ================================================================== B1 蓄力
def b1(t, img):
    E = 0.0
    for p in TL.B1_PULSE:
        E += env(t, p, 0.016, 0.150)
    E = min(E, 1.45)
    grow = out_expo((t - 0.02) / 0.62)
    h = 360.0 * grow * (1.0 + 0.145 * E)
    w = 3.2 * (1.0 + 0.60 * E)
    a = clamp01(grow * 1.2)
    if t >= 1.795:
        s = inout_cubic((t - 1.795) / 0.135)
        h *= (1.0 - s)
        w *= (1.0 - 0.40 * s)
        a *= (1.0 - smooth((t - 1.845) / 0.105))
    col = mix(CREAM, HOT, 0.60 * E)
    if E > 0.01:
        gfx.blob_add(img, CX, BAR_CY, 120.0, ORANGE, 0.085 * E)
        CM.ghost_bar(img, CX, BAR_CY, w, h, mix(CREAM, ORANGE, 0.35), t, E, n=14, dt=0.010)
    if a > 0.004 and h > 0.4:
        CM.vbar(img, CX, BAR_CY, w, h, col, a)

def b1_over(t, img):
    return

# ================================================================== B2 爆发
# The comb doubles on every 8th note (0.25 s).  Three things make each doubling
# read as ENERGY instead of a dissolve:
#   1. every new bar is BORN on its parent's pixels and splits outward, staggered
#      centre -> edge, so you watch one bar press another open;
#   2. the heights carry a 16-step rhythm that marches one step per 8th note with a
#      per-beat kick riding on a travelling band (a visible "one-two" pulse);
#   3. bars are fat while there are few of them and thin down as they pack
#      (30 px -> 1.6 px), so the array gains density and loses weight at once.
B2_PAT = np.array([0.30, 0.94, 0.52, 1.00, 0.40, 0.76, 0.26, 0.88,
                   0.62, 0.82, 0.34, 0.70, 0.98, 0.46, 0.84, 0.28], np.float32)
B2_STEP = 0.25       # 8th note at 120 BPM
B2_RISE = 0.075      # one pair separates in this long
B2_SPREAD = 0.062    # stagger from the middle of the comb out to its edges
                     #   0.015 + 0.062 + 0.075 = 0.152 s  ->  every doubling settles
                     #   inside its own 8th note, and the settled comb still breathes
                     #   through 40% of the beat instead of dissolving forever.

def _expo_vec(u):
    u = np.clip(u, 0.0, 1.0)
    return np.where(u >= 1.0, 1.0, 1.0 - np.exp2(-10.0 * u)).astype(np.float32)

def b2_span(n):
    """the comb both multiplies and widens: 780 px at one bar, full width by sixteen.
    Depends only on the count, so stage k's arrival is stage k+1's departure."""
    return lerp(780.0, SPAN_FULL, float(smooth((n - 2.0) / 12.0)))

def b2_heights(n, t):
    idx = np.arange(n)
    bp = (t - TL.B2_HIT) / B2_STEP
    beat = int(math.floor(bp))
    age = bp - beat
    q = smooth(age / 0.055)                      # 55 ms attack between steps
    pat = B2_PAT[(idx + (beat - 1) * 3) % 16] * (1.0 - q) + B2_PAT[(idx + beat * 3) % 16] * q
    kick = math.exp(-age * B2_STEP / 0.085) * q
    band = ((idx % 4) == (beat % 4)).astype(np.float32)
    return (h_for(n) * (0.30 + 0.92 * pat) * (1.0 + 0.42 * band * kick)).astype(np.float32)

def b2(t, img):
    k = int(min(7, max(0, math.floor((t - TL.B2_HIT) / B2_STEP))))
    t_k = TL.B2_HIT + B2_STEP * k
    n0, n1 = 2 ** k, 2 ** (k + 1)
    s0, s1 = b2_span(n0), b2_span(n1)
    if t > 3.84:                       # hand the comb over to the B3 window width
        sh = float(smooth((t - 3.84) / 0.16))
        s0, s1 = s0 + (1400.0 - s0) * sh, s1 + (1400.0 - s1) * sh
    p0 = evenly(n0, s0)
    p1 = evenly(n1, s1)
    idx = np.arange(n1)
    x0 = p0[np.minimum(idx // 2, n0 - 1)].copy()
    odd = (idx & 1).astype(bool)
    x0[odd] += 1.5                    # a hair apart, never a see-through clone
    cen = np.abs(idx - 0.5 * (n1 - 1)) / max(1.0, 0.5 * (n1 - 1))
    u = _expo_vec((t - t_k - 0.015 - B2_SPREAD * cen) / B2_RISE)
    xs = (x0 + (p1 - x0) * u).astype(np.float32)
    # teeth: fat while the comb is short, thinning as it packs -> density gains,
    # weight drops, and the array reads as one instrument being tightened
    ws = np.full(n1, float(np.clip(s1 / max(1.0, n1 - 1.0) * 0.40, 1.55, 52.0)), np.float32)
    hs = b2_heights(n1, t)
    al = np.where(odd, 0.86 * (0.20 + 0.80 * u), 0.86).astype(np.float32)
    draw_field(img, xs, ws, hs, np.full(n1, BAR_CY), al, CREAM, gain=1.0)
    b2_dust(t, img)

def b2_dust(t, img):
    X = []; Y = []; WW = []
    for d in range(8):
        t0 = 2.00 + 0.25 * d
        age = t - t0
        if age < 0.0 or age > 0.62:
            continue
        rs = np.random.RandomState(900 + d)
        n = 520
        ang = rs.uniform(0.0, 2.0 * np.pi, n)
        spd = 320.0 + 1650.0 * rs.uniform(0.0, 1.0, n) ** 2.2
        r = spd * age
        X.append(CX + np.cos(ang) * r)
        Y.append(BAR_CY + np.sin(ang) * r * 0.52)
        WW.append((0.030 * (1.0 - age / 0.62) ** 2.0) / n ** 0.45 * 40.0)
    if X:
        gfx.particles_add(img, np.concatenate(X), np.concatenate(Y),
                          float(np.mean(WW)), mix(CREAM, ORANGE, 0.3), soft=0.7)

# ================================================================== B3 900帧
def b3(t, img):
    wu = out_expo((t - 4.00) / 0.40)
    ww = lerp(3.0, WIN_W, wu); wh = lerp(360.0, WIN_H, wu)
    wy = lerp(BAR_CY, WIN_CY, wu)
    wx0, wx1 = CX - ww * 0.5, CX + ww * 0.5
    wy0, wy1 = wy - wh * 0.5, wy + wh * 0.5
    wm = win_mask(wx0, wy0, wx1, wy1)

    # ---- bars, clipped by the window (the array is taller than its frame)
    fcy = lerp(BAR_CY, WIN_CY, wu)
    if t < 4.25:
        n0, n1, uu = 128, 256, out_expo((t - 4.00) / 0.16)
    elif t < 4.50:
        n0, n1, uu = 256, 512, out_expo((t - 4.25) / 0.16)
    elif t < 4.75:
        n0, n1, uu = 512, 900, out_expo((t - 4.50) / 0.25)
    else:
        n0, n1, uu = 900, 900, 1.0
    xs, ws, hs, _, _ = morph(n0, n1, 1400.0, 1400.0, uu)
    # 900 solid bars read as one grey slab: give them real gaps and a beat-driven
    # silhouette so the array is legible as a waveform instead of a gradient.
    n_bars = len(xs)
    pitch = 1400.0 / max(1.0, float(n_bars))
    ws2 = np.full(n_bars, float(np.clip(pitch * 0.55, 1.0, 52.0)), np.float32)
    ph = np.arange(n_bars, dtype=np.float32) / max(1.0, n_bars - 1.0)
    wave = (0.40 + 0.60 * np.power(0.5 + 0.5 * np.sin(ph * 25.0 + t * 6.5), 1.3)).astype(np.float32)
    for tk in TL.B3_TICKS:
        age = t - tk
        if 0.0 <= age <= 0.34:
            wave = wave * (1.0 + 0.55 * math.exp(-age / 0.085)
                           * np.cos(ph * 47.0 + age * 30.0)).astype(np.float32)
    hs2 = (float(h_for(n_bars)) * 1.20 * wave).astype(np.float32)
    draw_field(img, xs, ws2, hs2, np.full(n_bars, fcy), env_alphas(n_bars, 0.94),
               CREAM, clip=wm)

    # ---- frame ticks: the window advances a frame, the whole picture nods
    for tk in TL.B3_TICKS:
        age = t - tk
        if 0.0 <= age <= 0.22:
            f = age / 0.22
            band = lerp(wy0 + 24.0, wy1 - 24.0, smooth(f))
            gfx.rect_add(img, wx0, wx1, band - 26.0, band + 26.0, CREAM, 0.085 * (1.0 - f), wm)
            gfx.rect_add(img, wx0, wx1, band + 24.0, band + 26.5, CREAM, 0.34 * (1.0 - f), wm)
            gfx.rect_add(img, wx0, wx1, band - 26.5, band - 24.0, ORANGE, 0.20 * (1.0 - f), wm)

    # ---- window furniture (drawn last so it is never clipped)
    fl = 0.0
    for tk in TL.B3_TICKS:
        age = t - tk
        if 0.0 <= age <= 0.16:
            fl = max(fl, 1.0 - age / 0.16)
    ba = 0.38 + 0.42 * fl
    bt = 2.0
    gfx.rect_add(img, wx0, wx1, wy0 - bt, wy0 + bt, CREAM, ba)
    gfx.rect_add(img, wx0, wx1, wy1 - bt, wy1 + bt, CREAM, ba)
    gfx.rect_add(img, wx0 - bt, wx0 + bt, wy0, wy1, CREAM, ba)
    gfx.rect_add(img, wx1 - bt, wx1 + bt, wy0, wy1, CREAM, ba)
    if wu > 0.55:
        k = smooth((wu - 0.55) / 0.30)
        L = 26.0
        for cxx, sgn in ((wx0, 1.0), (wx1, -1.0)):
            for cyy, sgn2 in ((wy0, 1.0), (wy1, -1.0)):
                gfx.rect_add(img, min(cxx, cxx + sgn * L), max(cxx, cxx + sgn * L),
                             cyy - 2.0, cyy + 2.0, ORANGE, 0.85 * k)
                gfx.rect_add(img, cxx - 2.0, cxx + 2.0,
                             min(cyy, cyy + sgn2 * L), max(cyy, cyy + sgn2 * L), ORANGE, 0.85 * k)

# ================================================================== B4 塌缩 (PEAK)
def b4(t, img):
    if t < 6.18:
        u = inout_cubic((t - 6.00) / 0.18)
        xs, ws, hs, _, _ = morph(900, 1, 1400.0, 0.0, u)
        al = np.full(len(xs), 0.30 + 0.70 * (1.0 - u) ** 0.55)
        draw_field(img, xs, ws, hs, np.full(len(xs), BAR_CY), al,
                   mix(CREAM, HOT, 0.45 * (1.0 - u)))
    else:
        hb = 360.0 * (1.0 + 0.028 * math.sin(2.0 * math.pi * (t - 6.18) / 2.0))
        a = 0.44 + 0.46 * smooth((t - 6.20) / 0.55)
        e = 0.30 + 0.70 * smooth((t - 6.20) / 1.2)
        CM.ghost_bar(img, CX, BAR_CY, 1.7, hb, CREAM, t, 0.20 * e, n=12, dt=0.013)
        gfx.blob_add(img, CX, BAR_CY, 46.0, mix(ORANGE, HOT, 0.4), 0.055 * e)
        CM.vbar(img, CX, BAR_CY, 1.7, hb, CREAM, a)

# ================================================================== B5 任何主题
B5_SEG = [(8.00, 1, 3, 0.0, 300.0, 0.20),
          (8.50, 3, 5, 300.0, 420.0, 0.17),
          (9.00, 5, 8, 420.0, 510.0, 0.18),
          (9.50, 8, 13, 510.0, 580.0, 0.19)]

def b5_state(t):
    n0 = n1 = 1
    s0 = s1 = 0.0
    u = 1.0
    for (ta, a, b, sa, sb, d) in B5_SEG:
        if t >= ta:
            n0, n1, s0, s1 = a, b, sa, sb
            u = out_expo((t - ta) / d)
    n0 = int(n0); n1 = int(n1)
    xs, ws, hs, m0, m1 = morph(n0, n1, s0, s1, u, f0=FAC[n0], f1=FAC[n1], wmax=26.0)
    if t > 9.72:
        k = smooth((t - 9.72) / 0.28)
        s = 1.0 - 0.14 * k
        xs = CX + (xs - CX) * s
        ws = ws * s
        hs = hs * (1.0 - 0.06 * k)
    return xs, ws, hs

def b5(t, img):
    xs, ws, hs = b5_state(t)
    draw_field(img, xs, ws, hs, np.full(len(xs), BAR_CY), np.full(len(xs), 0.92),
               CREAM, gain=1.0)
    for j, (ta, a, b, sa, sb, d) in enumerate(B5_SEG):
        age = t - ta
        if age < 0.0 or age > 0.34:
            continue
        f = age / 0.34
        CM.ring(img, CX, BAR_CY, 36.0 + (300.0 + 40.0 * j) * inout_cubic(f), 1.8,
                CREAM, 0.42 * (1.0 - f) ** 1.5)
        CM.ring(img, CX, BAR_CY, 36.0 + (300.0 + 40.0 * j) * inout_cubic(f) * 0.62, 1.2,
                ORANGE, 0.26 * (1.0 - f) ** 2.0)

# ================================================================== B6 落版
# The swarm lands first, then the ink resolves on top of it at the same coordinates.
# Frame-exact: 11.0333 s is frame 331. The swap happens ON the white flash peak, so the
# audience never sees it - that is the whole trick.
P_FLASH = 385.0 / 30.0      # 12.8333 s = 12s25f. Measured: the last particle is at its
                            # target by 12.81 s, so this is the FIRST frame on which the
                            # formation is complete - the flash fires on completion itself.
BRAND_IN = P_FLASH    # the real type appears on frame 331, at full opacity, no animation
CTA_IN = 13.24

def _brand_geom():
    w1 = CM.text_width("claude", "serif", SERIF_SZ, 0.0, kern=True)
    w2 = CM.text_width("-motion-film", "mono", MONO_SZ, 0.0, kern=True)
    return w1, w2

def b6(t, img):
    # ---- 13 bars -> one underline
    u = out_expo((t - 12.00) / 0.24)
    if u < 0.90:
        xs0, ws0, hs0 = b5_state(9.999)
        n = len(xs0)
        for i in range(n):
            x = lerp(float(xs0[i]), CX, u)
            w = lerp(float(ws0[i]), UNDER_W, u)
            h = lerp(float(hs0[i]), 2.6, u)
            y = lerp(BAR_CY, UNDER_Y, u)
            gfx.rect_add(img, x - w * 0.5, x + w * 0.5, y - h * 0.5, y + h * 0.5,
                         mix(CREAM, HOT, 0.5), 0.34)
    # ---- the underline, the motif in its last role
    if t >= 12.00:
        uw = UNDER_W
        col = CREAM
        al = 0.95
        if t >= 15.70:
            f = inout_cubic((t - 15.70) / 0.275)
            uw = UNDER_W * (1.0 - f)
            al = 0.95 + 0.05 * f
            col = mix(CREAM, HOT, 0.75 * f)
        hot = 0.0
        if t >= TL.B6_FINAL_HIT:
            hot = math.exp(-(t - TL.B6_FINAL_HIT) / 0.10)
            col = mix(col, HOT, 0.85 * hot)
            al = min(1.4, al + 0.45 * hot)
        if uw > 0.4:
            gfx.rect_add(img, CX - uw * 0.5, CX + uw * 0.5, UNDER_Y - 1.7, UNDER_Y + 1.7,
                         col, al)
            gfx.blob_add(img, CX, UNDER_Y, 120.0, mix(ORANGE, HOT, 0.5),
                         0.05 + 0.09 * (hot if t >= TL.B6_FINAL_HIT else 0.0))

    # ---- brand lockup : serif italic word, mono name on the next line, one rule
    if t >= BRAND_IN:
        # HARD ON. No ramp, no blur-in, no slide: any entrance animation here would read
        # as a seam against the particle formation it is replacing.
        w1, w2 = _brand_geom()
        hot2 = 0.0
        if t >= TL.B6_FINAL_HIT:
            hot2 = math.exp(-(t - TL.B6_FINAL_HIT) / 0.13)
        for s, key, sz, kk, base, xx in (
                ("claude", "serif", SERIF_SZ, True, BRAND_BASE, CX - w1 * 0.5),
                ("-motion-film", "mono", MONO_SZ, True, NAME_BASE, CX - w2 * 0.5)):
            m, ox, oy, bd = gfx.text_ink(s, key, sz, 0, kk)
            vb = 7.0 * hot2
            mm = gfx.vblur(m, vb) if vb > 0.6 else m
            gfx.blit(img, mm, xx + ox, base + oy,
                     mix(CREAM, HOT, 0.20 * hot2), 0.97)

    # ---- CTA : the one request line, orange full stop
    if t >= CTA_IN:
        CM.copy_line(img, "装上它。", "cjk", 76, CX, CTA_BASE, t, CTA_IN, 13.0,
                     stag=0.11, rev=0.26, slam=1.22, blur0=30.0, alpha=0.95,
                     exit_dur=0.001, accent_last=True)

# ================================================================== overlays
def overlay(t, img):
    # B2 needs one horizontal read of its own: full-width light sweeps on the
    # 2.00 and 3.00 downbeats are what make the doubling feel like acceleration.
    if 2.00 <= t < 2.47:
        CM.light_sweep(img, t, 2.00, dur=0.46, y0=270.0, y1=690.0, n=18, gain=0.32, seed=7)
    if 3.00 <= t < 3.45:
        CM.light_sweep(img, t, 3.00, dur=0.44, y0=270.0, y1=690.0, n=16, gain=0.22, seed=23)
    if 2.00 <= t < 2.62:
        gfx.radial_flash(img, CX, BAR_CY, 1.15 * math.exp(-(t - 2.00) / 0.070), 880.0)
        CM.impact_ring(img, t, 2.00, r0=30.0, r1=1540.0, dur=0.44, thick=2.2, alpha=0.85)
        CM.impact_ring(img, t, 2.00, color=ORANGE, r0=30.0, r1=1180.0, dur=0.38,
                       thick=1.2, alpha=0.55)
    if 4.00 <= t < 4.20:
        gfx.radial_flash(img, CX, BAR_CY, 0.42 * math.exp(-(t - 4.00) / 0.040), 780.0)
        CM.impact_ring(img, t, 4.00, r0=30.0, r1=900.0, dur=0.34, thick=1.6, alpha=0.42)
    if 6.00 <= t < 6.60:
        u = clamp01((t - 6.00) / 0.50)
        R = 36.0 + 2400.0 * inout_cubic(u)
        rim = 0.92 * (1.0 - smooth((R - 300.0) / 1500.0))
        CM.iris_white(img, CX, BAR_CY, R, rim, rim * 0.55)
        img += WHITE * (0.30 * math.exp(-(t - 6.00) / 0.05))
    if 8.00 <= t < 8.34:
        gfx.radial_flash(img, CX, BAR_CY, 0.55 * math.exp(-(t - 8.00) / 0.048), 700.0)
        CM.impact_ring(img, t, 8.00, r0=30.0, r1=760.0, dur=0.30, thick=1.6, alpha=0.45)
    if 12.00 <= t < 12.34:
        gfx.radial_flash(img, CX, UNDER_Y, 0.72 * math.exp(-(t - 12.00) / 0.055), 900.0)
        CM.impact_ring(img, t, 12.00, r0=30.0, r1=1540.0, dur=0.36, thick=2.0, alpha=0.55, cy=UNDER_Y)
        CM.light_sweep(img, t, 12.06, dur=0.44, y0=470.0, y1=610.0, n=14, gain=0.34, seed=101)
    # ---- the seam-hider. A full-frame warm-white hit whose peak lands exactly on the
    # swap frame: attack 60 ms, decay tau 75 ms. Because frame 331 is pure white, the
    # audience cannot see the particles leaving or the type arriving.
    age = t - P_FLASH
    # NO attack: the flash is already at peak on its first frame, which is also the frame
    # where the last particle lands at its target. Only the decay has a transition.
    if 0.0 <= age <= 0.42:
        if age < 0.067:
            a = 1.0                        # peak, held for two frames
        else:
            a = math.exp(-(age - 0.067) / 0.075)
        a = min(1.0, max(0.0, a))
        if a > 0.003:
            img *= (1.0 - a)
            img += a * np.array([1.0, 0.984, 0.962], np.float32)
    if 15.55 <= t < 15.95:
        gfx.radial_flash(img, CX, UNDER_Y, 0.46 * math.exp(-(t - 15.55) / 0.055), 760.0)
        CM.impact_ring(img, t, 15.55, r0=30.0, r1=1540.0, dur=0.42, thick=2.2, alpha=0.62, cy=UNDER_Y)
        CM.impact_ring(img, t, 15.55, color=ORANGE, r0=30.0, r1=1000.0, dur=0.34,
                       thick=1.2, alpha=0.40, cy=UNDER_Y)

# Impact envelope.  Both shake and chroma are TRANSIENTS: they exist only in the
# window right after one of the six AUDIO_HITS and reach exactly 0.0 at the end
# of it, so every other frame is geometrically clean.  (A constant 7px/3px floor
# here is what made the whole film look like a broken render.)
AMP_DUR = 0.240      # shake: attack-free, gone in a quarter second
CH_DUR = 0.165       # chroma: 0.12-0.20 s, then hard zero
IMPACTS = ((2.00, 26.0, 11.0), (4.00, 14.0, 7.0), (6.00, 26.0, 11.0),
           (8.00, 16.0, 8.0), (12.00, 20.0, 9.0), (15.55, 18.0, 8.0))

def shake_at(t):
    amp = 0.0
    ch = 0.0
    for t0, A, C in IMPACTS:
        age = t - t0
        if age < 0.0:
            continue
        if age < AMP_DUR:
            amp = max(amp, A * (1.0 - age / AMP_DUR) ** 1.35)
        if age < CH_DUR:
            ch = max(ch, C * (1.0 - age / CH_DUR) ** 2.0)
    for tk in TL.B3_TICKS:            # frame ticks: the window nods, the lens stays clean
        age = t - tk
        if 0.0 <= age < 0.12:
            amp = max(amp, 5.5 * (1.0 - age / 0.12) ** 1.4)
    # A constant low lens fringing is texture, not damage; the impact transients above
    # ride on top of it.  It relaxes for the lockup so the type stays crisp.
    ch += 2.4 if t < TL.B6_HIT else 1.2
    return max(amp, 0.0), ch

# ================================================================== B5b burst + flow
import particles as PT

P_FADE0, P_FADE1 = 11.02, 11.44

def b5b(t, img):
    """8.00: the breathing hairline contracts into a dot, which then bursts into
    the flow-field swarm.  No cut - the line IS the particle source."""
    if t < 8.14:
        u = inout_cubic((t - 8.00) / 0.14)
        CM.vbar(img, CX, BAR_CY, 1.7, max(0.0, 360.0 * (1.0 - u)), CREAM, 0.90 * (1.0 - 0.45 * u))
        CM.dot(img, CX, BAR_CY, lerp(0.6, 11.0, u), ORANGE, 0.20 + 0.80 * u)
    PT.draw(img, t, gain=1.0)

# The hand-off. Particles are ADDED on top of the ink, so their brightness is itself a
# mask: bloom the swarm until it covers the word, then dim it and the real type is simply
# there. Nothing cross-fades, so there is no double image.
P_BLOOM0, P_BLOOM1 = 12.60, 12.85    # the accelerating swarm glows as it slams in
P_GAIN_PEAK = 1.45


def b6_particles(t, img):
    if t >= P_FLASH:
        return                      # off, instantly, on the flash frame
    if t < P_BLOOM0:
        g = 1.0
    else:
        g = 1.0 + (P_GAIN_PEAK - 1.0) * smooth((t - P_BLOOM0) / (P_BLOOM1 - P_BLOOM0))
    PT.draw(img, t, gain=g)

# ================================================================== frame
def draw(t, img):
    img += ground()
    if t < 2.00:
        b1(t, img)
        CM.copy_line(img, "一句话。", "cjk", 132, CX, COPY_BASE, t, TL.B1_L1_IN, 2.00,
                     stag=0.09, rev=0.26, slam=1.15, blur0=26.0)
    elif t < 4.00:
        b2(t, img)
        CM.copy_line(img, "一支片。", "cjk", 132, CX, COPY_BASE, t, TL.B2_L2_IN, TL.B2_L2_OUT,
                     stag=0.09, rev=0.26, slam=1.15, blur0=28.0)
    elif t < 6.00:
        b3(t, img)
        CM.copy_line(img, "900 帧。", "cjk", 132, CX, COPY_BASE, t, TL.B3_L3_IN, TL.B3_L3_OUT,
                     stag=0.08, rev=0.26, slam=1.15, blur0=28.0)
    elif t < 8.00:
        b4(t, img)
        CM.copy_line(img, "一条线。", "cjk", 150, CX, COPY_BASE, t, TL.B4_L4_IN, TL.B5_HIT,
                     stag=0.10, rev=0.30, slam=1.12, blur0=22.0, alpha=0.94)
    elif t < 12.00:
        b5b(t, img)
        CM.copy_line(img, "任何主题。", "cjk", 132, CX, COPY_BASE, t, TL.B5_L5_IN, TL.B5_L5_OUT,
                     stag=0.08, rev=0.26, slam=1.15, blur0=28.0)
    else:
        b6(t, img)
        b6_particles(t, img)

def render(f, cf=None, cm=None):
    t = f / float(TL.FPS)
    img = gfx.new_frame()
    draw(t, img)
    (cm or CM).hud(img, t, f)
    overlay(t, img)
    img = gfx.post(img, f)
    amp, ch = shake_at(t)
    img = gfx.shake_chroma(img, t, amp, ch)
    return gfx.finish(img)
