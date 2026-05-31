"""
GUI test driver — win32gui for exact client coords, per-screen back-button side.
Run: .venv/Scripts/python test_gui_runner.py
"""
import subprocess
import time
import pathlib
import ctypes
import ctypes.wintypes as wt
import pyautogui
import pygetwindow as gw

SHOTS_DIR = pathlib.Path("test_screenshots")
SHOTS_DIR.mkdir(exist_ok=True)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.2

PROJ = pathlib.Path(__file__).parent
PYTHON = str(PROJ / ".venv" / "Scripts" / "python.exe")
user32 = ctypes.windll.user32
RESULTS = []

# NAV_H=58, PAD=18 from theme — back button occupies roughly 90px wide
# LEFT back:  center x ≈ PAD + 75  = 93px from client left
# RIGHT back: center x ≈ cw - PAD - 45 from client left
BACK_LEFT_RX  = None   # computed from cw after client_rect() is known
BACK_RIGHT_RX = None
BACK_RY       = None   # footer centre ≈ ch - 29 pixels from client top


def shot(name):
    p = SHOTS_DIR / f"{name}.png"
    pyautogui.screenshot(str(p))
    print(f"  [shot] {p.name}")
    return p


def find_window(timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in gw.getAllWindows():
            t = w.title.lower()
            if "hygiene" in t or "zambia" in t:
                return w
        time.sleep(0.3)
    raise RuntimeError("App window not found")


def client_rect(win):
    hwnd = user32.FindWindowW(None, win.title)
    rect = wt.RECT()
    pt = wt.POINT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, rect.right, rect.bottom   # cx, cy, cw, ch


def focus(win):
    try:
        win.restore()
    except Exception:
        pass
    try:
        win.activate()
    except Exception:
        pass
    time.sleep(0.5)
    pyautogui.click(win.left + win.width // 2, win.top + 15)
    time.sleep(0.4)


def click_at(cx, cy, cw, ch, rx, ry, label=""):
    x = cx + int(cw * rx)
    y = cy + int(ch * ry)
    print(f"  -> {label:25s} abs({x},{y})  rel({rx:.3f},{ry:.3f})")
    pyautogui.click(x, y)
    time.sleep(1.3)


def go_back(win, cx, cy, cw, ch, side="left"):
    focus(win)
    rx = BACK_LEFT_RX if side == "left" else BACK_RIGHT_RX
    click_at(cx, cy, cw, ch, rx, BACK_RY, label=f"Back ({side})")
    time.sleep(0.6)


def test_screen(win, cx, cy, cw, ch, name, rx, ry, back_side="left"):
    print(f"\n[TEST] {name}  (back={back_side})")
    focus(win)
    click_at(cx, cy, cw, ch, rx, ry, label=name)
    img = shot(name.lower().replace(" ", "_"))
    RESULTS.append((name, img))
    go_back(win, cx, cy, cw, ch, side=back_side)


def main():
    global BACK_LEFT_RX, BACK_RIGHT_RX, BACK_RY

    print("Launching app ...")
    proc = subprocess.Popen(
        [PYTHON, "windows_app.py"],
        cwd=str(PROJ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        win = find_window()
        print(f"Window: '{win.title}'  {win.left},{win.top}  {win.width}x{win.height}")
        focus(win)
        time.sleep(1.5)

        cx, cy, cw, ch = client_rect(win)
        print(f"Client: origin=({cx},{cy})  size=({cw}x{ch})")

        # Compute back button coords from actual client dimensions
        BACK_LEFT_RX  = 93 / cw            # PAD=18 + half of ~150px button
        BACK_RIGHT_RX = (cw - 18 - 45) / cw  # PAD=18 + half of ~90px button
        BACK_RY       = (ch - 29) / ch     # footer centre (NAV_H=58 → half=29)
        print(f"Back coords: left_rx={BACK_LEFT_RX:.3f}  right_rx={BACK_RIGHT_RX:.3f}  ry={BACK_RY:.3f}")

        shot("00_welcome")

        # ── Tool button grid (relative to CLIENT area) ──────────────────────
        # Left panel = 290px fixed; right panel inner has PAD_LG=28 each side.
        rp_start = (290 + 28) / cw
        rp_end   = (cw - 28) / cw
        col_span = (rp_end - rp_start) / 4
        col_x = [rp_start + col_span * (i + 0.5) for i in range(4)]

        # Row centres calibrated from client dimensions (welcome layout):
        # 3 button rows stacked in lower ~20% of right panel
        row_y = [0.67, 0.74, 0.81]

        print(f"Grid  col_x={[f'{c:.3f}' for c in col_x]}")
        print(f"      row_y={[f'{r:.3f}' for r in row_y]}")

        # ── Row 0: History | Network Scan | Infra Scan | Zambia Risk ─────────
        # All have back button on the LEFT
        test_screen(win, cx, cy, cw, ch, "History",      col_x[0], row_y[0], "left")
        test_screen(win, cx, cy, cw, ch, "Network Scan", col_x[1], row_y[0], "left")
        test_screen(win, cx, cy, cw, ch, "Infra Scan",   col_x[2], row_y[0], "left")
        test_screen(win, cx, cy, cw, ch, "Zambia Risk",  col_x[3], row_y[0], "left")

        # ── Row 1: Policy Docs | Deploy Check | Remediation | Active Dir ─────
        # Policy Docs, Deploy Check, Remediation: LEFT;  Active Dir: RIGHT
        test_screen(win, cx, cy, cw, ch, "Policy Docs",  col_x[0], row_y[1], "left")
        test_screen(win, cx, cy, cw, ch, "Deploy Check", col_x[1], row_y[1], "left")
        test_screen(win, cx, cy, cw, ch, "Remediation",  col_x[2], row_y[1], "left")
        test_screen(win, cx, cy, cw, ch, "Active Dir",   col_x[3], row_y[1], "right")

        # ── Row 2: Dashboard | Export | Audit Log | Settings ─────────────────
        # All have back button on the RIGHT
        test_screen(win, cx, cy, cw, ch, "Dashboard",    col_x[0], row_y[2], "right")
        test_screen(win, cx, cy, cw, ch, "Export",       col_x[1], row_y[2], "right")
        test_screen(win, cx, cy, cw, ch, "Audit Log",    col_x[2], row_y[2], "right")
        test_screen(win, cx, cy, cw, ch, "Settings",     col_x[3], row_y[2], "right")

        # ── Start New Assessment (CTA, centred in right panel, y≈61%) ────────
        print("\n[TEST] Start New Assessment")
        focus(win)
        cta_rx = (290 / cw + 1) / 2     # midpoint of right panel
        click_at(cx, cy, cw, ch, cta_rx, 0.61, label="Start New Assessment")
        shot("start_new_assessment")

        print(f"\n{'='*50}")
        print(f"DONE — {len(RESULTS)+2} screenshots in {SHOTS_DIR}/")
        for name, p in RESULTS:
            print(f"  {name:20s} -> {p.name}")

    except Exception as exc:
        import traceback
        shot("ERROR")
        print(f"\nERROR: {exc}")
        traceback.print_exc()
    finally:
        proc.terminate()
        time.sleep(0.4)
        try:
            proc.kill()
        except Exception:
            pass


if __name__ == "__main__":
    main()
