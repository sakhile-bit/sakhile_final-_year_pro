"""Shared design system — all UI constants live here."""

APP_NAME    = "Zambia Digital Hygiene Certification"
APP_VERSION = "2.0.0"

# ── Colour palette ────────────────────────────────────────────────────────────
CLR_BG          = "#0B1622"   # deep navy page background
CLR_SURFACE     = "#152030"   # card / panel surface
CLR_SURFACE_ALT = "#1E2E42"   # slightly lighter surface (input fields, hover)
CLR_SURFACE_HVR = "#243447"   # hover state for surface elements
CLR_BORDER      = "#2A3D54"   # subtle border
CLR_DIVIDER     = "#1E2E42"   # horizontal rule / separator

CLR_ACCENT      = "#00C896"   # primary green (CTAs, highlights)
CLR_ACCENT_HOV  = "#00A87A"   # green hover
CLR_ACCENT_DIM  = "#004D3A"   # very dark green (pressed / dimmed)
CLR_BLUE        = "#2485E8"   # secondary blue accent
CLR_AMBER       = "#F0A500"   # warning / amber

CLR_TEXT        = "#E8F1FF"   # primary text
CLR_TEXT_SEC    = "#A8BCCC"   # secondary / subheading text
CLR_MUTED       = "#6A8099"   # muted / caption text

CLR_SUCCESS     = "#00C896"
CLR_WARNING     = "#F0A500"
CLR_DANGER      = "#E84040"

CLR_GOLD        = "#F5C518"
CLR_SILVER      = "#C8D0D8"
CLR_BRONZE      = "#CD8A3A"

TIER_COLOURS = {
    "GOLD":          CLR_GOLD,
    "SILVER":        CLR_SILVER,
    "BRONZE":        CLR_BRONZE,
    "NOT CERTIFIED": CLR_DANGER,
}

TIER_THRESHOLD = {"GOLD": 80, "SILVER": 60, "BRONZE": 40}

# ── Typography ────────────────────────────────────────────────────────────────
FONT_DISPLAY  = ("Segoe UI", 26, "bold")    # hero title
FONT_TITLE    = ("Segoe UI", 20, "bold")    # screen section title
FONT_HEADING  = ("Segoe UI", 15, "bold")    # card heading
FONT_SUBHEAD  = ("Segoe UI", 13, "bold")    # subheading
FONT_SUBTITLE = ("Segoe UI", 13)            # subtitle / description
FONT_BODY     = ("Segoe UI", 12)            # body copy
FONT_SMALL    = ("Segoe UI", 11)            # captions, labels
FONT_CAPTION  = ("Segoe UI", 10)            # very small labels
FONT_MONO     = ("Consolas", 11)            # monospace

# ── Layout ────────────────────────────────────────────────────────────────────
PAD     = 20       # standard padding
PAD_SM  = 12       # small padding
PAD_LG  = 32       # large padding

WIN_W   = 980
WIN_H   = 700

# Component sizes
HDR_H   = 68       # screen header height
NAV_H   = 64       # bottom nav bar height
BTN_H   = 38       # standard button height
BTN_H_LG = 48      # large/primary button height
BTN_R   = 20       # button corner radius
BTN_R_SM = 10      # small button corner radius
CARD_R  = 14       # card corner radius
CARD_R_LG = 18     # large card corner radius
ENTRY_H = 42       # input field height
