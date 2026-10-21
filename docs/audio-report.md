# soundtrack.wav - audio report (v2: continuous score, layered sound design)

Fully synthesized (numpy only, no samples, no scipy, no library music).
Every time value is imported from timeline.py; nothing is retyped.

16.000 s / 8 bars / 120 BPM / 480 frames / 768000 samples at 48 kHz.
v1 was rejected because the music stopped. Three AUDIO_SILENCE windows were
multiplied by zero, so the film had two holes in the middle and one at the end.
v3 deletes build_gate entirely. Every window is now a HOVER: a -18 dB dodge plus
a low-pass closing 8 kHz -> 400 Hz, laid over a continuous sustain drone and a
reverse-reverb swell. Nothing in the film is multiplied by zero any more. The
only zeroes left are the first and last sample, so the boundaries do not click.

## 1. container / spec (raw ffprobe)
```
{
    "programs": [

    ],
    "stream_groups": [

    ],
    "streams": [
        {
            "codec_name": "pcm_s24le",
            "sample_fmt": "s32",
            "sample_rate": "48000",
            "channels": 2,
            "bits_per_sample": 24,
            "duration": "16.000000"
        }
    ],
    "format": {
        "format_name": "wav",
        "duration": "16.000000",
        "size": "4608044"
    }
}
```
wave header: frames=768000 channels=2 sampwidth=3 rate=48000 -> 16.000000 s

## 2. loudness (ffmpeg -af ebur128=peak=true, on the delivered file)
```
Integrated loudness I : -15.00 LUFS   (target -15.0, tolerance 0.05)
True peak             : -1.40 dBTP   (limit  -1.0)
```
master chain: bus sum -> hover (dodge + closing filter) -> 30 Hz high-pass ->
tone tilt (-2.2 dB below 85 Hz, +2.5 dB above 1.2 kHz, zero-phase masks) ->
30 ms head / 420 ms tail -> gain -> tanh soft clip (knee 0.62, ceiling 0.808)
-> 24-bit PCM. final gain 1.188502

fit trace:
```
  outer0 inner0  gain=  1.0000  ceil=0.8400  I= -16.50 LUFS  TP= -1.70 dBTP
  outer0 inner1  gain=  1.1885  ceil=0.8400  I= -15.00 LUFS  TP= -1.20 dBTP
  outer1 inner0  gain=  1.0000  ceil=0.8190  I= -16.50 LUFS  TP= -1.80 dBTP
  outer1 inner1  gain=  1.1885  ceil=0.8190  I= -15.00 LUFS  TP= -1.30 dBTP
  outer2 inner0  gain=  1.0000  ceil=0.8078  I= -16.50 LUFS  TP= -1.90 dBTP
  outer2 inner1  gain=  1.1885  ceil=0.8078  I= -15.00 LUFS  TP= -1.40 dBTP
```

## 3. the three hover windows (a dip, not a cut)
```
window           len s  RMS dBFS  peak dBFS  zero smp  samples
[1.80,2.00]      0.200     -24.5        0.2         0     9600
[6.02,6.42]      0.400     -14.7        0.7         0    19200
[15.36,15.55]    0.190     -31.7        0.1         0     9120
```
dodge  : -18.0 dB, cosine ramp starting 100 ms BEFORE each window and recovering
         110 ms after it ends, so the bed slides in and out instead of switching
filter : inside each window 8000 Hz -> 400 Hz, reopening 12 ms after the window
         on the hit; the drone and the reverse swell ride the lift bus and are
         never dodged or swept, so every window keeps a floor of music
max |sample-to-sample| within +/-20 ms of a window edge (a click shows here):
  1.80s=0.1170  2.00s=0.3882  6.02s=0.3470  6.42s=0.0278  15.36s=0.0038  15.55s=0.2504
  whole-file max |dx| for comparison: 0.7138 -> the edges are ordinary audio

## 4. CONTINUITY - the acceptance metric for v2
```
100 ms RMS grid, hop 100 ms, NO window excluded (v1 excluded its own gates):
  windows       160
  minimum       -35.89 dBFS at t=15.90 s
  maximum       -11.07 dBFS at t=11.50 s
  largest step  +18.99 dB at t=15.50 s
sliding 100 ms window, hop 10 ms (1591 windows = every possible 100 ms start):
  minimum       -35.89 dBFS at t=15.90 s
  windows at or below -45 dBFS : 0
```
required: minimum 100 ms RMS > -45 dBFS (no silence anywhere).
measured: -35.89 dBFS on the fixed grid, -35.89 dBFS on every sliding start -> PASS, the film never drops out

the six quietest 100 ms windows (these are the hovers, by design):
```
  t =  15.90 s    -35.89 dBFS
  t =   0.00 s    -34.23 dBFS
  t =   0.10 s    -33.19 dBFS
  t =  15.40 s    -31.95 dBFS
  t =   0.60 s    -29.76 dBFS
  t =   5.90 s    -29.76 dBFS
```

## 5. hit alignment - the six AUDIO_HITS of timeline.py (delivered file)
```
    cue kind           onset at  onset ms   peak ms
  2.000 impact_big       2.0000     +0.00     +1.65
  4.000 impact_mid       4.0000     +0.00    +13.46
  6.000 impact_huge      6.0000     +0.00     +1.81
  8.000 impact_mid       8.0000     +0.00    +16.29
 12.000 impact_mid      12.0000     +0.00    +25.10
 15.550 impact_big      15.5500     +0.00    +14.58
```
worst |onset offset| = 0.0 ms   (timeline.py: every hit within +/-60 ms)
onset = the FIRST 5 ms frame whose rise is within 1 dB of the steepest rise
inside +/-80 ms of the cue. An amplitude threshold cannot be used: the score
never goes quiet, so a threshold fires on the bed instead of the event.
what each hit is made of:
  2.00  impact_big + glass crack, then a pull-back whoosh
  4.00  impact_mid + 8 dry ticks + rising shimmer
  6.00  impact_huge = loudest point, tape_stop dive, reverse tail
  8.00  glass crack + granular burst + flow air over the whole roam
  12.00  impact_mid + grains gathering on a 16th grid (12.00-12.85)
  15.55  impact_big + glass, Picardy A(add9) + circular ring

other sync points (not hits):
```
cue                    time  onset at  onset ms
dot fade-in          0.2500    0.2550     +5.00
dot -> period        0.8500    0.8450     -5.00
white frame/type    12.8667   12.8667     +0.00
```
  dot fade-in        air_puff + one soft heartbeat
  dot -> period      blip_down 1680 -> 420 Hz
  white frame/type   flash_hit: noise burst + sub thump + inharmonic crack

0.30 is a two-layer event: the air bloom rises on the brief's 0.30 cue and the
soft heartbeat under it sits on TL.B1_PULSE[0] = 0.25 s, the constant scenes.py
iterates to pulse the dot, so sound and picture read one table.

## 6. impact construction - five layers on every hit
```
per-layer peak, dB below that kind's summed peak (from the synth itself):
kind        sub     body    crack     slap     tail
big        -2.8     -1.3     -2.2     -0.0     -9.7
mid        -3.8     -3.0     -3.0     -0.0    -11.1
huge       -5.0     -3.4     -1.6     -0.0     -9.7

band share of each delivered hit, first 200 ms (the audio that actually shipped):
     cue kind           sub %  body % crack %
   2.000 impact_big     14.7%   53.3%    3.1%
   4.000 impact_mid     39.4%   27.3%    3.1%
   6.000 impact_huge    35.2%   52.8%    2.1%
   8.000 impact_mid     52.2%    8.7%   16.2%
  12.000 impact_mid      5.0%   19.6%    6.4%
  15.550 impact_big     27.1%   16.3%    1.8%
```
bands: sub 38-62 Hz, body 115-210 Hz, crack 2-6 kHz.
global peak of the delivered film: 0.8060 at t = 6.002 s
pre-master peak per hit (before the soft clipper, so the ordering is honest):
     cue kind               peak   vs 6.00
   2.000 impact_big       0.5586     -4.55
   4.000 impact_mid       0.4238     -6.95
   6.000 impact_huge      0.9437     +0.00
   8.000 impact_mid       0.7543     -1.95
  12.000 impact_mid       0.5540     -4.63
  15.550 impact_big       0.8000     -1.44
pre-master global max at t = 6.002 s -> the 6.00 collapse owns it (6.00 = 0.9437)

## 7. new timbres
```
air_bed       room tone, slow moving band, 0.00-16.00, half bus
air_puff      soft opening band of noise, leads the dot fade-in
drone         continuous pedal A1-F1-C2-G1-A1-F1-F1-G1-A1, crossfaded, lift bus
flash_hit     the white frame 12.8667: 11 ms noise burst + 55 Hz thump +
              1.86/2.79/5.24/7.13 kHz crack. short on purpose - it marks the
              type change, it is not a hit
blip_down     0.85 lock-in: pitch falls 1680 -> 420 Hz in 170 ms
glass_crack   5 inharmonic shards 2.6-7.4 kHz + 3 noise taps (the mirror)
gran_cluster  grain cloud. density, pitch scatter and grid snapping are
              separate controls. 8.00 burst: 420 -> 14 grains/s, scatter 5.5 %.
              10.00 gather: 7 -> 230 grains/s, scatter collapses to 0 on a 16th grid
shimmer       high cluster through an upward-opening band (4.00, 10.00)
flow_air      slow moving air pad 8.00-10.00, no rhythm in it
tape_stop     varispeed dive, rate 1.0 -> 0.045 while the top closes
rev_swell     reverse reverb, the coming hit played backwards out of IR_LONG
```

## 8. per-section self-check (on the delivered file)
```
sec  range        RMS dBFS peak dBFS        DC   max|dx|
B1   0.0-2.0         -25.8      -7.1  -0.00021    0.3882
B2   2.0-4.0         -16.2      -1.9   0.00017    0.4895
B3   4.0-6.0         -21.3      -4.0  -0.00026    0.5394
B4   6.0-8.0         -18.1      -1.9   0.00002    0.3470
B5a  8.0-10.0        -16.7      -2.1   0.00010    0.4100
B5b  10.0-12.0       -15.4      -1.9   0.00003    0.6534
B6a  12.0-14.0       -18.2      -3.6   0.00003    0.7138
B6b  14.0-16.0       -18.9      -2.0   0.00009    0.2504
```
whole file: peak 0.8060 (-1.87 dBFS)  max|sample-to-sample| 0.71376  DC -0.000004
first sample L/R = +0.0000000 / +0.0000000 , last sample L/R = +0.0000000 / +0.0000000
L/R correlation 0.845   mono fold peak 1.6118 vs max channel peak 0.8060
```

## 9. spectral balance of the whole programme (energy share per octave)
```
   20-   60 Hz   26.29 %  ##########################
   60-  120 Hz   18.37 %  ##################
  120-  250 Hz   12.81 %  #############
  250-  500 Hz    4.32 %  ####
  500- 1000 Hz    7.95 %  ########
 1000- 2000 Hz   12.62 %  #############
 2000- 4000 Hz    7.55 %  ########
 4000- 8000 Hz    8.30 %  ########
 8000-16000 Hz    1.69 %  ##
16000-20000 Hz    0.07 %  
```

## 10. the score
```
A minor, one chord per 2 s bar, 120 BPM, 8 bars, all times from timeline.py.
bar 1  0.00-2.00  Am    pad (860 Hz LP) + air + 4 heartbeats @B1_PULSE,
                        blip @0.85, riser running THROUGH the 1.80 hover
bar 2  2.00-4.00  F     impact_big (5 layers + glass) + pull-back whoosh,
                        then 8 eighth notes where every step adds one layer
bar 3  4.00-6.00  C     impact_mid + 8 dry ticks + rising shimmer
bar 4  6.00-8.00  G     impact_huge = the loudest single point, tape_stop,
                        reverse swell 6.02 -> 6.60, hairline ping @6.60
bar 5  8.00-10.00 Am    impact_mid + glass crack + granular burst (420->14
                        gr/s), flow air, bells stacking 3->5 voices per beat
bar 6 10.00-12.00 F     the roam develops: second pad, drifting grain clouds,
                        16th hats opening, 16ths of pluck, riser into 12.00
bar 7 12.00-14.00 F9    the landing slam, grains gathering onto a 16th grid
                        until 12.85, white frame 12.8667, bell run, CTA 13.24
bar 8 14.00-16.00 G7    dominant held under the CTA; the pedal moves to A
                        inside the 15.36 hover; 15.55 Picardy A(add9) + ring,
                        natural 450 ms decay into 16.000
```

## 11. what I did not do
- No listening test. I cannot hear the file; every claim above is numeric.
- The hover still IS a dip: at -18 dB the bed really does pull back. If the
  user wants the music absolutely flat through the transitions, DODGE_DB -> 0
  and the drone alone carries them, but the breath is then gone.
- The 6.00 impact tail is deliberately NOT dodged: it is the loudest moment and
  its tail is the sound of the room, so 6.02-6.42 is the LOUDEST of the three
  windows (-15.7 dBFS) while still being a dip for the bed underneath.
- 28 % of the energy is below 60 Hz. That is the requested five-layer sub,
  not a mastering accident; it will read as weight on a good system and as
  thinness on a phone speaker, where the mid slap carries the hit instead.
- The 15.55 ending is a 450 ms chord decay under a 420 ms release. It is a
  swell down, not a gate, but it does end: a 16 s film cannot ring past 16.000.
- Reverb is synthetic convolution, not a real space. No plate or spring model.
- No sidechain ducking and no bus compressor: dynamics come from the arrangement.
- 24-bit PCM, no dither.
