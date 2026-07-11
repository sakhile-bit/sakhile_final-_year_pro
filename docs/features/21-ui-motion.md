# Feature: UI Motion & Smooth Experience

## Overview
A small, dependency-free motion toolkit gives the desktop app a smooth,
modern feel without a compositor. Everything is driven by Tk's `after()` at
~60 fps, follows the 150–300 ms transition guideline, cancels itself if the
widget is destroyed mid-animation, and **degrades to an instant change when
the window isn't viewable** (withdrawn roots in tests, minimised windows) so
behaviour stays synchronous and testable.

**Module:** [`src/gui/motion.py`](../../src/gui/motion.py)

---

## Primitives

| Function | Effect |
|---|---|
| `animate(widget, ms, on_frame, …)` | Core eased frame loop; per-widget `key` cancels a prior animation with the same key (rapid hover in/out, repeated nav) |
| `fade_in_window(win)` | Alpha fade for a toplevel — used on app startup and login |
| `slide_in(widget, distance)` | Horizontal slide of a single screen into place |
| `cross_slide(old, new, direction)` | **Push/pop screen transition** — outgoing screen parallaxes away while the incoming one slides in over it, so there's no blank flash between screens. The **Router** uses this |
| `slide_down_reveal(widget)` | Eases a fixed-height banner's height 0→natural (used by the elevation banner) |
| `blend(a, b, t)` / `animate_color(w, opt, …)` | Interpolate/ease a colour option (borders, fills) |
| `bind_hover(w, opt, base, hover)` | Eased colour transition on Enter/Leave — welcome tiles, buttons |
| `stagger_grid(widgets)` | Reveal grid children one-by-one for a cascade entrance |
| `smooth_progress(bar, target)` | Ease a `CTkProgressBar` to a value instead of snapping |
| `smooth_scroll(frame)` | Eased, momentum mouse-wheel scrolling for a `CTkScrollableFrame` |
| `enable_global_smooth_scroll()` | Monkeypatch `CTkScrollableFrame.__init__` once so **every** scroll area in the app is smooth |

---

## Smooth scrolling (how it works)

customtkinter scrolls its underlying canvas in coarse discrete jumps
(`yview("scroll", n, "units")`), which reads as janky on long result screens.
`smooth_scroll()`:

1. Forces the frame's `check_if_master_is_canvas` to return `False`, which
   disables ctk's own discrete wheel handler **for that frame only** (other
   frames keep theirs).
2. Binds its own `<MouseWheel>` handler that animates `yview_moveto` toward an
   **accumulating target** with `ease_out_cubic`, so fast flicks feel like
   momentum and single notches glide.
3. `notch_fraction` is measured against the *visible viewport*, so scroll speed
   feels identical on short and long screens.

It is idempotent (guarded by `_smooth_scroll_on`) and defensive (any failure
is swallowed and the frame still works with default scrolling).

`enable_global_smooth_scroll()` is called once in
[`src/gui/app.py`](../../src/gui/app.py) at startup, so no screen needs
per-frame wiring — all ~30 scrollable frames become smooth automatically.

---

## Where motion is applied

- **App startup / login** — `fade_in_window`
- **Screen navigation** — `Router._render` → `cross_slide` push/pop, with
  `_pending_old` snapping any in-flight transition so rapid navigation never
  stacks animations or leaks screens
- **Elevation banner** — `slide_down_reveal` when the app is launched without
  administrator rights (see [Server Hardening](19-server-hardening.md))
- **Welcome tiles** — `bind_hover` lift + `stagger_grid` entrance
- **Server Hardening & Infrastructure Scanner** — `smooth_progress` on the scan
  bar, `stagger_grid` cascade when results land
- **Network Scanner** — `animate_color` pulse on changed devices
- **Everywhere** — global smooth mouse-wheel scrolling

---

## Testing note
Because every animation degrades to an instant change when the toplevel isn't
viewable, tests that build screens under a withdrawn root see final state
immediately — no waiting, no flake. The full suite stays green with motion on.
