"""Shared constants for AstroSurfer. Keeping every tunable number in one
place makes it easy to rebalance the feel of the game without hunting
through every file."""

TITLE = "AstroSurfer"

SCREEN_W, SCREEN_H = 960, 540
FPS = 60

# --- world geometry -----------------------------------------------------
GROUND_Y = SCREEN_H - 110      # the "floor" the surfer normally rides on
CEILING_Y = 110                # the "ceiling" used when gravity is flipped
SURFER_X = 220                 # fixed on-screen x position of the surfer
SURFER_SIZE = 40

# --- physics (pixels / second, pixels / second^2) ------------------------
GRAVITY = 2600.0
JUMP_SPEED = 900.0             # initial upward speed of a thruster jump
BOOST_SPEED = 1300.0           # extra kick granted by a BoostOrb (~2x jump height)
TERMINAL_FALL_SPEED = 1600.0

BASE_SCROLL_SPEED = 360.0      # px/s at the start of a level
SCROLL_SPEED_RAMP = 4.0        # px/s scroll speed gained per second survived
MAX_SCROLL_SPEED = 620.0

PIXELS_PER_BEAT_UNIT = 90      # spacing used when authoring level layouts

# --- colors ---------------------------------------------------------------
WHITE = (235, 240, 255)
BLACK = (8, 8, 14)
STAR_DIM = (90, 100, 130)
STAR_BRIGHT = (230, 235, 255)

SURFER_BODY = (225, 230, 245)
SURFER_VISOR = (90, 220, 255)
SURFER_BOARD = (120, 130, 160)
THRUSTER_FLAME = (255, 150, 60)

ASTEROID_FILL = (130, 115, 105)
ASTEROID_EDGE = (70, 60, 55)
DEBRIS_FILL = (80, 210, 195)
DEBRIS_EDGE = (30, 110, 105)
BOOST_ORB_COLOR = (255, 210, 80)
WARP_PORTAL_COLOR = (200, 90, 255)

UI_TEXT = (235, 240, 255)
UI_DIM = (150, 160, 190)
UI_ACCENT = (90, 220, 255)
UI_DANGER = (255, 100, 110)
UI_PANEL = (18, 18, 32)

# --- input ------------------------------------------------------------
JUMP_KEYS = ("space", "up")
