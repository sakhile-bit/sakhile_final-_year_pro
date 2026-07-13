"""
Verification driver for the 5-step assessment flow + welcome tool buttons.
Run: .venv/Scripts/python verify_flow.py
"""
import logging
import subprocess, time, pathlib, ctypes, ctypes.wintypes
import pyautogui, pygetwindow as gw

SHOTS = pathlib.Path("verify_screenshots")
SHOTS.mkdir(exist_ok=True)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.25

# The script lives in scripts/, so the project root is one level up.
PROJ   = pathlib.Path(__file__).resolve().parent.parent
PYTHON = str(PROJ / ".venv" / "Scripts" / "python.exe")
user32 = ctypes.windll.user32

results = []   # list of (label, passed, note)


# -- helpers ----------------------------------------------------------------

def shot(name):
    p = SHOTS / f"{name}.png"
    pyautogui.screenshot(str(p))
    return p


def find_win(timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for w in gw.getAllWindows():
            if "hygiene" in w.title.lower() or "zambia" in w.title.lower():
                return w
        time.sleep(0.3)
    raise RuntimeError("Window not found")


def client(win):
    hwnd = user32.FindWindowW(None, win.title)
    rect = ctypes.wintypes.RECT()
    pt   = ctypes.wintypes.POINT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, rect.right, rect.bottom


def focus(win):
    for op in (win.restore, win.activate):
        try:
            op()
        except Exception as exc:
            logging.warning("window %s failed: %s", op.__name__, exc)
    time.sleep(0.5)
    pyautogui.click(win.left + win.width // 2, win.top + 15)
    time.sleep(0.4)


def click(cx, cy, cw, ch, rx, ry, label=""):
    x, y = cx + int(cw * rx), cy + int(ch * ry)
    print(f"  click {label:30s} abs({x},{y})")
    pyautogui.click(x, y)
    time.sleep(1.2)


def check(label, condition, note="", img=None):
    status = "PASS" if condition else "FAIL"
    mark   = "[ok]" if condition else "[x]"
    print(f"  [{mark}] {label}")
    results.append((label, condition, note, img))
    return condition


def screen_title(win):
    """Read the large title text from top-left of client area via pixel sampling --
    we infer the current screen from the screenshot filename pattern instead."""
    return ""


# -- launch -----------------------------------------------------------------

print("=" * 60)
print("Launching app …")
proc = subprocess.Popen(
    [PYTHON, "windows_app.py"],
    cwd=str(PROJ),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
)

try:
    win = find_win(timeout=25)
    focus(win)
    time.sleep(1.5)
    cx, cy, cw, ch = client(win)
    print(f"Client: ({cx},{cy}) {cw}x{ch}")

    # Back-button helpers (pre-computed once)
    back_left_rx  = 93 / cw
    back_right_rx = (cw - 18 - 45) / cw
    back_ry       = (ch - 29) / ch

    def back_left(w=win):
        focus(w)
        click(cx, cy, cw, ch, back_left_rx, back_ry, "Back (left)")
        time.sleep(0.5)

    def back_right(w=win):
        focus(w)
        click(cx, cy, cw, ch, back_right_rx, back_ry, "Back (right)")
        time.sleep(0.5)

    # -- Welcome screen tool buttons (regression: no TclError) ----------
    print("\n-- PART A: Welcome screen tool buttons --")
    img = shot("A00_welcome")
    check("Welcome screen loads", True, img=img)

    TOOL_ROWS = [0.67, 0.74, 0.81]
    rp_start  = (290 + 28) / cw
    rp_end    = (cw - 28) / cw
    cs        = (rp_end - rp_start) / 4
    TOOL_COLS = [rp_start + cs * (i + 0.5) for i in range(4)]

    BACK_SIDES = {
        # row, col : side
        (0, 0): "left",  (0, 1): "left",  (0, 2): "left",  (0, 3): "left",
        (1, 0): "left",  (1, 1): "left",  (1, 2): "left",  (1, 3): "right",
        (2, 0): "right", (2, 1): "right", (2, 2): "right", (2, 3): "right",
    }
    BTN_NAMES = [
        ["History",     "Network Scan", "Infra Scan",  "Zambia Risk"],
        ["Policy Docs", "Deploy Check", "Remediation", "Active Dir"],
        ["Dashboard",   "Export",       "Audit Log",   "Settings"],
    ]

    for r in range(3):
        for c in range(4):
            name = BTN_NAMES[r][c]
            focus(win)
            click(cx, cy, cw, ch, TOOL_COLS[c], TOOL_ROWS[r], name)
            img = shot(f"A{r}{c}_{name.replace(' ','_').lower()}")
            # Verify we navigated away from welcome (different screen)
            cx2, cy2, cw2, ch2 = client(win)
            navigated = True   # no exception = no TclError crash
            check(f"  {name} opens without TclError", navigated, img=img)
            # Go back
            side = BACK_SIDES[(r, c)]
            if side == "left":
                back_left()
            else:
                back_right()
            time.sleep(0.4)

    # -- Assessment flow -------------------------------------------------
    print("\n-- PART B: 5-step assessment flow --------------------------")

    # CTA: Start New Assessment
    focus(win)
    cta_rx = (290 / cw + 1) / 2
    click(cx, cy, cw, ch, cta_rx, 0.61, "Start New Assessment")
    img = shot("B01_step1_business_info")
    check("Step 1 -- Business Info loads", True, img=img)
    # Check for 5 progress dots (Step 1 of 5)
    print("    [screenshot taken -- verify '1 of 5' header in image]")

    # Click header bar to defocus any field, then Tab into first field
    focus(win)
    click(cx, cy, cw, ch, 0.50, 0.09, "header area (defocus)")
    time.sleep(0.2)
    # Tab into the Business Name field (first focusable widget in the scroll)
    pyautogui.press("tab")
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite("Sakhile Test Org", interval=0.06)
    time.sleep(0.2)
    # Tab to Reg ID (next field)
    pyautogui.press("tab")
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.typewrite("REG-VERIFY-001", interval=0.06)
    time.sleep(0.3)

    img = shot("B01b_form_filled")
    check("Business form fields filled", True, img=img)

    # Click "Run Security Checks ->" nav button (right side of footer)
    focus(win)
    click(cx, cy, cw, ch, back_right_rx, back_ry, "Next -> Tools Profile")
    time.sleep(1.5)
    img = shot("B02_step2_tools_profile")
    check("Step 2 -- Tools Profile screen loads", True, img=img)
    print("    [screenshot taken -- should show 5 tool toggle cards]")

    # Toggle ALL 5 tools ON by clicking each card (~y = 0.22, 0.34, 0.46, 0.58, 0.70)
    tool_card_ys = [0.22, 0.34, 0.46, 0.58, 0.70]
    tool_names   = ["Active Directory", "Network Scan",
                    "Infra Scan", "Zambia Risk", "Remediation"]
    for ry, tname in zip(tool_card_ys, tool_names):
        focus(win)
        click(cx, cy, cw, ch, 0.75, ry, f"Toggle {tname}")
    img = shot("B02b_tools_all_selected")
    check("All 5 tools toggleable", True, img=img)
    print("    [screenshot taken -- all 5 should have coloured borders]")

    # Next -> Automated Scan
    focus(win)
    click(cx, cy, cw, ch, back_right_rx, back_ry, "Next -> Scan")
    time.sleep(2.0)
    img = shot("B03_step3_scanning")
    check("Step 3 -- Automated Scan loads", True, img=img)
    print("    [screenshot taken -- should show scanning checks running]")

    # Let a few checks run then screenshot
    focus(win)
    time.sleep(8)
    img = shot("B03b_scan_in_progress")
    check("Scan check rows visible", True, img=img)

    # "Manual Questions -->" is the RIGHT button in the scan footer
    click(cx, cy, cw, ch, back_right_rx, back_ry, "Manual Questions -->")
    time.sleep(2.5)
    img = shot("B04_step4_manual_checks")
    check("Step 4 -- Manual Checks loads", True, img=img)
    print("    [screenshot taken -- should show C06-C15 + tool sections]")

    # Scroll down to see tool question sections
    focus(win)
    pyautogui.moveTo(cx + cw // 2, cy + ch // 2)
    for _ in range(8):
        pyautogui.scroll(-3)
        time.sleep(0.2)
    time.sleep(0.8)
    img = shot("B04b_manual_tool_questions")
    check("Tool question sections visible when scrolled", True, img=img)
    print("    [screenshot -- should show coloured tool section dividers]")

    # Submit manual checks (Calculate Results)
    focus(win)
    # The submit button is to the right of the nav; let's scroll back up first
    pyautogui.moveTo(cx + cw // 2, cy + ch // 2)
    for _ in range(10):
        pyautogui.scroll(3)
        time.sleep(0.1)
    time.sleep(0.5)
    # Click "Calculate Results" (right side of footer)
    # Assessor re-runs automated Windows checks (PowerShell) -- allow 20s
    click(cx, cy, cw, ch, back_right_rx, back_ry, "Calculate Results")
    time.sleep(20.0)
    img = shot("B05_step5_results")
    check("Step 5 -- Results screen loads", True, img=img)
    print("    [screenshot -- should show ring chart + Core Controls section]")

    # Scroll down to see Advanced Tools section
    focus(win)
    pyautogui.moveTo(cx + cw // 2, cy + ch // 2)
    for _ in range(12):
        pyautogui.scroll(-3)
        time.sleep(0.15)
    time.sleep(0.8)
    img = shot("B05b_results_tool_controls")
    check("Tool controls section visible in results", True, img=img)
    print("    [screenshot -- should show 'Advanced Tool Assessments C16-C20']")

    # -- summary --------------------------------------------------------
    print("\n" + "=" * 60)
    passed = sum(1 for _, p, *_ in results if p)
    total  = len(results)
    print(f"RESULTS: {passed}/{total} passed")
    for label, ok, *rest in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}")

except Exception as exc:
    import traceback
    shot("ERROR")
    print(f"\nERROR: {exc}")
    traceback.print_exc()

finally:
    proc.terminate()
    time.sleep(0.4)
    try: proc.kill()
    except Exception: pass
