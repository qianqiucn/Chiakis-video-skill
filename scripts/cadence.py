"""Measure limited-animation cadence: update rhythm, layer jumps, subject drift.

Run with python -X utf8; needs numpy, cv2, ffmpeg (on PATH or imageio-ffmpeg).
  cadence.py VIDEO START_S DUR_S [--track BOX]... [--subject BOX]... [options]
             [--ref VIDEO START_S DUR_S [--ref-track BOX]... [--ref-subject BOX]...]
BOX = X,Y,W,H[:FEATURE]: top-left and size as fractions 0-1, cut from the clip's
first frame. FEATURE = what is matched: bgr (default); gray; sat (255 - satur.:
white/grey/black subject on saturated colour); dark (255 - value: ink lines,
hair, shoes; ignores a light background's colour). --track = background element
(glyph, bar end); --subject = body part that costume cycles do not redraw (face,
shoes); both repeatable; --ref-* boxes belong to the --ref clip.
  --search HX,HY   track search half-size around the last confident place
                   (default 1,1 = whole frame; .05,1 = own column only)
  --subject-search HX,HY   same for subjects (default .1,.25)
  --min-score S    TM_CCOEFF_NORMED below S = lost (default .6)
  --reseed         tracks: when lost or ambiguous, cut a new template at the seed box
  --move PX (4) --smooth SEC (.5) --exclude X0,X1 (.42,.58) --strips A-B,.. (none)
  --snap DIR       DIR/<A|B>_<kind><n>.png: first frame and first 11 moves or
                   losses as previous | current crop; box green ok, yellow ?,
                   red lost (last known place). Look before trusting numbers.
Example: cadence.py ref.mp4 207 5 --search .05,1 --reseed --track .352,.431,.047,.097
Px are for a 1080-high frame (decoded 540 high); fK = clip frame K from 0.
1. Update cadence: 270-high gray diff > 24 outside --exclude; < 1% changed
   pixels = still pair (held drawing). Exposure N = a drawing shown N frames.
   Updates/s = changed pairs per s; "on N at 24 fps" = 24 / updates per s
   (30 fps with an update every 2.5 frames = 12/s = on twos at 24 fps).
2. Layers. Status ok; ? ambiguous (another peak beyond a quarter box within .1
   of the best); L lost; S seeded. A seed is refused if its per-channel std
   < 20 (flat: only noise would match) or another spot in its search area
   scores > .8 (repeated). Displacement only between ok/S frames of one
   template; move = |d| >= --move; hold before move = frames it stayed put
   first; direction by dominant axis, +y down; stagger = whether two tracks
   move on the same frames. Strips: phase correlation (response > .15), only
   for continuous scrolling; a hint says --track when updates break them.
3. Subject: same tracking + path range, slow path (moving mean over --smooth
   within one template), residual = position - slow path; residual RMS / P90
   = jitter; drift = slow-path change over the longest template run.
--ref adds "Compare" (A / B): updates/s, still-pair fraction, median background
move (tracks, else strips), median subject residual RMS.
Limits: a template follows an element only while it stays in frame and looks
alike; redrawn, tinted, scaled or exiting elements turn L (not wrong numbers),
so a subject redrawn every update gives few ok frames: use several boxes or
short clips. Keep boxes clear of glitch bars and lyrics, or they follow those.
Wrong peaks can still pass at scores .6-.8: check --snap. Precision ~2 px.
The bright-blob (HSV) subject center is gone: cycling costumes and other white
shapes drag a blob center, so its jitter measured the clothes, not the body.
"""
import argparse, glob, itertools, os, re, shutil, subprocess, sys

import cv2
import numpy as np

H = 540            # analysis height; printed px are scaled by 1080 / H
AMBIGUOUS = 0.1    # another peak within this of the best marks a match "?"
UNIQUE = 0.8       # a seed is refused if another spot in its search area scores above this
CONTRAST = 20      # a seed needs this per-channel std (0-255); flatter patches only match noise
SNAPS = 12         # rows per --snap sheet
GOOD = ("ok", "S")
FEATURES = {"bgr": lambda f: f, "gray": lambda f: cv2.cvtColor(f, cv2.COLOR_BGR2GRAY),
            "sat": lambda f: 255 - cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[..., 1],
            "dark": lambda f: 255 - cv2.cvtColor(f, cv2.COLOR_BGR2HSV)[..., 2]}


def fractions(text, counts=(2,)):
    values = tuple(map(float, text.split(",")))
    if len(values) not in counts or not all(0 <= v <= 1 for v in values):
        raise argparse.ArgumentTypeError(f"expected {counts} fractions in [0,1]: {text}")
    return values


def box_spec(text):
    coords, _, feature = text.partition(":")
    x, y, w, h = fractions(coords, (4,))
    if feature not in ("", *FEATURES) or w <= 0 or h <= 0 or x + w > 1 or y + h > 1:
        raise argparse.ArgumentTypeError(f"box must lie inside the frame, feature one of {list(FEATURES)}: {text}")
    return x, y, w, h, feature or "bgr"


def stats(values, fmt=".1f"):
    return f"median {np.median(values):{fmt}}, range {min(values):{fmt}}..{max(values):{fmt}}, n={len(values)}" if len(values) else "n/a"


def histogram(values):
    return " ".join(f"{k}{'+' if k == 4 else ''}:{sum(v == k if k < 4 else v >= 4 for v in values)}" for k in (1, 2, 3, 4))


def holds(moved, valid):
    """Frames each position was shown before the next move; the hold must start in view."""
    lengths, quiet = [], None
    for ok, move in zip(valid, moved):
        if ok and move and quiet is not None:
            lengths.append(quiet + 1)
        quiet = None if not ok else 0 if move else None if quiet is None else quiet + 1
    return lengths


def decode(ffmpeg, video, start, duration, width):
    command = [ffmpeg, "-v", "error", "-ss", str(start), "-i", video, "-t", str(duration), "-map", "0:v:0", "-an",
               "-vf", f"scale={width}:{H}", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        while len(raw := process.stdout.read(width * H * 3)) == width * H * 3:
            yield np.frombuffer(raw, np.uint8).reshape(H, width, 3)
        if process.wait():
            raise subprocess.CalledProcessError(process.returncode, command)


class Tracker:
    """Follow one box by template matching; positions are box centers in 1080p px."""

    def __init__(self, box, kind, width, search, opts):
        self.box, self.kind, self.width, self.search, self.opts = box, kind, width, search, opts
        w, h = max(6, round(box[2] * width)), max(6, round(box[3] * H))
        self.seed = (min(int(box[0] * width), width - w), min(int(box[1] * H), H - h), w, h)
        self.template, self.at, self.segment, self.refused = None, None, 0, 0
        self.pos, self.score, self.status, self.segments, self.snaps = [], [], [], [], []

    def grab(self, image):
        """Cut a template at the seed box unless it is flat or repeated in its search area."""
        x, y, w, h = self.seed
        old, self.template, self.at = (self.template, self.at), image[y:y + h, x:x + w].copy(), (float(x), float(y))
        if cv2.meanStdDev(self.template)[1].mean() < CONTRAST or self.match(image)[1] > UNIQUE:
            self.template, self.at, self.refused = *old, self.refused + 1
            return False
        self.segment += 1
        return True

    def match(self, image):
        """Return best score, best score beyond a quarter box, and the best top-left place."""
        (x, y), (w, h) = self.at, self.seed[2:]
        x0, y0 = max(0, int(x - self.search[0] * self.width)), max(0, int(y - self.search[1] * H))
        area = image[y0:int(y + h + self.search[1] * H) + 1, x0:int(x + w + self.search[0] * self.width) + 1]
        result = cv2.matchTemplate(area, self.template, cv2.TM_CCOEFF_NORMED)
        _, best, _, (px, py) = cv2.minMaxLoc(result)
        others = result.copy()
        others[max(0, py - h // 4):py + h // 4 + 1, max(0, px - w // 4):px + w // 4 + 1] = -1
        vertex = lambda v: float(np.clip(.5 * (v[0] - v[2]) / c, -.5, .5)) if (c := v[0] - 2 * v[1] + v[2]) < 0 else 0.
        dx = vertex(result[py, px - 1:px + 2]) if 0 < px < result.shape[1] - 1 else 0.   # sub-pixel parabola peak
        dy = vertex(result[py - 1:py + 2, px]) if 0 < py < result.shape[0] - 1 else 0.
        return best, float(others.max()), (x0 + px + dx, y0 + py + dy)

    def step(self, frame, previous):
        image, status, score, place = FEATURES[self.box[4]](frame), "L", np.nan, None
        if self.template is not None:
            score, second, place = self.match(image)
            if score >= self.opts.min_score:
                status = "?" if second > score - AMBIGUOUS else "ok"
                self.at = place if status == "ok" else self.at
        if status != "ok" and (not self.status or self.opts.reseed and self.kind == "track") and self.grab(image):
            status, place = "S", self.at
        self.pos.append(tuple((np.array(place) + np.divide(self.seed[2:], 2)) * 1080 / H) if status != "L" else (np.nan, np.nan))
        self.score.append(score), self.status.append(status), self.segments.append(self.segment)
        n = len(self.pos) - 1
        moved = n and status == "ok" and self.status[n - 1] in GOOD and self.segments[n - 1] == self.segment \
            and np.hypot(*np.subtract(self.pos[n], self.pos[n - 1])) >= self.opts.move
        if self.opts.snap and len(self.snaps) < SNAPS and (n == 0 or moved or status == "L" != self.status[n - 1]):
            self.snap((previous, frame), n)

    def snap(self, frames, n):
        """Same crop of previous | current frame around both box places, as one 600x270 row."""
        w, h = self.seed[2:]
        tops = {k: np.array(self.pos[k]) * H / 1080 - [w / 2, h / 2] if self.status[k] != "L" else np.array(self.at)
                for k in (n - 1, n) if k >= 0 and (self.status[k] != "L" or self.at is not None)}
        if tops:
            x0, y0 = np.maximum(np.min(list(tops.values()), axis=0) - [2 * w, 1.5 * h], 0).astype(int)
            x1, y1 = np.minimum(np.max(list(tops.values()), axis=0) + [3 * w, 2.5 * h], [self.width, H]).astype(int)
            scale, row = min(300 / (x1 - x0), 270 / (y1 - y0)), np.zeros((270, 600, 3), np.uint8)
            for side, (k, frame) in enumerate(zip((n - 1, n), frames)):
                if frame is not None and k >= 0:
                    tile = cv2.resize(frame[y0:y1, x0:x1], None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                    color, corner = {"L": (0, 0, 255), "?": (0, 255, 255)}.get(self.status[k], (0, 255, 0)), (tops[k] - [x0, y0]) * scale
                    cv2.rectangle(tile, tuple(int(v) for v in corner), tuple(int(v) for v in corner + [w * scale, h * scale]), color, 2)
                    cv2.putText(tile, f"f{k} {self.status[k]} {self.score[k]:.2f}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, .45, color, 1)
                    row[:tile.shape[0], 300 * side:300 * side + tile.shape[1]] = tile
            self.snaps.append(row)


def measure(ffmpeg, video, start, duration, tracks, subjects, strips, opts):
    info = subprocess.run([ffmpeg, "-hide_banner", "-i", video], capture_output=True, text=True, errors="replace").stderr
    size, rate = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", info), re.search(r"Video:.*?, ([\d.]+) fps", info)
    if not size or not rate or start < 0 or not duration > 0:
        raise ValueError(f"Cannot read video size/fps, or bad START_S/DUR_S: {video} @ {start}+{duration}")
    width, fps = round(int(size[1]) / int(size[2]) * H / 2) * 2, float(rate[1])
    trackers = ([Tracker(b, "track", width, opts.search, opts) for b in tracks]
                + [Tracker(b, "subject", width, opts.subject_search, opts) for b in subjects])
    regions = [(int(a * width), int(b * width)) for a, b in strips]
    mask = np.ones((H // 2, width // 2), bool)
    mask[:, int(opts.exclude[0] * width / 2):int(opts.exclude[1] * width / 2)] = False
    changes, flows, previous = [], [[] for _ in regions], None
    for frame in decode(ffmpeg, video, start, duration, width):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (width // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.int16)
        patches = [gray[:, a:b].astype(np.float32) - gray[:, a:b].mean() for a, b in regions]
        for tracker in trackers:
            tracker.step(frame, previous and previous[0])
        if previous is not None:
            changes.append((np.abs(small - previous[1])[mask] > 24).mean())
            for values, old, new in zip(flows, previous[2], patches):
                (dx, dy), response = cv2.phaseCorrelate(old, new)
                values.append((dx * 1080 / H, dy * 1080 / H, response))
        previous = frame, small, patches
    if not changes:
        raise ValueError(f"Need at least two decoded frames: {video} @ {start}+{duration}")
    return fps, np.array(changes), [np.array(f).reshape(-1, 3) for f in flows], trackers


def follow(t, update, fps, opts, lines):
    """Describe one tracker; return its move magnitudes, move/valid masks and residual RMS."""
    pos, seg, status, score = np.array(t.pos, float), np.array(t.segments), np.array(t.status), np.array(t.score, float)
    good = np.isin(status, GOOD)
    valid = good[:-1] & good[1:] & (seg[:-1] == seg[1:])
    d = np.diff(pos, axis=0)
    mag = np.hypot(d[:, 0], d[:, 1])
    moved = valid & (mag >= opts.move)
    count = {k: int((status == k).sum()) for k in ("ok", "?", "L", "S")}
    lines.append(f"{t.kind} {','.join(f'{v:g}' for v in t.box[:4])}:{t.box[4]}: ok {count['ok']}, ambiguous {count['?']}, "
                 f"lost {count['L']}, seeded {count['S']} (refused {t.refused}) of {len(status)} frames; "
                 f"ok score {stats(score[status == 'ok'], '.2f')}")
    (dx, dy), vertical = d[moved].T, np.abs(d[moved, 1]) >= np.abs(d[moved, 0])
    every = f" (one per {valid.sum() / moved.sum():.1f} valid pairs)" if moved.any() else ""
    lines.append(f"  valid pairs {valid.sum()}, moves {moved.sum()}{every}; |d| px {stats(mag[moved])}")
    lines.append(f"  hold before move, frames {stats(holds(moved, valid), '.0f')}; direction up {np.sum(vertical & (dy < 0))}"
                 f" down {np.sum(vertical & (dy > 0))} left {np.sum(~vertical & (dx < 0))} right {np.sum(~vertical & (dx > 0))}"
                 + (f"; median dx {np.median(dx):+.1f} dy {np.median(dy):+.1f}" if moved.any() else ""))
    rms = np.nan
    if t.kind == "subject" and good.sum() >= 2:
        lines.extend(f"  {axis} px {pos[good, i].min():.1f}..{pos[good, i].max():.1f} (span {np.ptp(pos[good, i]):.1f}, "
                     f"std {pos[good, i].std():.1f})" for i, axis in enumerate("xy"))
        window, slow = max(3, round(opts.smooth * fps) // 2 * 2 + 1), np.full_like(pos, np.nan)
        for s in np.unique(seg[good]):
            inside = good & (seg == s)
            weight = np.maximum(np.convolve(inside.astype(float), np.ones(window), "same"), 1)
            for i in (0, 1):
                slow[inside, i] = (np.convolve(np.where(inside, pos[:, i], 0), np.ones(window), "same") / weight)[inside]
        residual = np.hypot(*(pos - slow)[good].T)
        rms = float(np.sqrt(np.mean(residual ** 2)))
        run = np.flatnonzero(good & (seg == max(np.unique(seg[good]), key=lambda s: np.sum(good & (seg == s)))))
        drift, seconds = slow[run[-1]] - slow[run[0]], max(run[-1] - run[0], 1) / fps
        lines.append(f"  slow path ({window}-frame mean): drift {drift[0]:+.1f},{drift[1]:+.1f} px over {seconds:.2f} s "
                     f"({drift[0] / seconds:+.1f},{drift[1] / seconds:+.1f} px/s); residual jitter RMS {rms:.1f}, "
                     f"P90 {np.percentile(residual, 90):.1f}, max {residual.max():.1f}")
    entries = [f"f{k + 1}:{d[k, 0]:+.0f},{d[k, 1]:+.0f}/{score[k + 1]:.2f}" if valid[k]
               else f"f{k + 1}:{status[k + 1] if status[k + 1] != 'ok' else 'gap'}" for k in np.flatnonzero(update)]
    lines.append("  per update (fK:dx,dy/score; L lost, ? ambiguous, S seeded, gap = previous frame unusable):")
    lines.extend("    " + " ".join(entries[i:i + 8]) for i in range(0, len(entries), 8))
    return mag[moved], moved, valid, rms


def report(fps, change, flows, trackers, strips, opts):
    still = change < .01
    update = ~still
    exposure = holds(update, np.ones(len(still), bool))
    per_second = update.sum() / (len(change) / fps)
    blocks = [[f"{len(change) + 1} frames at {fps:g} fps; {len(change)} pairs; changed pixels mean {change.mean():.2%}, "
               f"on update pairs {change[update].mean() if update.any() else 0:.2%}; still pairs {still.mean():.2%}",
               f"Repeat runs (clip edges included): {histogram([len(list(g)) for flag, g in itertools.groupby(still) if flag])}"
               f"; complete exposures (1/2/3/4+): {histogram(exposure)}",
               f"Mean exposure {np.mean(exposure) if exposure else np.nan:.2f} frames; updates per second {per_second:.2f}"
               + (f" = on {24 / per_second:.2f}s at 24 fps" if per_second else ""),
               "First <=48 pairs, changed pixels %: " + " ".join(f"{v * 100:.0f}" for v in change[:48])], [], []]
    followed = [(t.kind == "track", *follow(t, update, fps, opts, blocks[1 if t.kind == "track" else 2])) for t in trackers]
    moves, strip_moves = [m for track, magnitudes, *_ in followed if track for m in magnitudes], []
    move_sets = [(moved, valid) for track, _, moved, valid, _ in followed if track]
    jitters = [rms for track, *_, rms in followed if not track and np.isfinite(rms)]
    for (i, (a, av)), (j, (b, bv)) in itertools.combinations(enumerate(move_sets, 1), 2):
        a, b = set(np.flatnonzero(a & av & bv)), set(np.flatnonzero(b & av & bv))
        timing = ("fully staggered" if not a & b else "same times" if a == b else "partly staggered") if a and b else "n/a"
        blocks[1].append(f"Tracks {i}/{j}: {timing}; shared {len(a & b)} of {len(a | b)} move frames (jointly valid pairs)")
    for k, (flow, strip) in enumerate(zip(flows, strips), 1):
        good, mag = flow[:, 2] > .15, np.hypot(flow[:, 0], flow[:, 1])
        moved, reliable = good & (mag >= opts.move), good[update].mean() if update.any() else 1.
        strip_moves.extend(mag[moved])
        blocks[1].append(f"Strip {k} x={strip[0]:g}..{strip[1]:g} (phase corr.): reliable {good.sum()}/{len(good)} pairs, "
                         f"{reliable:.0%} of update pairs; moves {moved.sum()}; |d| px {stats(mag[moved])}; median dy "
                         f"{f'{np.median(flow[moved, 1]):+.1f}' if moved.any() else 'n/a'}; hold {stats(holds(moved, good), '.0f')}")
        if reliable < .5:
            blocks[1].append(f"  Hint: strip {k} loses correlation on most updates, so the picture is replaced or jumps "
                             "out of the strip when it updates; measure layers with --track instead.")
    blocks[1], blocks[2] = blocks[1] or ["Skipped (no --track / --strips)"], blocks[2] or ["Skipped (no --subject)"]
    background = np.median(moves) if moves else np.median(strip_moves) if strip_moves else np.nan
    return blocks, [per_second, still.mean(), background, np.median(jitters) if jitters else np.nan]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video"), parser.add_argument("start_s", type=float), parser.add_argument("dur_s", type=float)
    parser.add_argument("--ref", nargs=3, metavar=("VIDEO", "START_S", "DUR_S")), parser.add_argument("--reseed", action="store_true")
    for name in ("track", "subject", "ref-track", "ref-subject"):
        parser.add_argument(f"--{name}", type=box_spec, action="append", default=[])
    for name, kind, default in (("search", fractions, (1., 1.)), ("subject-search", fractions, (.1, .25)),
                                ("min-score", float, .6), ("move", float, 4.), ("smooth", float, .5), ("snap", str, None),
                                ("exclude", fractions, (.42, .58)), ("strips", str, "0.08-0.23,0.78-0.96")):
        parser.add_argument(f"--{name}", type=kind, default=default)
    opts = parser.parse_args()
    strips = [] if opts.strips.lower() == "none" else [fractions(s.replace("-", ",")) for s in opts.strips.split(",")]
    if any(a >= b for a, b in strips) or opts.exclude[0] >= opts.exclude[1] or (opts.ref_track or opts.ref_subject) and not opts.ref:
        parser.error("--strips/--exclude bounds must increase; --ref-track/--ref-subject need --ref")
    ffmpeg = os.environ.get("CHIAKI_FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg:
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg = None
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg not found (install ffmpeg on PATH or `pip install imageio-ffmpeg`, or set CHIAKI_FFMPEG)")
    clips = [(opts.video, opts.start_s, opts.dur_s, opts.track, opts.subject)] + (
        [(opts.ref[0], float(opts.ref[1]), float(opts.ref[2]), opts.ref_track, opts.ref_subject)] if opts.ref else [])
    results = [measure(ffmpeg, *clip, strips, opts) for clip in clips]
    reports = [report(*result, strips, opts) for result in results]
    print(f"Units: px of a 1080-high frame; move >= {opts.move:g} px; min score {opts.min_score:g}; track search {opts.search}; "
          f"subject search {opts.subject_search}; reseed {opts.reseed}; exclude {opts.exclude}")
    print("\n".join(f"{label}{' (--ref)' * (label == 'B')}: {clip[0]} @ {clip[1]:g} + {clip[2]:g} s" for label, clip in zip("AB", clips)))
    for block, heading in enumerate(("1. Update cadence", "2. Layers (background)", "3. Subject")):
        print(f"\n{heading}\n" + "\n".join(f"[{label}] {line}" for label, (blocks, _) in zip("AB", reports) for line in blocks[block]))
    for label, result in zip("AB", results if opts.snap else []):
        for n, t in enumerate(result[3], 1):
            if t.snaps and not os.makedirs(opts.snap, exist_ok=True):
                cv2.imwrite(os.path.join(opts.snap, f"{label}_{t.kind}{n}.png"), np.vstack(t.snaps))
    names = ("updates/s", "still-pair fraction", "background move median px", "subject residual RMS px")
    print("\nCompare A vs B (--ref): " + "; ".join(f"{name} {a:.3g} vs {b:.3g} ({f'{a / b:.2f}x' if np.isfinite([a, b]).all() and b else 'n/a'})"
                                                  for name, a, b in zip(names, *(r[1] for r in reports))) if opts.ref else "")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
