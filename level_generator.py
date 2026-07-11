"""Procedurally builds a level's obstacle layout from a difficulty tier,
using the same safe-spacing physics rules that were hand-derived and
bot-verified for the original three levels. This keeps every generated
level collision-fair by construction instead of hand-tuning each one.

Physics recap (see settings.py): a normal jump (JUMP_SPEED=900,
GRAVITY=2600) clears a 44px-tall hazard for ~0.586s of flight and covers
~429px of world distance in that time at the game's top speed (620px/s).
A boost (BOOST_SPEED=1300) clears the same hazard for ~0.93s (~577px at
top speed). Every spacing constant below is derived from those numbers
with a safety margin, then the whole level is still bot-playtested before
shipping - this file makes "probably fine" levels, the bot makes them
"confirmed fine".
"""

import colorsys
import random

import settings as s

HAZARD_HEIGHT = 44.0
JUMP_FLIGHT_TIME = 2 * s.JUMP_SPEED / s.GRAVITY
JUMP_SAFE_DISTANCE_PX = JUMP_FLIGHT_TIME * s.MAX_SCROLL_SPEED * 0.85  # 15% safety margin
BOOST_FLIGHT_TIME = 2 * s.BOOST_SPEED / s.GRAVITY
BOOST_SAFE_DISTANCE_PX = BOOST_FLIGHT_TIME * s.MAX_SCROLL_SPEED * 0.85

PORTAL_TRANSIT_BUFFER_PX = 650  # time for gravity to carry the surfer across the tunnel
MAX_LEDGE_ELEVATION_PX = 140    # gap + height a normal jump can still reach
LEAD_IN_BEATS = 4               # quiet beats before the first hazard


def _px_to_beats(px, px_per_beat):
    return px / px_per_beat


def _difficulty_margin(difficulty):
    """1.0 = easiest (most buffer over the hard physics minimum),
    10.0 = hardest (spacing hugs the minimum)."""
    t = (difficulty - 1) / 9.0  # 0..1
    return 1.45 - 0.40 * t      # 1.45 down to 1.05


def _theme_for_index(index, total):
    hue = (index / max(1, total)) % 1.0
    top = colorsys.hsv_to_rgb(hue, 0.55, 0.20)
    bottom = colorsys.hsv_to_rgb(hue, 0.65, 0.38)
    accent = colorsys.hsv_to_rgb(hue, 0.55, 1.0)
    to255 = lambda c: tuple(int(x * 255) for x in c)
    return {"bg_top": to255(top), "bg_bottom": to255(bottom), "accent": to255(accent)}


def generate_level(name, key, bpm, length_beats, difficulty, seed, theme=None):
    """Returns (OBSTACLES list, THEME dict). `difficulty` is 1-10."""
    rnd = random.Random(seed)
    px_per_beat = (60.0 / bpm) * s.BASE_SCROLL_SPEED
    margin = _difficulty_margin(difficulty)

    solo_gap_beats = _px_to_beats(JUMP_SAFE_DISTANCE_PX * margin, px_per_beat)
    ledge_gap_beats = solo_gap_beats  # elevated ledges use the same solo-hazard spacing
    portal_buffer_beats = _px_to_beats(PORTAL_TRANSIT_BUFFER_PX, px_per_beat)
    orb_lead_beats = _px_to_beats(160, px_per_beat)
    orb_step_beats = _px_to_beats(80, px_per_beat)

    unlock_ledges = difficulty >= 2
    unlock_portals = difficulty >= 4
    unlock_orbs = difficulty >= 3
    double_portal_section = difficulty >= 7
    ceiling_ledges = difficulty >= 6

    # An orb's boost clears a 44px hazard for ~1.0s of flight (~527px at
    # top speed with margin). Earlier hand-tuned levels proved a lead of
    # 180px + 2 asteroids at 70px spacing (250px total span) is reliably
    # safe; a 3rd/4th asteroid pushes the span close enough to the boost's
    # safe-window edge that it becomes speed-dependent and fragile (this
    # was confirmed by the bot catching exactly that failure). So the
    # cluster size is fixed, not difficulty-scaled.
    ORB_CLUSTER_SIZE = 2

    obstacles = []
    beat = float(LEAD_IN_BEATS)
    on_ceiling = False

    def place(kind, **kwargs):
        obstacles.append((round(beat, 3), kind, dict(kwargs)))

    while beat < length_beats - solo_gap_beats:
        roll = rnd.random()

        if unlock_portals and roll < 0.12 and not on_ceiling:
            place("warp_portal")
            beat += portal_buffer_beats
            on_ceiling = True
            n_hazards = 2 if not double_portal_section else rnd.randint(2, 3)
            for _ in range(n_hazards):
                if ceiling_ledges and rnd.random() < 0.35:
                    gap = rnd.uniform(50, MAX_LEDGE_ELEVATION_PX - 40)
                    place("debris", height=30, gap=round(gap), on_ceiling=True)
                else:
                    place("asteroid", on_ceiling=True)
                beat += ledge_gap_beats
            place("warp_portal")
            beat += portal_buffer_beats
            on_ceiling = False
            continue

        if unlock_orbs and roll < 0.30:
            place("boost_orb", y_offset=20)
            beat += orb_lead_beats
            for _ in range(ORB_CLUSTER_SIZE):
                place("asteroid")
                beat += orb_step_beats
            beat += solo_gap_beats - ORB_CLUSTER_SIZE * orb_step_beats
            continue

        if unlock_ledges and roll < 0.55:
            if rnd.random() < 0.5:
                place("debris", height=round(rnd.uniform(28, 42)))
            else:
                gap = rnd.uniform(50, MAX_LEDGE_ELEVATION_PX - 35)
                place("debris", height=30, gap=round(gap))
            beat += ledge_gap_beats
            continue

        place("asteroid")
        beat += solo_gap_beats

    return obstacles, (theme or _theme_for_index(hash(key) % 97, 97))
