# -*- coding: utf-8 -*-
"""particles.py - the flow-field murmuration and the glyph aggregation.

Two behaviours, both pure functions of time:
  * 8.00-10.00  a dot bursts into N particles that ride a curl-ish flow field
                (tangential swirl + moving roost + weak cohesion, speed-normalised
                so the swarm reads as one ribbon rather than a gas).
  * 10.00->     the swarm re-flows into glyph targets by MINIMUM TOTAL TRAVEL with a
                perpendicular arc on every path, staggered per particle.

Nothing here is random at render time: the simulation is seeded and cached, so
frame 300 is the same on every machine.
"""
import math
import os

import numpy as np

import timeline as TL

N = 9000          # density is the whole reason a glyph reads: the reference sampler
                  # takes one particle per 4x4 px grid cell, which is thousands, not hundreds
T_BURST = float(TL.B5_HIT)      # 8.00  the line contracts to a dot, then bursts
T_AGG   = float(TL.B6_HIT)      # 10.00 the swarm becomes a word
AGG_DUR = 0.75
DELAY_MAX = 0.06          # last particle lands at 12.81 -> fully assembled on frame 385,
                          # so the flash at frame 386 fires on a completed formation

# cubic-bezier(0.71, 0.00, 0.99, 0.52) - a hard ease-IN: the swarm hangs, then is pulled
# in and slams. The previous 1-(1-u)^4 was an ease-OUT (fast start, slow stop), which is
# why the motion read as a hard slide rather than as attraction.
CB = (0.71, 0.00, 0.99, 0.52)


def _bez(t, p1, p2):
    mt = 1.0 - t
    return 3.0 * mt * mt * t * p1 + 3.0 * mt * t * t * p2 + t * t * t


def bezier_ease(x):
    """Vectorised cubic-bezier: solve x(t)=x by bisection, then read y(t)."""
    x = np.clip(x, 0.0, 1.0)
    lo = np.zeros_like(x)
    hi = np.ones_like(x)
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        v = _bez(mid, CB[0], CB[2])
        lo = np.where(v < x, mid, lo)
        hi = np.where(v < x, hi, mid)
    return _bez(0.5 * (lo + hi), CB[1], CB[3])
CX, CY  = TL.W * 0.5, 486.0     # burst origin == the hairline's centre

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "build", "particles.npz")

_rng = np.random.default_rng(23)
DELAY = _rng.uniform(0.0, DELAY_MAX, N).astype(np.float64)
PHI = _rng.uniform(0.0, 2.0 * np.pi, (N, 2)).astype(np.float64)
IS_OR = (_rng.random(N) < 0.06)


# --------------------------------------------------------------------- targets
def glyph_points(text, key, size, base, n, kern=True, seed=5):
    """Sample n points that sit exactly on the glyph ink drawn by common.place()."""
    import gfx
    m, ox, oy, _ = gfx.text_ink(text, key, int(round(size)), 0, int(kern))
    thr = 0.40 if float(m.max()) <= 1.01 else 100.0
    ys, xs = np.nonzero(m > thr)
    w = m.shape[1]
    x_left = CX - w * 0.5
    pts = np.stack([xs + x_left + ox, ys + base + oy], 1).astype(np.float64)
    # grid sampling, exactly like the reference's getPixels(step): a regular 4 px lattice
    # gives even coverage, so the letters read cleanly instead of clumping where the
    # random subsample happened to land.
    key = (np.round(pts[:, 0] / 4.0).astype(np.int64) * 100000
           + np.round(pts[:, 1] / 4.0).astype(np.int64))
    _, first = np.unique(key, return_index=True)
    pts = pts[first]
    rng = np.random.default_rng(seed)
    if len(pts) > n:
        pts = pts[rng.permutation(len(pts))[:n]]
    return pts + rng.uniform(-0.55, 0.55, pts.shape)


# ------------------------------------------------------------------ simulation
def simulate():
    rng = np.random.default_rng(17)
    pos = np.array([CX, CY], np.float64) + rng.normal(0.0, 4.0, (N, 2))
    ang = rng.uniform(0.0, 2.0 * np.pi, N)
    sp0 = rng.uniform(700.0, 2300.0, N)
    vel = np.stack([np.cos(ang), np.sin(ang)], 1) * sp0[:, None]
    ph = rng.uniform(0.0, 2.0 * np.pi, (N, 2))
    wi = rng.uniform(-1.0, 1.0, N) * 380.0
    globals()["WI"] = wi
    dt = 1.0 / 60.0
    nsteps = int(round((T_AGG - T_BURST) * 60.0)) + 1
    P = np.empty((nsteps, N, 2), np.float32)
    for s in range(nsteps):
        tt = s * dt
        fx = np.cos(pos[:, 1] * 0.0072 + tt * 1.15 + ph[:, 0] * 0.40)
        fy = np.cos(pos[:, 0] * 0.0061 - tt * 0.95 + ph[:, 1] * 0.40)
        # a sweeping RIBBON, not a shell: every particle owns a slot along an axis that
        # slowly turns, so the swarm reads as a band of starlings instead of a ring.
        # the roost must stay SLOWER than the swarm can fly, or the swarm orbits it
        # forever and reads as a ring (that was the bug: 930 px/s roost vs 640 px/s cap)
        roost = np.array([CX + 430.0 * math.sin(0.78 * tt + 0.40),
                          CY + 175.0 * math.sin(1.15 * tt + 1.10) - 70.0])
        ang = 0.85 * math.sin(0.90 * tt + 0.9) + 0.22 * math.sin(1.70 * tt)
        axis = np.array([math.cos(ang), math.sin(ang) * 0.42])
        tgt = roost[None, :] + WI[:, None] * axis[None, :]
        d = tgt - pos
        dn = np.linalg.norm(d, axis=1, keepdims=True) + 1e-3
        com = pos.mean(0)
        acc = (np.stack([fx, fy], 1) * 430.0
               + (d / dn) * np.clip(dn, 0.0, 260.0) * 3.4 * min(1.0, tt / 0.35)
               + (com - pos) * 0.5)
        vel = vel + acc * dt
        sp = np.linalg.norm(vel, axis=1, keepdims=True) + 1e-6
        vhi = 2600.0 if tt < 0.30 else 640.0
        vel = vel / sp * np.clip(sp, 55.0, vhi)
        pos = pos + vel * dt
        # soft walls: a margin force, not a clip, so the swarm turns instead of squaring off
        lo = np.array([110.0, 132.0])
        hi = np.array([TL.W - 110.0, 655.0])
        pos = pos + np.where(pos < lo, (lo - pos) * 0.10, 0.0) + np.where(pos > hi, (hi - pos) * 0.10, 0.0)
        P[s] = pos
    return P


def simulate_ribbon():
    """Analytic flowing band. Free-running physics kept finding limit cycles (rings),
    so the swarm is placed on a travelling spine instead: deterministic, no rings,
    and every particle still carries its own flutter phase."""
    rng = np.random.default_rng(17)
    S = rng.uniform(0.0, 1.0, N)
    TH = rng.normal(0.0, 1.0, N)
    FL = rng.uniform(0.0, 2.0 * np.pi, (N, 2))
    c0 = np.array([CX, CY])
    dt = 1.0 / 60.0
    nsteps = int(round((T_AGG - T_BURST) * 60.0)) + 1
    P = np.empty((nsteps, N, 2), np.float32)
    for s in range(nsteps):
        tt = s * dt
        e = 1.0 - math.exp(-tt / 0.17)          # 0 -> 1 : the burst leaving the dot
        kick = 1.0 + 0.55 * math.exp(-tt / 0.10)  # slight overshoot on the way out
        xs = 150.0 + S * (TL.W - 300.0)
        ys = (CY - 70.0
              + 150.0 * np.sin(6.28318 * 1.55 * S + 2.10 * tt)
              + 62.0 * np.sin(6.28318 * 3.10 * S - 1.35 * tt + 1.0))
        xs = xs + 34.0 * TH * np.sin(1.70 * tt + FL[:, 0])
        ys = ys + 30.0 * TH * np.cos(1.50 * tt + FL[:, 1])
        a = 0.085 * math.sin(0.80 * tt)
        ca, sa = math.cos(a), math.sin(a)
        dx = xs - c0[0]
        dy = ys - c0[1]
        xs = c0[0] + ca * dx - sa * dy
        ys = c0[1] + sa * dx + ca * dy
        P[s] = c0[None, :] + (np.stack([xs, ys], 1) - c0[None, :]) * (e * kick)
    return P


def assign(src, tgt):
    """Order-preserving pairing along a slanted scan line. At 4200 points an all-pairs
    matching is a 17 M-entry matrix; sorting both sets by the same key removes long
    crossings for free and is visually indistinguishable once the paths are arced."""
    def key(p):
        return p[:, 0] + 0.35 * p[:, 1]
    si = np.argsort(key(src))
    ti = np.argsort(key(tgt))
    out = np.empty_like(tgt)
    k_src = si[np.linspace(0, len(si) - 1, len(tgt)).astype(np.int64)] \
        if len(si) != len(tgt) else si
    out[k_src] = tgt[ti]
    return out


def build():
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    P = simulate_ribbon()
    tgt = glyph_points("claude", "serif", 500, 540.0, N, kern=True, seed=5)
    TGT = assign(P[-1], tgt).astype(np.float32)
    np.savez(CACHE, P=P, TGT=TGT)
    return P, TGT


_state = {}


def load():
    if "P" not in _state:
        if not os.path.exists(CACHE):
            build()
        d = np.load(CACHE)
        _state["P"] = d["P"]
        _state["TGT"] = d["TGT"]
    return _state["P"], _state["TGT"]


# ------------------------------------------------------------------- kinematics
def flow_at(t):
    P, _ = load()
    x = (t - T_BURST) * 60.0
    x = min(max(x, 0.0), len(P) - 1.0)
    j = int(math.floor(x))
    a = x - j
    j = min(j, len(P) - 2)
    return (P[j] * (1.0 - a) + P[j + 1] * a).astype(np.float64)


def positions(t):
    P, TGT = load()
    if t <= T_AGG:
        return flow_at(t)
    P0 = flow_at(T_AGG - 1e-4)
    uu = np.clip((t - T_AGG - DELAY) / AGG_DUR, 0.0, 1.0)
    e = bezier_ease(uu)
    d = TGT - P0
    nrm = np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    perp = np.stack([-d[:, 1], d[:, 0]], 1) / nrm
    # a shallower arc than before: with an accelerating curve the straight-ish approach
    # already reads as gravity, and a big bow would fight it
    out = P0 + d * e[:, None] + perp * (42.0 * np.sin(np.pi * uu))[:, None]
    if t > T_AGG + AGG_DUR:
        # the formation tightens as it settles: residual jitter decays so the glyph edge
        # hardens at the moment the ink hands over
        k = float(np.clip((t - T_AGG - AGG_DUR) / 0.30, 0.0, 1.0))
        amp = 1.05 * (1.0 - 0.72 * k)
        out = TGT + amp * np.stack([np.sin(2.0 * np.pi * 1.30 * t + PHI[:, 0]),
                                    np.cos(2.0 * np.pi * 1.70 * t + PHI[:, 1])], 1)
    return out


def speeds(t):
    return np.linalg.norm(positions(t) - positions(t - 0.022), axis=1)


# --------------------------------------------------------------------- drawing
TAPS = ((0.000, 1.00), (0.022, 0.42), (0.044, 0.18), (0.070, 0.07))


def draw(img, t, gain=1.0):
    """Round dots, phosphor-trailed.

    The reference never clears its canvas - it fills with rgba(bg, 0.18) each frame, so
    every particle leaves a decaying smear and the motion reads smooth. A pure function
    of time cannot hold a framebuffer, so the same look is reconstructed from four time
    taps. Dot width comes from a 0.9 px gaussian: a ~4 px disc that tiles the 4 px
    sampling lattice, which is what keeps the glyph crisp instead of muddy.
    """
    import gfx
    H, Wd = TL.H, TL.W
    orn = IS_OR
    cr = (~orn).astype(np.float64)
    orr = orn.astype(np.float64)
    acc_c = np.zeros(H * Wd, np.float64)
    acc_o = np.zeros(H * Wd, np.float64)
    for dt, w in TAPS:
        ts = t - dt
        if ts < T_BURST:
            continue
        Q = positions(ts)
        ix = np.clip(Q[:, 0].astype(np.int32), 0, Wd - 1)
        iy = np.clip(Q[:, 1].astype(np.int32), 0, H - 1)
        flat = iy * Wd + ix
        acc_c += w * np.bincount(flat, weights=cr, minlength=H * Wd)
        acc_o += w * np.bincount(flat, weights=orr, minlength=H * Wd)
    acc_c = gfx.blur(acc_c.reshape(H, Wd).astype(np.float32), 1.15)
    acc_o = gfx.blur(acc_o.reshape(H, Wd).astype(np.float32), 1.15)
    # tone-map the accumulation: without this the dense interior clips to flat white and
    # the formation stops reading as dots at all.
    acc_c = acc_c / (1.0 + 0.85 * acc_c)
    acc_o = acc_o / (1.0 + 0.85 * acc_o)
    # NB: the frame buffer is 0..1 (gfx.finish clips to 1 and scales by 255), so the
    # colour tokens must come from gfx.* which are normalised - using the raw 0..255
    # TL.* tuples here clips every particle to white.
    k = gain * 4.6          # measured: p90 = 0.141, so 4.6 puts the typical dot at 0.65
    img += acc_c[..., None] * gfx.CREAM * k
    img += acc_o[..., None] * gfx.ORANGE * (k * 1.35)


if __name__ == "__main__":
    import time
    t0 = time.time()
    P, TGT = build()
    print("built in %.1fs  P%s TGT%s" % (time.time() - t0, P.shape, TGT.shape))
    print("target bbox x[%.0f..%.0f] y[%.0f..%.0f]" %
          (TGT[:, 0].min(), TGT[:, 0].max(), TGT[:, 1].min(), TGT[:, 1].max()))
