"""Shared theme constants for the Windows GUI."""

APP_NAME = "Zambia Digital Hygiene Certification"
APP_VERSION = "1.0.0"

# Colours
CLR_BG        = "#0D1B2A"   # dark navy background
CLR_SURFACE   = "#1B2A3B"   # card / frame surface
CLR_ACCENT    = "#00C896"   # green accent (brand)
CLR_ACCENT2   = "#1E90FF"   # blue secondary accent
CLR_TEXT      = "#E6F1FF"   # primary text
CLR_MUTED     = "#7A8FA6"   # muted / secondary text
CLR_SURFACE_ALT = "#243447" # lighter surface tone
CLR_BORDER    = "#324659"   # subtle border accent
CLR_SUCCESS   = "#00C896"
CLR_WARNING   = "#FFB800"
CLR_DANGER    = "#FF4C4C"
CLR_GOLD      = "#FFD700"
CLR_SILVER    = "#C0C0C0"
CLR_BRONZE    = "#CD7F32"

# Fonts
FONT_TITLE    = ("Segoe UI", 26, "bold")
FONT_SUBHEADING = ("Segoe UI", 18, "semibold")
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_HEADING  = ("Segoe UI", 16, "bold")
FONT_BODY     = ("Segoe UI", 12)
FONT_SMALL    = ("Segoe UI", 10)
FONT_MONO     = ("Consolas", 11)

# Sizes
PAD           = 20
WIN_W         = 960
WIN_H         = 680

TIER_COLOURS = {
    "GOLD":          CLR_GOLD,
    "SILVER":        CLR_SILVER,
    "BRONZE":        CLR_BRONZE,
    "NOT CERTIFIED": CLR_DANGER,
}

TIER_THRESHOLD = {
    "GOLD":   80,
    "SILVER": 60,
    "BRONZE": 40,
}
