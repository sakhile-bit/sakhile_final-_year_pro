"""
Motion toolkit — easing-based micro-animations for the desktop app.

Tk has no compositor, so the animations here stick to what it can do well:
window alpha fades, place()-based slides, colour interpolation, and smooth
progress. Everything is driven by ``after()`` at ~60 fps, follows the
150-300 ms transition guideline, cancels itself if the widget dies, and
degrades to an instant change when the window isn't viewable (withdrawn
roots in tests, minimised windows) so behaviour stays synchronous there.
"""
from __future__ import annotations

import time
from typing import Callable, Optional, Sequence

FRAME_MS = 15          # ~66 fps
DEFAULT_MS = 200       # inside the 150-300 ms sweet spot


def ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _viewable(widget) -> bool:
    try:
        return bool(widget.winfo_toplevel().winfo_viewable())
    except Exception:
        return False


def animate(widget, duration_ms: int, on_frame: Callable[[float], None],
            on_done: Optional[Callable[[], None]] = None,
            easing: Callable[[float], float] = ease_out_cubic,
            key: str = "anim") -> None:
    """Run ``on_frame(eased_progress)`` every frame for ``duration_ms``.

    ``key`` scopes the animation per widget: starting a new animation with
    the same key cancels the previous one (rapid hover in/out, repeated
    navigation) instead of letting two loops fight over the widget.
    """
    seqs = getattr(widget, "_motion_seq", None)
    if seqs is None:
        seqs = widget._motion_seq = {}
    seqs[key] = seq = seqs.get(key, 0) + 1
    start = time.perf_counter()

    def tick():
        try:
            if not widget.winfo_exists() or seqs.get(key) != seq:
                return
            t = min(1.0, (time.perf_counter() - start) * 1000 / duration_ms)
            on_frame(easing(t))
            if t < 1.0:
                widget.after(FRAME_MS, tick)
            elif on_done is not None:
                on_done()
        except Exception:
            return  # widget torn down mid-frame — animation simply ends

    tick()


# ── window fades ─────────────────────────────────────────────────────────────

def fade_in_window(win, duration_ms: int = 220, to_alpha: float = 1.0) -> None:
    """Fade a toplevel window in from transparent (no-op if unsupported)."""
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        return

    def frame(p: float) -> None:
        win.attributes("-alpha", to_alpha * p)

    def done() -> None:
        try:
            win.attributes("-alpha", to_alpha)
        except Exception:
            return

    animate(win, duration_ms, frame, on_done=done, key="fade")


# ── screen slides ────────────────────────────────────────────────────────────

def slide_in(widget, distance: int = 32, duration_ms: int = DEFAULT_MS,
             on_done: Optional[Callable[[], None]] = None) -> None:
    """Slide a screen-sized widget horizontally into place, then pack it.

    Positive ``distance`` enters from the right (forward navigation),
    negative from the left (back). Packs immediately when the window
    isn't viewable so navigation stays synchronous in tests.
    """
    if distance == 0 or not _viewable(widget.master):
        widget.pack(fill="both", expand=True)
        if on_done is not None:
            on_done()
        return

    widget.place(x=distance, y=0, relwidth=1.0, relheight=1.0)

    def frame(p: float) -> None:
        widget.place_configure(x=round(distance * (1.0 - p)))

    def done() -> None:
        if widget.winfo_exists():
            widget.place_forget()
            widget.pack(fill="both", expand=True)
        if on_done is not None:
            on_done()

    animate(widget, duration_ms, frame, on_done=done, key="slide")


# ── colour transitions ───────────────────────────────────────────────────────

def _hex_to_rgb(clr: str) -> tuple:
    clr = clr.lstrip("#")
    return tuple(int(clr[i:i + 2], 16) for i in (0, 2, 4))


def blend(clr_a: str, clr_b: str, t: float) -> str:
    """Interpolated hex colour between ``clr_a`` (t=0) and ``clr_b`` (t=1)."""
    a, b = _hex_to_rgb(clr_a), _hex_to_rgb(clr_b)
    return "#%02x%02x%02x" % tuple(
        round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def animate_color(widget, option: str, from_clr: str, to_clr: str,
                  duration_ms: int = 140) -> None:
    """Ease a widget's colour option from one hex value to another."""
    if not _viewable(widget):
        try:
            widget.configure(**{option: to_clr})
        except Exception:
            return
        return

    def frame(p: float) -> None:
        widget.configure(**{option: blend(from_clr, to_clr, p)})

    animate(widget, duration_ms, frame, key=f"clr:{option}")


def bind_hover(widget, option: str, base: str, hover: str,
               duration_ms: int = 130) -> None:
    """Animate ``option`` between base and hover colours on Enter/Leave."""
    widget.bind("<Enter>", lambda _e: animate_color(
        widget, option, base, hover, duration_ms), add="+")
    widget.bind("<Leave>", lambda _e: animate_color(
        widget, option, hover, base, duration_ms), add="+")


# ── entrances & progress ─────────────────────────────────────────────────────

def stagger_grid(widgets: Sequence, interval_ms: int = 24) -> None:
    """Reveal grid-managed widgets one at a time (subtle cascade entrance).

    ``grid_remove`` remembers each widget's grid options, so re-gridding
    restores the exact layout. No-op when the window isn't viewable.
    """
    widgets = [w for w in widgets if w.winfo_exists()]
    if not widgets or not _viewable(widgets[0]):
        return
    for w in widgets:
        w.grid_remove()

    anchor = widgets[0]

    def show(i: int = 0) -> None:
        try:
            if i >= len(widgets):
                return
            if widgets[i].winfo_exists():
                widgets[i].grid()
            anchor.after(interval_ms, show, i + 1)
        except Exception:
            return  # cascade aborts silently if the screen is torn down

    show()


def smooth_progress(bar, target: float, duration_ms: int = 260) -> None:
    """Ease a CTkProgressBar from its current value to ``target``."""
    try:
        current = float(bar.get())
    except Exception:
        return
    if not _viewable(bar):
        bar.set(target)
        return

    def frame(p: float) -> None:
        bar.set(current + (target - current) * p)

    animate(bar, duration_ms, frame, key="progress")
