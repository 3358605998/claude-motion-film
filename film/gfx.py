# -*- coding: utf-8 -*-
"""gfx.py - toolbox. easing / colour / gaussian / glyphs / primitives / post.

Everything returns float32 in [0,1]. Nothing here knows about the story.
Anti-aliasing: glyphs are rasterised at SS=2 in their own tile and LANCZOS'd down;
vector primitives (bars, rings, dots) use exact analytic pixel coverage, which is
strictly better than 2x supersampling for thin strokes.
"""
from __future__ import annotations
import math
import functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import timeline as TL

W, H = TL.W, TL.H
SS = 2

# ------------------------------------------------------------------ easing
def clamp01(x):
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def lerp(a, b, u):
    return a + (b - a) * u

def smooth(u):
    u = np.clip(u, 0.0, 1.0); return u * u * (3.0 - 2.0 * u)

def out_cubic(u):
    u = clamp01(u); v = 1.0 - u; return 1.0 - v * v * v

def in_cubic(u):
    u = clamp01(u); return u * u * u

def inout_cubic(u):
    u = clamp01(u)
    return 4.0 * u * u * u if u < 0.5 else 1.0 - (-2.0 * u + 2.0) ** 3 / 2.0

def out_expo(u):
    u = clamp01(u)
    return 1.0 if u >= 1.0 else 1.0 - math.pow(2.0, -10.0 * u)

def in_expo(u):
    u = clamp01(u)
    return 0.0 if u <= 0.0 else math.pow(2.0, 10.0 * (u - 1.0))

def inout_sine(u):
    u = clamp01(u); return 0.5 - 0.5 * math.cos(math.pi * u)

def out_back(u, s=1.55):
    u = clamp01(u); v = u - 1.0
    return 1.0 + (s + 1.0) * v * v * v + s * v * v

# ------------------------------------------------------------------ colour
def _c(v):
    return np.array(v, np.float32) / 255.0

BG     = _c(TL.BG)
PANEL  = _c(TL.PANEL)
CREAM  = _c(TL.CREAM)
GREY   = _c(TL.GREY)
DIM    = _c(TL.DIM)
ORANGE = _c(TL.ORANGE)
HOT    = _c(TL.HOT)
WHITE  = np.array([1.0, 1.0, 1.0], np.float32)

def mix(a, b, u):
    u = clamp01(u)
    return a * (1.0 - u) + b * u

# ------------------------------------------------------------------ gaussian (no scipy)
def _box1d(a, r, axis):
    n = a.shape[axis]
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, r)
    ap = np.pad(a, pad, mode="edge")
    cs = np.cumsum(ap, axis=axis, dtype=np.float32)
    zs = list(cs.shape); zs[axis] = 1
    cs = np.concatenate([np.zeros(zs, np.float32), cs], axis=axis)
    lo = [slice(None)] * a.ndim; lo[axis] = slice(0, n)
    hi = [slice(None)] * a.ndim; hi[axis] = slice(2 * r + 1, 2 * r + 1 + n)
    return (cs[tuple(hi)] - cs[tuple(lo)]) * (1.0 / (2 * r + 1))

def blur(a, sigma):
    """3 box passes ~ gaussian."""
    if sigma < 0.55:
        return a
    w = math.sqrt(12.0 * sigma * sigma / 3.0 + 1.0)
    r = max(1, int(round((w - 1.0) * 0.5)))
    for _ in range(3):
        a = _box1d(a, r, 0)
        a = _box1d(a, r, 1)
    return a

def down4(a):
    h, w = a.shape[:2]
    if a.ndim == 3:
        return a.reshape(h // 4, 4, w // 4, 4, a.shape[2]).mean((1, 3), dtype=np.float32)
    return a.reshape(h // 4, 4, w // 4, 4).mean((1, 3), dtype=np.float32)

def up4(a, W0, H0, mode="F"):
    """bilinear upsample by 4 through PIL (fast, C)."""
    oh, ow = H0, W0
    if a.ndim == 3:
        ch = [np.asarray(Image.fromarray(np.ascontiguousarray(a[..., i]), "F")
                         .resize((ow, oh), Image.BILINEAR)) for i in range(a.shape[2])]
        return np.stack(ch, axis=-1)
    return np.asarray(Image.fromarray(np.ascontiguousarray(a), "F").resize((ow, oh), Image.BILINEAR))

# ------------------------------------------------------------------ glyphs
_CACHE = {}

def _font(key, px):
    f = _CACHE.get((key, px))
    if f is None:
        f = ImageFont.truetype(TL.FONTS[key], px, index=TL.FONT_INDEX[key])
        _CACHE[(key, px)] = f
    return f

@functools.lru_cache(maxsize=384)
def text_ink(text, key, size, track_q, kern):
    """Tight glyph mask + placement offsets.

    Returns (mask f32 (h,w), ox, oy, bounds)
      ox, oy : offset of mask top-left from (pen_x, baseline_y), in 1x px
      bounds : k+1 normalised x boundaries of each character inside the mask
    """
    track = track_q / 100.0
    s2 = int(round(size * SS))
    f = _font(key, s2)
    asc, desc = f.getmetrics()
    PAD = 8
    if kern or track == 0.0:
        adv = f.getlength(text)
        total = adv
        im = Image.new("L", (int(math.ceil(total)) + 2 * PAD, asc + desc + 2 * PAD), 0)
        ImageDraw.Draw(im).text((PAD, PAD), text, font=f, fill=255)
        cuts = [PAD + f.getlength(text[:i]) for i in range(len(text) + 1)]
    else:
        advs = [f.getlength(c) for c in text]
        total = sum(advs) + track * s2 * (len(text) - 1)
        im = Image.new("L", (int(math.ceil(total)) + 2 * PAD, asc + desc + 2 * PAD), 0)
        d = ImageDraw.Draw(im)
        x = float(PAD)
        cuts = [x]
        for c, a in zip(text, advs):
            d.text((x, PAD), c, font=f, fill=255)
            x += a + track * s2
            cuts.append(x)
    bb = im.getbbox()
    if bb is None:
        return (np.zeros((1, 1), np.float32), 0.0, 0.0, (0.0, 1.0))
    im = im.crop(bb)
    tw = max(1, int(round(im.width / SS)))
    th = max(1, int(round(im.height / SS)))
    im = im.resize((tw, th), Image.LANCZOS)
    m = np.asarray(im, np.float32) * (1.0 / 255.0)
    ox = (bb[0] - PAD) / SS
    oy = (bb[1] - PAD - asc) / SS
    bounds = tuple((c - bb[0]) / SS for c in cuts)
    return (m, ox, oy, bounds)

def vblur(mask, r):
    if r < 0.5:
        return mask
    return _box1d(mask, max(1, int(round(r))), 0)

def scale_mask(mask, s):
    if abs(s - 1.0) < 0.004:
        return mask
    h, w = mask.shape
    im = Image.fromarray(mask, "F").resize((max(1, int(round(w * s))), max(1, int(round(h * s)))),
                                           Image.BILINEAR)
    return np.asarray(im, np.float32)

# ------------------------------------------------------------------ blending
def blit(img, mask, x, y, color, alpha=1.0, clip=None):
    """additive light-on-dark blit, clamped. x,y = top-left (float)."""
    if alpha <= 0.002:
        return
    h, w = mask.shape
    H0, W0 = img.shape[:2]
    x0 = int(math.floor(x)); y0 = int(math.floor(y))
    x1 = x0 + w; y1 = y0 + h
    sx0 = max(0, -x0); sy0 = max(0, -y0)
    dx0 = max(0, x0); dy0 = max(0, y0)
    dx1 = min(W0, x1); dy1 = min(H0, y1)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    sub = mask[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)]
    c = sub * alpha
    if clip is not None:
        c = c * clip[dy0:dy1, dx0:dx1]
    dst = img[dy0:dy1, dx0:dx1]
    dst += c[..., None] * color

def blit_cols(img, mask, x, y, color, colmul, clip=None):
    """blit with a per-column multiplier (staggered reveal)."""
    h, w = mask.shape
    cc = np.ascontiguousarray(colmul, np.float32)
    if cc.shape[0] != w:
        xs = np.linspace(0.0, w - 1.0, w)
        cc = np.interp(xs, np.linspace(0.0, cc.shape[0] - 1.0, cc.shape[0]), cc).astype(np.float32)
    blit(img, mask * cc[None, :], x, y, color, 1.0, clip)

def rect_add(img, x0, x1, y0, y1, color, gain=1.0, clip=None):
    """exact analytic coverage rect, additive."""
    H0, W0 = img.shape[:2]
    ix0 = int(math.floor(x0)); ix1 = int(math.ceil(x1))
    iy0 = int(math.floor(y0)); iy1 = int(math.ceil(y1))
    ix0 = max(0, ix0); iy0 = max(0, iy0)
    ix1 = min(W0, ix1); iy1 = min(H0, iy1)
    if ix1 <= ix0 or iy1 <= iy0 or gain <= 0.0:
        return
    X = np.arange(ix0, ix1, dtype=np.float32) + 0.5
    Y = np.arange(iy0, iy1, dtype=np.float32) + 0.5
    cx = np.clip(np.minimum(X, x1) - np.maximum(X - 1.0, x0), 0.0, 1.0)
    cy = np.clip(np.minimum(Y, y1) - np.maximum(Y - 1.0, y0), 0.0, 1.0)
    cov = np.outer(cy, cx) * gain
    if clip is not None:
        cov = cov * clip[iy0:iy1, ix0:ix1]
    img[iy0:iy1, ix0:ix1] += cov[..., None] * color

def dot_add(img, cx, cy, r, color, gain=1.0, clip=None):
    rect_add(img, cx - r, cx + r, cy - r, cy + r, color, gain, clip)

# ------------------------------------------------------------------ fields
GRID_X = None
GRID_Y = None
def grids():
    global GRID_X, GRID_Y
    if GRID_X is None:
        GRID_X = (np.arange(W, dtype=np.float32) + 0.5)[None, :]
        GRID_Y = (np.arange(H, dtype=np.float32) + 0.5)[:, None]
    return GRID_X, GRID_Y

def ring_add(img, cx, cy, R, thick, color, gain=1.0, clip=None):
    """expanding ring, analytic AA. bbox limited to on-screen."""
    X, Y = grids()
    r0 = R - thick * 0.5; r1 = R + thick * 0.5
    if r1 <= 0:
        return
    x0 = max(0, int(cx - r1 - 2)); x1 = min(W, int(cx + r1 + 3))
    y0 = max(0, int(cy - r1 - 2)); y1 = min(H, int(cy + r1 + 3))
    if x1 <= x0 or y1 <= y0:
        return
    dx = X[0:1, x0:x1] - cx; dy = Y[y0:y1, 0:1] - cy
    d = np.sqrt(dx * dx + dy * dy)
    cov = np.clip(r1 - d + 0.5, 0.0, 1.0) * np.clip(d - r0 + 0.5, 0.0, 1.0)
    cov *= gain
    if clip is not None:
        cov = cov * clip[y0:y1, x0:x1]
    img[y0:y1, x0:x1] += cov[..., None] * color

def disc_mask(cx, cy, R, soft=1.5):
    """full-frame soft disc coverage (0..1)."""
    X, Y = grids()
    d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    return np.clip((R - d) / soft + 0.5, 0.0, 1.0).astype(np.float32)

def halo64(img, cx, cy, R, color, gain, duty=0.035, len_in=0.0, len_out=26.0):
    """64-point halo around a ring circumference."""
    if R < 6 or gain <= 0.0:
        return
    for k in range(64):
        a = 2.0 * math.pi * k / 64.0
        ca, sa = math.cos(a), math.sin(a)
        px, py = cx + ca * R, cy + sa * R
        if not (-80 < px < W + 80 and -80 < py < H + 80):
            continue
        for j in range(3):
            q = j * 0.55
            rect_add(img, px + ca * (len_in + q) - 1.0, px + ca * (len_in + q) + 1.0,
                     py + sa * (len_in + q) - 1.0, py + sa * (len_in + q) + 1.0,
                     color, gain * (1.0 - 0.26 * j))

SW, SH = W // 4, H // 4
def particles_add(img, xs, ys, wts, color, soft=1.0):
    """additive dust accumulated at 1/4 res then bilinear-upsampled (soft glow dots)."""
    n = xs.shape[0]
    if n == 0:
        return
    ix = np.clip((xs * 0.25).astype(np.int32), 0, SW - 1)
    iy = np.clip((ys * 0.25).astype(np.int32), 0, SH - 1)
    w = np.full(n, float(wts), np.float32) if np.ndim(wts) == 0 else wts.astype(np.float32)
    acc = np.bincount(iy * SW + ix, weights=w, minlength=SW * SH).astype(np.float32)
    acc = acc.reshape(SH, SW)
    if soft > 0:
        acc = blur(acc, soft)
    img += up4(acc, W, H)[..., None] * color

def radial_flash(img, cx, cy, amt, sigma=950.0):
    """explosive burst: bright core falling off, not a flat wash."""
    if amt <= 0.002:
        return
    X, Y = grids()
    d2 = ((X[0, 0] if False else (X - cx) / sigma) ** 2) + ((Y - cy) / sigma) ** 2
    g = np.exp(-d2 * 0.5).astype(np.float32)
    img += (g * amt)[..., None]

def blob_add(img, cx, cy, rad, color, gain=1.0):
    """soft radial light. rad = ~2 sigma."""
    H0, W0 = img.shape[:2]
    x0 = max(0, int(cx - rad * 2)); x1 = min(W0, int(cx + rad * 2) + 1)
    y0 = max(0, int(cy - rad * 2)); y1 = min(H0, int(cy + rad * 2) + 1)
    if x1 <= x0 or y1 <= y0 or gain <= 0.0:
        return
    X, Y = grids()
    d2 = (X[0:1, x0:x1] - cx) ** 2 + (Y[y0:y1, 0:1] - cy) ** 2
    g = np.exp(-d2 * (0.5 / (rad * rad))).astype(np.float32)
    img[y0:y1, x0:x1] += (g * gain)[..., None] * color

# ------------------------------------------------------------------ post stack
_VIG = None
_GRAIN = None
def _init_post():
    global _VIG, _GRAIN
    if _VIG is not None:
        return
    X, Y = grids()
    xx = (X - W * 0.5) / (W * 0.5)
    yy = (Y - H * 0.5) / (H * 0.5)
    r = np.sqrt(xx * xx + yy * yy)
    v = 1.0 - 0.45 * smooth((r - 0.35) / 0.95)
    _VIG = np.clip(v, 0.55, 1.0).astype(np.float32)[..., None]
    rs = np.random.RandomState(20260701)
    _GRAIN = []
    for _ in range(5):
        g = rs.normal(0.0, 2.2 / 255.0, (H, W)).astype(np.float32)
        _GRAIN.append(g[..., None])

GLOW_K = 0.26
GLOW_KNEE = 0.150
def post(img, f):
    """glow -> vignette -> grain -> shake + chromatic aberration."""
    _init_post()
    # 1. glow at 1/4 res, dual gaussian, soft knee so the ground never blooms
    small = down4(img)
    small = np.maximum(small - GLOW_KNEE, 0.0)
    g1 = blur(small, 2.2)
    g2 = blur(small, 7.0)
    gl = up4((g1 * 0.45 + g2 * 0.62).astype(np.float32), W, H)
    img += gl * GLOW_K
    # 2. vignette
    img *= _VIG
    # 3. grain
    img += _GRAIN[f % 5]
    return img

def shake_chroma(img, t, amp, chroma):
    """whole-frame shake (px) + RGB channel displacement (px). edge-clamped."""
    if amp < 0.35 and chroma < 0.35:
        return img
    sx, sy = shake_offsets(amp, t)
    return _shift3(img, sx, sy, chroma)

def shake_offsets(amp, t):
    """34 Hz jitter (aliases to a stable per-frame sequence) riding a slow camera drift."""
    a = 2.0 * math.pi * 34.0 * t
    dx = (0.42 * math.sin(a) + 0.16 * math.sin(1.7 * a + 1.1)
          + 0.30 * math.sin(2.0 * math.pi * 1.7 * t + 0.4)
          + 0.12 * math.sin(2.0 * math.pi * 0.63 * t + 2.4))
    dy = (0.42 * math.cos(0.9 * a + 0.7) + 0.16 * math.sin(1.3 * a + 2.3)
          + 0.30 * math.cos(2.0 * math.pi * 1.13 * t + 1.9)
          + 0.12 * math.sin(2.0 * math.pi * 0.41 * t + 0.2))
    n = max(1e-6, math.hypot(dx, dy))
    return dx / n * amp, dy / n * amp

CA_R = 1100.0
def _lateral_ca(a, amount):
    """lens dispersion: R and B scaled about the frame centre - 0 px on axis,
    amount px at radius CA_R.  Keeps the centre of the frame clean."""
    s = float(amount) / CA_R
    out = a.copy()
    for ch, k in ((0, s), (2, -s)):
        w2 = max(2, int(round(W * (1.0 + k))))
        h2 = max(2, int(round(H * (1.0 + k))))
        im = Image.fromarray(np.ascontiguousarray(a[..., ch]), "F").resize((w2, h2), Image.BILINEAR)
        arr = np.asarray(im, np.float32)
        if w2 >= W and h2 >= H:
            x0 = (w2 - W) // 2; y0 = (h2 - H) // 2
            arr = arr[y0:y0 + H, x0:x0 + W]
        else:
            px0 = (W - w2) // 2; py0 = (H - h2) // 2
            arr = np.pad(arr, ((py0, H - h2 - py0), (px0, W - w2 - px0)), mode="edge")
        out[..., ch] = arr[:H, :W]
    return out

def _shift3(img, sx, sy, chroma):
    m = int(math.ceil(max(abs(sx), abs(sy)))) + 2
    pad = np.pad(img, ((m, m), (m, m), (0, 0)), mode="edge")
    oy = m + int(round(sy)); ox = m + int(round(sx))
    out = np.ascontiguousarray(pad[oy:oy + H, ox:ox + W, :])
    if chroma >= 0.5:
        out = _lateral_ca(out, chroma)
    return out

def new_frame():
    img = np.empty((H, W, 3), np.float32)
    img[:] = BG
    return img

def finish(img):
    np.clip(img, 0.0, 1.0, out=img)
    return (img * 255.0 + 0.5).astype(np.uint8)

TO_8 = None
