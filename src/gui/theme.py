"""
Design system for the Zambia Digital Hygiene Windows app.
Inspired by Sentry.io — dark purple-gray palette, clean typography.
"""

APP_NAME    = "Zambia Digital Hygiene Certification"
APP_VERSION = "1.0.0"

# ── Colour palette (Sentry-inspired) ─────────────────────────────────────────
CLR_BRAND       = "#100E18"   # very dark brand panel (welcome left side)
CLR_BG          = "#1A1923"   # page / window background
CLR_SURFACE     = "#211F2B"   # card / panel surface
CLR_SURFACE_ALT = "#1C1A25"   # inputs, secondary surfaces
CLR_SURFACE_HVR = "#272535"   # hover state
CLR_BORDER      = "#2E2B3B"   # card borders
CLR_DIVIDER     = "#1F1C2A"   # horizontal rules / separators

CLR_ACCENT      = "#6C5FC7"   # primary purple (Sentry)
CLR_ACCENT_HOV  = "#7D70D6"   # purple hover
CLR_ACCENT_DIM  = "#1A1730"   # very dark purple (ghost btn hover bg)
CLR_BLUE        = "#4674CA"   # secondary blue accent
CLR_BLUE_DIM    = "#0E1828"   # blue dim
CLR_AMBER       = "#D9A222"   # warning / amber
CLR_AMBER_DIM   = "#1C1500"   # amber dim

CLR_TEXT        = "#EAE7F3"   # primary text
CLR_TEXT_SEC    = "#B4AFCA"   # secondary text
CLR_MUTED       = "#7C7691"   # muted / caption

CLR_SUCCESS     = "#2BA22B"   # semantic green — PASS / active
CLR_WARNING     = "#D9A222"   # semantic amber — WARNING
CLR_DANGER      = "#E03E3F"   # semantic red — FAIL / error
CLR_DANGER_DIM  = "#200A0A"   # danger dim

CLR_GOLD        = "#F5C518"
CLR_SILVER      = "#C0BCC8"
CLR_BRONZE      = "#C47B38"

TIER_COLOURS = {
    "GOLD":          CLR_GOLD,
    "SILVER":        CLR_SILVER,
    "BRONZE":        CLR_BRONZE,
    "NOT CERTIFIED": CLR_DANGER,
}

TIER_THRESHOLD = {"GOLD": 80, "SILVER": 60, "BRONZE": 40}

# ── Typography ────────────────────────────────────────────────────────────────
# Segoe UI is Windows' Inter equivalent — clean and professional
FONT_DISPLAY  = ("Segoe UI", 23, "bold")
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_HEADING  = ("Segoe UI", 15, "bold")
FONT_SUBHEAD  = ("Segoe UI", 13, "bold")
FONT_SUBTITLE = ("Segoe UI", 13)
FONT_BODY     = ("Segoe UI", 12)      # form fields / body text
FONT_SMALL    = ("Segoe UI", 11)      # tips, secondary labels
FONT_CAPTION  = ("Segoe UI", 10)      # captions / hints (was 9 — too small)
FONT_MONO     = ("Consolas", 11)

# ── Layout ────────────────────────────────────────────────────────────────────
PAD     = 18
PAD_SM  = 10
PAD_LG  = 28

WIN_W   = 1060
WIN_H   = 700

HDR_H    = 62
NAV_H    = 58
BTN_H    = 34
BTN_H_LG = 44
BTN_R    = 6      # tighter radius — Sentry uses 6px not pill-shaped
BTN_R_SM = 4
CARD_R   = 8      # 8px card radius
CARD_R_LG = 10
ENTRY_H  = 40      # roomier so the larger form-field font isn't cramped
