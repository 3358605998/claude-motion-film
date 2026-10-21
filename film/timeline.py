# -*- coding: utf-8 -*-
"""timeline.py - THE single cue sheet. Picture and audio BOTH import this.
120 BPM: beat = 0.5s, bar = 2.0s, 8 bars = 16.000s = 480 frames @30fps.
Every number below is authoritative. Do not retime here; retime in the scene/audio code
only if you must, and then update BOTH consumers.
"""

TITLE   = "claude-motion-film"
DUR     = 16.0
FPS     = 30
NFRAMES = int(DUR * FPS)          # 480
W, H    = 1920, 1080

BPM  = 120.0
BEAT = 60.0 / BPM                 # 0.500
BAR  = BEAT * 4                   # 2.000
NBARS = 8

# ------------------------------------------------------------------ B1  蓄力 (0.00-2.00)
B1_PULSE      = [0.25, 0.75, 1.25, 1.75]
B1_L1_IN      = 0.85
B1_VACUUM     = (1.80, 2.00)

# ------------------------------------------------------------------ B2  爆发 (2.00-4.00)
B2_HIT        = 2.00
B2_DOUBLE     = [2.00 + 0.25 * k for k in range(8)]
B2_L2_IN      = 2.40
B2_L2_OUT     = 3.90

# ------------------------------------------------------------------ B3  900 帧 (4.00-6.00)
B3_HIT        = 4.00
B3_WINDOW     = 4.00
B3_RAMP_END   = 4.75
B3_TICKS      = [4.00 + 0.25 * k for k in range(1, 9)]
B3_L3_IN      = 4.55
B3_L3_OUT     = 5.98

# ------------------------------------------------------------------ B4  白闪塌缩 (6.00-8.00)
B4_HIT        = 6.00
B4_COLLAPSE   = (6.00, 6.18)
B4_VACUUM     = (6.02, 6.42)
B4_L4_IN      = 6.60
B4_HOLD_END   = 8.00

# ------------------------------------------------------------------ B5  爆裂 + 引力流 (8.00-12.00)
B5_HIT        = 8.00
B5_L5_IN      = 8.25
B5_L5_OUT     = 11.98
B5_FLOW_END   = 12.00

# ------------------------------------------------------------------ B6  聚合 + 落版 (12.00-16.00)
B6_HIT        = 12.00
B6_AGG_END    = 12.85             # last particle lands (agg 0.75 + delay 0.10)
B6_FLASH      = 326.0 / 30.0 + 2.00 * 0           # replaced below, kept for reference
B6_FLASH      = 385.0 / 30.0      # 12.8333 s = 12s25f = frame 385, the first frame the
                                  # swarm is fully assembled. PEAK of the white hit.
B6_BRAND_IN   = B6_FLASH          # real type appears ON the peak frame, no animation
B6_CTA_IN     = 13.24
B6_UNDER_OUT  = 15.70
B6_FINAL_HIT  = 15.55
B6_END        = 16.00

# ------------------------------------------------------------------ copy (verbatim)
COPY = [
    ("L1", "一句话。",     B1_L1_IN,  B2_HIT,        3.5),
    ("L2", "一支片。",     B2_L2_IN,  B2_L2_OUT,     2.7),
    ("L3", "900 帧。",     B3_L3_IN,  B3_L3_OUT,     4.1),
    ("L4", "一条线。",     B4_L4_IN,  B5_HIT,        2.9),
    ("L5", "任何主题。",   B5_L5_IN,  B5_L5_OUT,     2.9),
    ("CTA", "装上它。",    B6_CTA_IN, B6_END,        2.9),
]

# ------------------------------------------------------------------ audio events
AUDIO_HITS = [
    (B2_HIT,  "impact_big"),
    (B3_HIT,  "impact_mid"),
    (B4_HIT,  "impact_huge"),
    (B5_HIT,  "impact_mid"),
    (B6_HIT,  "impact_mid"),
    (B6_FINAL_HIT, "impact_big"),
]
AUDIO_TICKS   = B3_TICKS + B2_DOUBLE[1:] + [B1_PULSE[0]] + B1_PULSE[1:]
AUDIO_SILENCE = [B1_VACUUM, B4_VACUUM, (15.36, 15.55)]

# ------------------------------------------------------------------ colour tokens
BG      = (20, 20, 19)
PANEL   = (31, 31, 29)
CREAM   = (240, 238, 230)
GREY    = (176, 174, 165)
DIM     = (104, 103, 96)
ORANGE  = (217, 119, 87)
HOT     = (255, 168, 128)
GREEN   = (122, 196, 120)
RED     = (236, 84, 80)
BLUE    = (106, 155, 204)
AMBER   = (232, 178, 90)

# ------------------------------------------------------------------ fonts (Windows)
FONTS = {
    "cjk":    r"C:\Windows\Fonts\msyhbd.ttc",
    "cjk_r":  r"C:\Windows\Fonts\msyh.ttc",
    "mono":   r"C:\Windows\Fonts\consolab.ttf",
    "latin":  r"C:\Windows\Fonts\bahnschrift.ttf",
    "serif":  r"C:\Windows\Fonts\georgiai.ttf",
}
FONT_INDEX = {"cjk": 0, "cjk_r": 0, "mono": 0, "latin": 0, "serif": 0}
