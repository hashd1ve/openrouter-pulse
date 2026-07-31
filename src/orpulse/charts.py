"""Inline SVG charts, no plotting library.

Written by hand for one reason: the dashboard has to be a single file that
renders anywhere with no server, no CDN and no runtime dependency. Every colour
is a CSS custom property, so light and dark are one stylesheet apart and the
palette lives in exactly one place.

Palette slots are the validated categorical 1-3 plus a neutral for the folded
tail. Scatter is an all-pairs form, which caps categorical hues at three -- so
the two residual archetypes fold into the neutral rather than seating a fourth
hue that would fail colourblind separation.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def fmt_compact(value: float, decimals: int = 1) -> str:
    """1_234_567 -> '1.2M'. Axis labels have no room for full numbers."""
    if value is None or not math.isfinite(value):
        return "—"
    for suffix, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if abs(value) >= size:
            return f"{value / size:.{decimals}f}{suffix}"
    if abs(value) >= 1:
        return f"{value:.0f}"
    return f"{value:.{decimals}g}"


# --- scales ----------------------------------------------------------------


@dataclass
class Scale:
    lo: float
    hi: float
    px_lo: float
    px_hi: float
    log: bool = False
    flip: bool = False

    def __post_init__(self):
        if self.log:
            self.lo = max(self.lo, 1e-12)
            self.hi = max(self.hi, self.lo * 10)
            self._a, self._b = math.log10(self.lo), math.log10(self.hi)
        else:
            self._a, self._b = self.lo, self.hi
            if self._b == self._a:
                self._b = self._a + 1

    def px(self, value: float) -> float:
        v = math.log10(max(value, 1e-12)) if self.log else value
        t = (v - self._a) / (self._b - self._a)
        t = min(max(t, -0.05), 1.05)
        if self.flip:
            t = 1 - t
        return self.px_lo + t * (self.px_hi - self.px_lo)

    def ticks(self, count: int = 5) -> list[float]:
        if self.log:
            out, e = [], math.floor(self._a)
            while e <= math.ceil(self._b):
                for m in (1, 3):
                    v = m * 10.0**e
                    if self.lo <= v <= self.hi:
                        out.append(v)
                e += 1
            return out
        step = _nice_step((self._b - self._a) / max(count, 1))
        start = math.ceil(self._a / step) * step
        out, v = [], start
        while v <= self._b + step * 1e-9:
            out.append(round(v, 10))
            v += step
        return out


def _nice_step(raw: float) -> float:
    if raw <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


# --- frame -----------------------------------------------------------------


def _frame(w, h, pad, x: Scale, y: Scale, x_title, y_title,
           x_fmt=fmt_compact, y_fmt=fmt_compact) -> str:
    """Recessive grid, axis labels, titles. Everything at low opacity on purpose:
    the data should be the only thing with contrast."""
    parts = []
    for t in x.ticks():
        px = x.px(t)
        if not (pad[3] - 1 <= px <= w - pad[1] + 1):
            continue
        parts.append(
            f'<line x1="{px:.1f}" y1="{pad[0]}" x2="{px:.1f}" y2="{h - pad[2]}" '
            f'class="grid"/>'
            f'<text x="{px:.1f}" y="{h - pad[2] + 16}" class="tick" '
            f'text-anchor="middle">{esc(x_fmt(t))}</text>'
        )
    for t in y.ticks():
        py = y.px(t)
        if not (pad[0] - 1 <= py <= h - pad[2] + 1):
            continue
        parts.append(
            f'<line x1="{pad[3]}" y1="{py:.1f}" x2="{w - pad[1]}" y2="{py:.1f}" '
            f'class="grid"/>'
            f'<text x="{pad[3] - 8}" y="{py + 4:.1f}" class="tick" '
            f'text-anchor="end">{esc(y_fmt(t))}</text>'
        )
    if x_title:
        parts.append(
            f'<text x="{(pad[3] + w - pad[1]) / 2:.0f}" y="{h - 6}" '
            f'class="axis-title" text-anchor="middle">{esc(x_title)}</text>'
        )
    if y_title:
        cy = (pad[0] + h - pad[2]) / 2
        parts.append(
            f'<text transform="rotate(-90 14 {cy:.0f})" x="14" y="{cy:.0f}" '
            f'class="axis-title" text-anchor="middle">{esc(y_title)}</text>'
        )
    return "".join(parts)


def _svg(w, h, body, label) -> str:
    # xmlns is not required for SVG inlined in HTML, but it is required the
    # moment anyone extracts one into a file or runs it through a strict XML
    # parser -- which the tests do. Declaring it costs 40 bytes.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'class="chart" role="img" aria-label="{esc(label)}" '
        f'preserveAspectRatio="xMidYMid meet">{body}</svg>'
    )


# --- charts ----------------------------------------------------------------


def scatter_log_log(points, *, x_title, y_title, vline=None, hline=None,
                    label="", w=860, h=520):
    """The workload plane.

    `points`: dicts with x, y, size, colour (a CSS var name), name, tooltip.
    Marks carry a 2px surface-coloured ring so overlapping circles stay
    separable -- with ~400 points in two dense clusters, that ring is what keeps
    the shape of the clusters readable rather than a blob.
    """
    pad = (18, 24, 44, 62)
    xs = [p["x"] for p in points if p["x"] > 0]
    ys = [p["y"] for p in points if p["y"] > 0]
    if not xs or not ys:
        return '<p class="empty">No data.</p>'

    x = Scale(min(xs), max(xs), pad[3], w - pad[1], log=True)
    y = Scale(min(ys), max(ys), pad[0], h - pad[2], log=True, flip=True)
    sizes = [p.get("size", 1) or 1 for p in points]
    s_lo, s_hi = min(sizes), max(sizes)

    def radius(v):
        if s_hi <= s_lo:
            return 5.0
        t = (math.log10(max(v, 1)) - math.log10(max(s_lo, 1))) / (
            math.log10(s_hi) - math.log10(max(s_lo, 1)) or 1
        )
        return 3.5 + 12 * max(min(t, 1), 0)

    body = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="none"/>']
    body.append(_frame(w, h, pad, x, y, x_title, y_title))

    for value, axis, cls in ((vline, "v", "cut"), (hline, "h", "cut")):
        if value is None:
            continue
        if axis == "v":
            px = x.px(value)
            body.append(f'<line x1="{px:.1f}" y1="{pad[0]}" x2="{px:.1f}" '
                        f'y2="{h - pad[2]}" class="{cls}"/>')
        else:
            py = y.px(value)
            body.append(f'<line x1="{pad[3]}" y1="{py:.1f}" x2="{w - pad[1]}" '
                        f'y2="{py:.1f}" class="{cls}"/>')

    # Biggest last so they land on top of the crowd rather than under it.
    for p in sorted(points, key=lambda p: p.get("size", 0) or 0):
        if p["x"] <= 0 or p["y"] <= 0:
            continue
        body.append(
            f'<circle cx="{x.px(p["x"]):.1f}" cy="{y.px(p["y"]):.1f}" '
            f'r="{radius(p.get("size", 1) or 1):.1f}" fill="var(--{p["colour"]})" '
            f'class="dot"><title>{esc(p.get("tooltip", p.get("name", "")))}</title></circle>'
        )
    for p in points:
        if not p.get("label"):
            continue
        px, py = x.px(p["x"]), y.px(p["y"])
        # Flip the label to the other side of its dot when it would otherwise
        # run past the right edge. Estimated at 6.6px per character, which is
        # close enough for a 12px sans-serif to keep every label inside.
        overflows = px + 11 + len(p["label"]) * 6.6 > w - 6
        body.append(
            f'<text x="{px + (-11 if overflows else 11):.1f}" y="{py - 7:.1f}" '
            f'text-anchor="{"end" if overflows else "start"}" '
            f'class="point-label">{esc(p["label"])}</text>'
        )
    return _svg(w, h, "".join(body), label)


def step_band(steps, *, x_title, y_title, label="", w=860, h=360,
              censor_marks=None, y_floor=None):
    """Kaplan-Meier: a step function with its confidence band.

    A step, never a smooth line: survival is constant between events, and
    interpolating between them would draw a decline that was never observed.

    `y_floor` truncates the vertical axis. A curve that never drops below 88%
    plotted on a full 0-100% axis is a flat line against nine-tenths of empty
    space, and the shape -- which is the whole point -- becomes invisible.
    Truncating a bar chart's axis misrepresents magnitude and is never allowed;
    truncating a step chart's axis rescales a trajectory and is fine SO LONG AS
    it is stated, which is why the caller passes it explicitly and the caption
    says so.
    """
    pad = (18, 24, 44, 62)
    if not steps:
        return '<p class="empty">No data.</p>'
    xs = [s["x"] for s in steps]
    x = Scale(0, max(xs), pad[3], w - pad[1])
    y = Scale(y_floor if y_floor is not None else 0.0, 1,
              pad[0], h - pad[2], flip=True)

    body = [_frame(w, h, pad, x, y, x_title, y_title,
                   x_fmt=lambda v: f"{v:,.0f}", y_fmt=lambda v: f"{v:.0%}")]

    upper, lower, line = [], [], []
    prev_x, prev_s = 0.0, 1.0
    for s in steps:
        line.append(f"{x.px(prev_x):.1f},{y.px(prev_s):.1f}")
        line.append(f"{x.px(s['x']):.1f},{y.px(prev_s):.1f}")
        line.append(f"{x.px(s['x']):.1f},{y.px(s['y']):.1f}")
        if s.get("hi") is not None and math.isfinite(s["hi"]):
            upper.append(f"{x.px(s['x']):.1f},{y.px(s['hi']):.1f}")
        if s.get("lo") is not None and math.isfinite(s["lo"]):
            lower.append(f"{x.px(s['x']):.1f},{y.px(s['lo']):.1f}")
        prev_x, prev_s = s["x"], s["y"]

    if upper and lower:
        body.append(f'<polygon points="{" ".join(upper + lower[::-1])}" class="band"/>')
    body.append(f'<polyline points="{" ".join(line)}" class="step"/>')

    for t in censor_marks or []:
        px, py = x.px(t["x"]), y.px(t["y"])
        body.append(f'<line x1="{px:.1f}" y1="{py - 4:.1f}" x2="{px:.1f}" '
                    f'y2="{py + 4:.1f}" class="censor"/>')
    return _svg(w, h, "".join(body), label)


def forest(rows, *, x_title, label="", w=860, row_h=34):
    """Point estimates with confidence intervals.

    The right form for regression output: it shows the uncertainty as the
    primary object rather than hiding it behind a coefficient. A bar chart of
    coefficients would imply a precision that is not there.
    """
    # Left padding is derived from the longest label rather than guessed: a
    # fixed value silently truncates whichever category happens to have a long
    # name, and the truncation looks like a rendering glitch rather than a bug.
    label_px = max((len(r["label"]) for r in rows), default=10) * 6.6 + 24
    pad = (22, 120, 44, max(150, min(label_px, w * 0.42)))
    h = pad[0] + pad[2] + row_h * max(len(rows), 1)
    lo = min([r["lo"] for r in rows] + [0])
    hi = max([r["hi"] for r in rows] + [0])
    span = (hi - lo) or 1
    x = Scale(lo - span * 0.08, hi + span * 0.08, pad[3], w - pad[1])

    body = [f'<line x1="{x.px(0):.1f}" y1="{pad[0] - 6}" x2="{x.px(0):.1f}" '
            f'y2="{h - pad[2] + 6}" class="zero"/>']
    for t in x.ticks(5):
        px = x.px(t)
        body.append(f'<text x="{px:.1f}" y="{h - pad[2] + 20}" class="tick" '
                    f'text-anchor="middle">{t:+.2f}</text>')
    for i, r in enumerate(rows):
        cy = pad[0] + row_h * i + row_h / 2
        colour = "s1" if r.get("significant") else "neutral"
        body.append(
            f'<text x="{pad[3] - 12}" y="{cy + 4:.1f}" class="row-label" '
            f'text-anchor="end">{esc(r["label"])}</text>'
            f'<line x1="{x.px(r["lo"]):.1f}" y1="{cy:.1f}" x2="{x.px(r["hi"]):.1f}" '
            f'y2="{cy:.1f}" stroke="var(--{colour})" class="ci"/>'
            f'<circle cx="{x.px(r["value"]):.1f}" cy="{cy:.1f}" r="5.5" '
            f'fill="var(--{colour})" class="dot"/>'
            f'<text x="{w - pad[1] + 10}" y="{cy + 4:.1f}" class="row-value">'
            f'{r["value"]:+.2f}<tspan class="muted"> n={r["n"]}</tspan></text>'
        )
    body.append(f'<text x="{(pad[3] + w - pad[1]) / 2:.0f}" y="{h - 6}" '
                f'class="axis-title" text-anchor="middle">{esc(x_title)}</text>')
    return _svg(w, h, "".join(body), label)


def paired_bars(rows, *, left_title, right_title, label="", w=860, row_h=30):
    """Two shares per category, mirrored around a shared centre.

    The right form when the point IS the disagreement between two measures. A
    grouped bar chart would let the eye compare the wrong pairs; mirroring makes
    the gap itself the visual object.
    """
    pad = (34, 20, 16, 20)
    h = pad[0] + pad[2] + row_h * max(len(rows), 1)
    centre = w / 2
    gap = 92                                  # space for the category label
    # The value label sits outside the bar end, so the bar cannot use the full
    # half-width or the number runs off the viewBox.
    value_room = 60
    half = (w - gap) / 2 - pad[3] - value_room
    peak = max([max(r["left"], r["right"]) for r in rows] + [1e-9])

    body = [
        f'<text x="{centre - gap / 2 - 8:.0f}" y="16" class="col-head" '
        f'text-anchor="end">{esc(left_title)}</text>'
        f'<text x="{centre + gap / 2 + 8:.0f}" y="16" class="col-head" '
        f'text-anchor="start">{esc(right_title)}</text>'
    ]
    for i, r in enumerate(rows):
        top = pad[0] + row_h * i
        cy = top + row_h / 2
        lw = half * (r["left"] / peak)
        rw = half * (r["right"] / peak)
        body.append(
            f'<rect x="{centre - gap / 2 - lw:.1f}" y="{top + 5:.1f}" '
            f'width="{max(lw, 0.5):.1f}" height="{row_h - 12}" rx="3" '
            f'fill="var(--s2)" class="bar"/>'
            f'<rect x="{centre + gap / 2:.1f}" y="{top + 5:.1f}" '
            f'width="{max(rw, 0.5):.1f}" height="{row_h - 12}" rx="3" '
            f'fill="var(--s1)" class="bar"/>'
            f'<text x="{centre:.0f}" y="{cy + 4:.1f}" class="row-label" '
            f'text-anchor="middle">{esc(r["label"])}</text>'
            f'<text x="{centre - gap / 2 - lw - 6:.1f}" y="{cy + 4:.1f}" '
            f'class="row-value" text-anchor="end">{r["left"]:.1%}</text>'
            f'<text x="{centre + gap / 2 + rw + 6:.1f}" y="{cy + 4:.1f}" '
            f'class="row-value" text-anchor="start">{r["right"]:.1%}</text>'
        )
    return _svg(w, h, "".join(body), label)


def hbar(rows, *, value_fmt=lambda v: f"{v:.1%}", label="", w=860, row_h=30,
         colour="s1"):
    """Horizontal bars, labels outside, 4px rounded data-end."""
    pad = (8, 90, 12, 170)
    h = pad[0] + pad[2] + row_h * max(len(rows), 1)
    peak = max([r["value"] for r in rows] + [1e-9])
    body = []
    for i, r in enumerate(rows):
        top = pad[0] + row_h * i
        cy = top + row_h / 2
        bw = (w - pad[3] - pad[1]) * (r["value"] / peak)
        c = r.get("colour", colour)
        body.append(
            f'<text x="{pad[3] - 12}" y="{cy + 4:.1f}" class="row-label" '
            f'text-anchor="end">{esc(r["label"])}</text>'
            f'<rect x="{pad[3]}" y="{top + 5:.1f}" width="{max(bw, 1):.1f}" '
            f'height="{row_h - 12}" rx="4" fill="var(--{c})" class="bar"/>'
            f'<text x="{pad[3] + bw + 10:.1f}" y="{cy + 4:.1f}" '
            f'class="row-value">{esc(value_fmt(r["value"]))}</text>'
        )
    return _svg(w, h, "".join(body), label)
