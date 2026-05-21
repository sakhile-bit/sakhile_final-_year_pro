"""Design system — all visual constants for the Zambia Digital Hygiene app."""

APP_NAME    = "Zambia Digital Hygiene Certification"
APP_VERSION = "2.0.0"

# ── Colour palette ────────────────────────────────────────────────────────────
CLR_BRAND       = "#070F1A"   # left brand panel background
CLR_BG          = "#0B1622"   # page / window background
CLR_SURFACE     = "#132236"   # card surface
CLR_SURFACE_ALT = "#1A2D42"   # inputs, secondary surfaces
CLR_SURFACE_HVR = "#1E3350"   # hover states
CLR_BORDER      = "#243D58"   # card borders
CLR_DIVIDER     = "#192E43"   # horizontal rules

CLR_ACCENT      = "#00C896"   # primary green (brand CTA)
CLR_ACCENT_HOV  = "#00B085"   # green hover
CLR_ACCENT_DIM  = "#003D28"   # dark green (hover bg for ghost btns)
CLR_BLUE        = "#2485E8"   # secondary accent
CLR_BLUE_DIM    = "#0D2744"   # blue dim
CLR_AMBER       = "#F0A500"   # warning / amber
CLR_AMBER_DIM   = "#2A1E00"   # amber dim

CLR_TEXT        = "#ECF4FF"   # primary text
CLR_TEXT_SEC    = "#A0B4C8"   # secondary text
CLR_MUTED       = "#5A7490"   # muted / caption

CLR_SUCCESS     = "#00C896"
CLR_WARNING     = "#F0A500"
CLR_DANGER      = "#E84040"
CLR_DANGER_DIM  = "#2D0A0A"

CLR_GOLD        = "#F5C518"
CLR_SILVER      = "#C0CDD8"
CLR_BRONZE      = "#D4873A"

TIER_COLOURS = {
    "GOLD":          CLR_GOLD,
    "SILVER":        CLR_SILVER,
    "BRONZE":        CLR_BRONZE,
    "NOT CERTIFIED": CLR_DANGER,
}

TIER_THRESHOLD = {"GOLD": 80, "SILVER": 60, "BRONZE": 40}

# ── Typography ────────────────────────────────────────────────────────────────
FONT_DISPLAY  = ("Segoe UI", 24, "bold")
FONT_TITLE    = ("Segoe UI", 18, "bold")
FONT_HEADING  = ("Segoe UI", 15, "bold")
FONT_SUBHEAD  = ("Segoe UI", 13, "bold")
FONT_SUBTITLE = ("Segoe UI", 13)
FONT_BODY     = ("Segoe UI", 12)
FONT_SMALL    = ("Segoe UI", 11)
FONT_CAPTION  = ("Segoe UI", 10)
FONT_MONO     = ("Consolas", 11)

# ── Spacing ───────────────────────────────────────────────────────────────────
PAD     = 20
PAD_SM  = 12
PAD_LG  = 32

# ── Window ────────────────────────────────────────────────────────────────────
WIN_W   = 1040
WIN_H   = 700

# ── Components ────────────────────────────────────────────────────────────────
HDR_H    = 68
NAV_H    = 64
BTN_H    = 38
BTN_H_LG = 50
BTN_R    = 20
BTN_R_SM = 10
CARD_R   = 14
CARD_R_LG= 18
ENTRY_H  = 40
