"""
Motion toolkit — easing-based micro-animations for the desktop app.

Tk has no compositor, so the animations here stick to what it can do well:
window alpha fades, place()-based slides, colour interpolation, smooth
progress, and pointer-driven wheel scrolling. Everything is driven by
``after()`` at ~60 fps, follows the 150-300 ms transition guideline, cancels
itself if the widget dies, and degrades to an instant change when the window
isn't viewable (withdrawn roots in tests, minimised windows) so behaviour
stays synchronous there.

Two things are worth knowing:

* Every effect is built on :func:`animate`, which honours a global
  :func:`set_reduced_motion` switch — flip it on and animations resolve
  instantly, for accessibility or low-powered machines.
* A small palette of easing curves (``ease_out_cubic`` and friends) can be
  passed to :func:`animate` via ``easing=`` to change the feel.
"""
from __future__ import annotations

import time
from typing import Callable, Optional, Sequence

__all__ = [
    # core
    "animate", "set_reduced_motion", "is_reduced_motion",
    # easing curves
    "linear", "ease_out_cubic", "ease_in_cubic", "ease_in_out_cubic",
    "ease_out_quad", "ease_out_back",
    # effects
    "fade_in_window", "slide_in", "cross_slide", "blend", "animate_color",
    "bind_hover", "stagger_grid", "slide_down_reveal", "smooth_progress",
    # scrolling
    "smooth_scroll", "enable_global_smooth_scroll",
]

FRAME_MS = 15          # ~66 fps
DEFAULT_MS = 200       # inside the 150-300 ms sweet spot


# ── reduced motion ────────────────────────────────────────────────────────────
# A single global switch every animation honours. When on, animations resolve
# instantly to their final frame — for users who find motion distracting, and
# for low-powered machines. Wire it from the settings screen via
# ``set_reduced_motion(get_bool_setting("reduced_motion", False))``.

_reduced_motion = False


def set_reduced_motion(enabled: bool) -> None:
    """Enable/disable instant (motion-free) animations app-wide."""
    global _reduced_motion
    _reduced_motion = bool(enabled)


def is_reduced_motion() -> bool:
    return _reduced_motion


# ── easing curves ─────────────────────────────────────────────────────────────
# All take and return a 0‥1 progress value. ``animate`` defaults to
# ``ease_out_cubic``; pass ``easing=`` to pick another feel.

def linear(t: float) -> float:
    return t


def ease_out_cubic(t: float) -> float:
    """Decelerate to a stop — the workhorse for entrances and moves."""
    return 1.0 - (1.0 - t) ** 3


def ease_in_cubic(t: float) -> float:
    """Accelerate from rest — good for exits."""
    return t ** 3


def ease_in_out_cubic(t: float) -> float:
    """Ease in then out — natural for A→B moves that start and end at rest."""
    return 4 * t ** 3 if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_out_quad(t: float) -> float:
    """Gentler deceleration than cubic."""
    return 1.0 - (1.0 - t) ** 2


def ease_out_back(t: float) -> float:
    """Overshoot slightly past the target then settle (playful pop).

    Note: returns values > 1 mid-curve, so only use where a small overshoot
    is safe (position, scale) — not for clamped values like alpha.
    """
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


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

    Resolves instantly to the final frame when :func:`is_reduced_motion` is
    set or ``duration_ms`` is non-positive, so every effect built on ``animate``
    degrades gracefully without special-casing.
    """
    # Instant path: reduced-motion preference or a zero/negative duration.
    if _reduced_motion or duration_ms <= 0:
        try:
            on_frame(easing(1.0))
            if on_done is not None:
                on_done()
        except Exception:
            pass
        return

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


# ── screen cross-transitions (push / pop) ────────────────────────────────────

def cross_slide(old, new, direction: int, duration_ms: int = 240,
                on_done: Optional[Callable[[], None]] = None,
                parallax: float = 0.22) -> None:
    """Cross-slide from ``old`` to ``new`` like a mobile push/pop.

    Unlike a bare slide, the outgoing screen stays visible and parallaxes
    away while the incoming one slides in over it, so there is never a flash
    of blank background between screens.

    * ``direction > 0`` (push/forward): ``new`` enters from the right on top;
      ``old`` drifts left underneath.
    * ``direction < 0`` (pop/back): ``old`` exits right on top; ``new`` is
      revealed from the left underneath.
    * ``direction == 0`` (replace) or an un-viewable window: instant swap.

    Both frames are ``place``-managed (relwidth/relheight = 1) during the
    animation, then ``new`` is packed and ``old`` destroyed. The animation is
    keyed on the shared container, so starting a new transition cancels any
    in-flight one cleanly.
    """
    container = new.master

    def finish() -> None:
        try:
            if old is not None and old.winfo_exists():
                old.destroy()
        except Exception:
            pass
        try:
            if new.winfo_exists():
                new.place_forget()
                new.pack(fill="both", expand=True)
        except Exception:
            pass
        if on_done is not None:
            on_done()

    # Instant swap: no direction, first screen, or window not on-screen.
    if direction == 0 or old is None or not _viewable(container):
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass
        try:
            new.pack(fill="both", expand=True)
        except Exception:
            pass
        if on_done is not None:
            on_done()
        return

    old.place(relx=0, rely=0, relwidth=1, relheight=1)
    if direction > 0:
        # Push: incoming slides in from the right, on top.
        new.place(relx=1.0, rely=0, relwidth=1, relheight=1)
        new.lift()

        def frame(p: float) -> None:
            new.place_configure(relx=1.0 - p)
            old.place_configure(relx=-parallax * p)
    else:
        # Pop: outgoing slides out to the right, on top; incoming revealed.
        new.place(relx=-parallax, rely=0, relwidth=1, relheight=1)
        old.lift()

        def frame(p: float) -> None:
            old.place_configure(relx=p)
            new.place_configure(relx=-parallax * (1.0 - p))

    animate(container, duration_ms, frame, on_done=finish, key="screen")


# ── colour transitions ───────────────────────────────────────────────────────

def _hex_to_rgb(clr: str) -> tuple:
    clr = clr.lstrip("#")
    if len(clr) == 3:                      # #abc → #aabbcc shorthand
        clr = "".join(ch * 2 for ch in clr)
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


def slide_down_reveal(widget, duration_ms: int = 200) -> None:
    """Reveal a fixed-height banner by easing its height from 0 to natural.

    The widget must have a configured ``height`` and ``grid/pack_propagate``
    off so the height is honoured. No-op (instant) when not viewable.
    """
    try:
        target = int(widget.cget("height"))
    except Exception:
        return
    if target <= 1:
        return
    if not _viewable(widget):
        return

    def frame(p: float) -> None:
        widget.configure(height=max(1, int(target * p)))

    def done() -> None:
        try:
            widget.configure(height=target)
        except Exception:
            return

    animate(widget, duration_ms, frame, on_done=done, key="reveal")


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


# ── smooth scrolling ──────────────────────────────────────────────────────────
#
# The mouse wheel has one well-known trap on Windows: Tk delivers
# ``<MouseWheel>`` to the *focused* widget, not the widget under the cursor.
# customtkinter's built-in handler keys off ``event.widget``, so a scroll
# frame only responds once you have clicked into it — on the scan/result
# screens focus usually sits on a nav button, so the wheel does nothing.
#
# The fix here is a single application-wide handler that finds the scroll
# frame under the *pointer* (``winfo_containing``) and eases it. Because it is
# pointer-based, every CTkScrollableFrame — scan output included — scrolls
# with the wheel or a touchpad whether or not it holds focus.

_NOTCH_FRACTION = 0.16     # viewport fraction travelled per full wheel notch
_SCROLL_MS = 160           # ease duration per notch (momentum on fast flicks)
_wheel_root = None         # the Tk root the global handler is bound to
# Per-canvas scroll state (accumulating target + tuning) lives on the canvas
# itself via ``_scroll_*`` attributes, so it dies with the canvas — no global
# registry to leak or collide on id() reuse after garbage collection.


def _find_scrollable_under_pointer(root, x_root, y_root):
    """Return the innermost CTkScrollableFrame under the pointer that still
    has content to scroll, or ``None``.

    Walks outward from the hovered widget so a fully-visible inner frame never
    swallows the wheel — the event bubbles to whatever outer page *can* move.
    """
    import customtkinter as ctk
    try:
        widget = root.winfo_containing(x_root, y_root)
    except Exception:
        widget = None

    while widget is not None:
        if isinstance(widget, ctk.CTkScrollableFrame):
            canvas = getattr(widget, "_parent_canvas", None)
            if canvas is not None:
                try:
                    first, last = canvas.yview()
                except Exception:
                    first, last = 0.0, 1.0
                if (last - first) < 1.0:      # genuinely overflows
                    return widget
        try:
            widget = widget.master
        except Exception:
            return None
    return None


def _scroll_canvas(canvas, steps: float) -> None:
    """Ease ``canvas`` by ``steps`` wheel notches toward an accumulating target."""
    try:
        first, last = canvas.yview()
    except Exception:
        return
    span = last - first
    if span >= 1.0:
        return

    notch = getattr(canvas, "_scroll_notch", _NOTCH_FRACTION)
    duration = getattr(canvas, "_scroll_ms", _SCROLL_MS)
    # Accumulate onto any in-flight target so fast flicks build momentum.
    pending = getattr(canvas, "_scroll_target", None)
    base = pending if pending is not None else first
    max_top = max(0.0, 1.0 - span)
    target = min(max_top, max(0.0, base + steps * notch * span))
    canvas._scroll_target = target
    start = first

    def on_frame(p: float) -> None:
        try:
            canvas.yview_moveto(start + (target - start) * p)
        except Exception:
            pass

    def on_done() -> None:
        try:
            canvas._scroll_target = None
        except Exception:
            pass

    animate(canvas, duration, on_frame, on_done=on_done, key="smoothscroll")


def _on_global_wheel(event):
    """Application-wide wheel handler: scroll whatever the pointer is over."""
    try:
        root = event.widget.winfo_toplevel()
    except Exception:
        return None
    target = _find_scrollable_under_pointer(root, event.x_root, event.y_root)
    if target is None:
        return None

    # Normalise across mouse wheels (Windows/macOS send ``delta`` in units of
    # 120), precision touchpads (small deltas → fine, smooth steps) and X11
    # (Button-4/5, no delta).
    if getattr(event, "num", 0) in (4, 5):
        steps = -1.0 if event.num == 4 else 1.0
    else:
        steps = -event.delta / 120.0
        if steps == 0.0:
            return None

    _scroll_canvas(target._parent_canvas, steps)
    return "break"   # we handled it — don't let ctk's focus-based handler re-scroll


def _install_global_wheel(widget) -> None:
    """Bind the pointer-based wheel handler once per Tk root."""
    global _wheel_root
    try:
        root = widget.winfo_toplevel()
    except Exception:
        return
    if _wheel_root is root:
        return
    try:
        widget.bind_all("<MouseWheel>", _on_global_wheel, add="+")   # Win / macOS
        widget.bind_all("<Button-4>", _on_global_wheel, add="+")     # X11 up
        widget.bind_all("<Button-5>", _on_global_wheel, add="+")     # X11 down
        _wheel_root = root
    except Exception:
        pass


def smooth_scroll(scrollable, notch_fraction: float = _NOTCH_FRACTION,
                  duration_ms: int = _SCROLL_MS) -> None:
    """Give a CTkScrollableFrame eased, pointer-driven mouse-wheel scrolling.

    Disables customtkinter's own focus-based discrete scroll for this frame
    and makes sure the application-wide pointer handler is installed. Safe and
    idempotent to call on any CTkScrollableFrame.

    ``notch_fraction`` (viewport fraction per wheel notch) and ``duration_ms``
    (ease length) tune this frame's feel — handy for a long log where you want
    faster travel.
    """
    # Per-frame tuning rides on the canvas so the global handler can read it.
    canvas = getattr(scrollable, "_parent_canvas", None)
    if canvas is not None:
        canvas._scroll_notch = notch_fraction
        canvas._scroll_ms = duration_ms

    if not getattr(scrollable, "_smooth_scroll_on", False):
        scrollable._smooth_scroll_on = True
        # Neutralise ctk's per-instance <MouseWheel> handler (it checks
        # check_if_master_is_canvas against the *focused* widget); the global
        # pointer-based handler drives all scrolling instead.
        try:
            scrollable.check_if_master_is_canvas = lambda _w: False  # type: ignore[assignment]
        except Exception:
            pass
    _install_global_wheel(scrollable)


def enable_global_smooth_scroll() -> None:
    """Make every CTkScrollableFrame in the app scroll smoothly by wheel/touchpad.

    Wraps ``CTkScrollableFrame.__init__`` once so each instance opts into
    :func:`smooth_scroll` at construction — no per-screen wiring needed.
    Idempotent and defensive: a failure to smooth one frame never blocks
    its creation.
    """
    import customtkinter as ctk

    if getattr(ctk.CTkScrollableFrame, "_smooth_patched", False):
        return
    orig_init = ctk.CTkScrollableFrame.__init__

    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        try:
            smooth_scroll(self)
        except Exception:
            pass

    ctk.CTkScrollableFrame.__init__ = patched_init
    setattr(ctk.CTkScrollableFrame, "_smooth_patched", True)
    # avoid patching multiple times in case the function is called repeatedly #
