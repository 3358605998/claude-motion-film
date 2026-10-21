# -*- coding: utf-8 -*-
"""render.py - the driver: scenes.render(f) -> rawvideo pipe -> ffmpeg.

    python render.py frame 78                 one PNG at out/frame_0078.png
    python render.py seg 120 179              frames a..b (inclusive) -> out/seg_0120_0179.mp4
    python render.py contact 0,4,8,...        contact sheets, 30 cells each, timecode burned in
    python render.py all [--chunked]          the film -> out/video_silent.mp4

Twelve workers render, but frames are written to the encoder STRICTLY in frame
order (Pool.imap preserves submission order, and the parent is the only writer),
so the pipe sees f0000, f0001, ... however the pool happens to finish.

--chunked splits the film into 60-frame segments under out/chunks/ and concats
them losslessly; segments already on disk are reused, so re-rendering one
segment in the middle means deleting one file and running 'all --chunked' again.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import timeline as TL

OUT = os.path.join(HERE, "out")
CHUNKS = os.path.join(OUT, "chunks")
W, H, FPS, NFRAMES = TL.W, TL.H, TL.FPS, TL.NFRAMES
JOBS = 12
CHUNK = 60
FRAME_BYTES = W * H * 3

X264 = ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]

# ------------------------------------------------------------------ work units
def _render_bytes(f):
    """Worker entry point: one frame, raw RGB24, C order."""
    import scenes
    return scenes.render(f).tobytes()


def _ensure(path):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def _ffmpeg_in(path):
    return (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
             "-r", str(FPS), "-i", "-"] + X264 + ["-movflags", "+faststart", path])


# ------------------------------------------------------------------ encoder
def encode(frames, path, jobs=JOBS, label=""):
    """Render frames through the pool, stream them to ffmpeg in order, report velocity."""
    _ensure(path)
    n = len(frames)
    cmd = _ffmpeg_in(path)
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    worked = 0
    try:
        with Pool(jobs) as pool:
            for i, buf in enumerate(pool.imap(_render_bytes, frames, chunksize=1)):
                proc.stdin.write(buf)
                worked = i + 1
                if worked % 30 == 0 or worked == n:
                    el = time.time() - t0
                    rate = worked / max(el, 1e-6)
                    print("  %-9s %4d/%d  %6.1fs  %5.2f f/s  eta %5.1fs"
                          % (label, worked, n, el, rate, (n - worked) / max(rate, 1e-6)),
                          flush=True)
    except BaseException:
        proc.stdin.close()
        proc.kill()
        raise
    proc.stdin.close()
    rc = proc.wait()
    dt = time.time() - t0
    if rc != 0:
        raise SystemExit("ffmpeg exited %d for %s" % (rc, path))
    print("  %-9s done  %d frames  %.1fs  (%.3f s/frame wall, %.3f s/frame cpu)"
          % (label, n, dt, dt / max(n, 1), dt * jobs / max(n, 1)), flush=True)
    return dt


def probe_frames(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-count_frames", "-show_entries",
                          "stream=nb_read_frames,width,height,r_frame_rate",
                          "-of", "default=nw=1", path],
                         capture_output=True, text=True).stdout
    d = dict(l.split("=", 1) for l in out.strip().splitlines() if "=" in l)
    d["nb_read_frames"] = int(d.get("nb_read_frames", 0))
    for k in ("width", "height"):
        d[k] = int(d.get(k, 0))
    return d


# ------------------------------------------------------------------ modes
def do_frame(fs):
    from PIL import Image
    import scenes
    for f in fs:
        t0 = time.time()
        im = scenes.render(f)
        p = os.path.join(OUT, "frame_%04d.png" % f)
        _ensure(p)
        Image.fromarray(im).save(p)
        print("  frame %04d  t=%.3fs  %.3fs  -> %s" % (f, f / FPS, time.time() - t0, p))


def do_seg(a, b, path=None):
    frames = list(range(a, b + 1))
    path = path or os.path.join(OUT, "seg_%04d_%04d.mp4" % (a, b))
    encode(frames, path, label="seg%04d" % a)
    pr = probe_frames(path)
    print("  -> %s  %d frames  %dx%d  %s fps"
          % (path, pr["nb_read_frames"], pr["width"], pr["height"], pr["r_frame_rate"]))


def do_contact(frames, cells=30, cols=5, cw=384, ch=216, tag="contact"):
    """Render the given frames, cut them into 5x6 sheets with the timecode burned in."""
    from PIL import Image, ImageDraw, ImageFont
    frames = frames[:]
    rows = (cells + cols - 1) // cols
    font = ImageFont.truetype(TL.FONTS["mono"], 21)
    shots = {}
    t0 = time.time()
    with Pool(JOBS) as pool:
        for i, buf in enumerate(pool.imap(_render_bytes, frames, chunksize=1)):
            # shrink immediately: a full frame is 6.2 MB and 90 of them is not a sheet
            shots[frames[i]] = Image.frombytes("RGB", (W, H), buf).resize((cw, ch), Image.LANCZOS)
            if (i + 1) % 30 == 0 or i + 1 == len(frames):
                print("  contact  %3d/%d  %.1fs" % (i + 1, len(frames), time.time() - t0),
                      flush=True)
    made = []
    for s in range(0, len(frames), cells):
        group = frames[s:s + cells]
        sheet = Image.new("RGB", (cols * cw, rows * ch), (10, 10, 9))
        d = ImageDraw.Draw(sheet)
        for i, f in enumerate(group):
            x, y = (i % cols) * cw, (i // cols) * ch
            sheet.paste(shots[f], (x, y))
            lab = "T %02d:%02d.%03d  f%04d" % (int(f // FPS) // 60, int(f // FPS) % 60,
                                               int(round((f / FPS % 1.0) * 1000)), f)
            d.rectangle([x, y, x + 214, y + 27], fill=(20, 20, 19))
            d.text((x + 7, y + 3), lab, font=font, fill=(240, 238, 230))
            d.rectangle([x, y, x + cw - 1, y + ch - 1], outline=(58, 58, 54))
        p = os.path.join(OUT, "%s_%02d.png" % (tag, len(made) + 1))
        sheet.save(p)
        made.append(p)
        print("  sheet %s  %d cells  %dx%d" % (p, len(group), sheet.width, sheet.height))
    return made


def do_all(chunked=False, jobs=JOBS):
    path = os.path.join(OUT, "video_silent.mp4")
    _ensure(path)
    t0 = time.time()
    if not chunked:
        encode(list(range(NFRAMES)), path, jobs=jobs, label="film")
    else:
        parts, todo = [], []
        for a in range(0, NFRAMES, CHUNK):
            b = min(NFRAMES, a + CHUNK) - 1
            p = os.path.join(CHUNKS, "c%04d_%04d.mp4" % (a, b))
            parts.append(p)
            if not os.path.exists(p):
                todo.append((a, b, p))
        for a, b, p in todo:
            encode(list(range(a, b + 1)), p, jobs=jobs, label="%04d" % a)
        lst = os.path.join(CHUNKS, "list.txt")
        with open(lst, "w", encoding="utf-8") as fh:
            for p in parts:
                fh.write("file '%s'\n" % p.replace("\\", "/"))
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        "-movflags", "+faststart", path], check=True)
    pr = probe_frames(path)
    print("  -> %s  %d frames  %dx%d  %s  (total %.1fs)"
          % (path, pr["nb_read_frames"], pr["width"], pr["height"],
             pr["r_frame_rate"], time.time() - t0))
    if pr["nb_read_frames"] != NFRAMES:
        raise SystemExit("frame count %d != %d" % (pr["nb_read_frames"], NFRAMES))


def parse_frames(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    bad = [f for f in out if not (0 <= f < NFRAMES)]
    if bad:
        raise SystemExit("frame out of range 0..%d: %s" % (NFRAMES - 1, bad[:5]))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description="claude-motion-film renderer")
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("frame", help="render frames to PNG")
    p.add_argument("frames", nargs="+")
    p = sub.add_parser("seg", help="render a frame range to its own mp4")
    p.add_argument("a", type=int)
    p.add_argument("b", type=int)
    p.add_argument("--out", default=None)
    p = sub.add_parser("contact", help="render contact sheets (default 30 cells each)")
    p.add_argument("frames")
    p.add_argument("--cells", type=int, default=30)
    p.add_argument("--tag", default="contact")
    p = sub.add_parser("all", help="render the whole film")
    p.add_argument("--chunked", action="store_true")
    p.add_argument("--jobs", type=int, default=JOBS)
    a = ap.parse_args(argv)

    if a.mode == "frame":
        fs = []
        for s in a.frames:
            fs.extend(parse_frames(s))
        do_frame(fs)
    elif a.mode == "seg":
        if not (0 <= a.a <= a.b < NFRAMES):
            raise SystemExit("range must satisfy 0 <= a <= b <= %d" % (NFRAMES - 1))
        do_seg(a.a, a.b, a.out)
    elif a.mode == "contact":
        do_contact(parse_frames(a.frames), cells=a.cells, tag=a.tag)
    elif a.mode == "all":
        do_all(a.chunked, a.jobs)


if __name__ == "__main__":
    main(sys.argv[1:])
