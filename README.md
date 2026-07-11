# AstroSurfer

A Geometry Dash-style auto-runner: an astronaut on a hoverboard auto-scrolls
through space, dodging asteroids and debris, riding warp gates that flip
gravity, and grabbing boost orbs for an extra kick. A guided tutorial, 13
levels of increasing difficulty, named player profiles with persistent
progress, a lives/currency economy, and a cosmetics shop.

See [`GAME_DESIGN.md`](GAME_DESIGN.md) for the full design writeup (mechanics,
economy, level design, monetization approach).

## Setup

```
cd AstroSurfer
pip install -r requirements.txt
python audio_gen.py     # generates every level's music into assets/audio/ (run once)
python main.py
```

Requires Python 3.10+ and Pygame (installed via requirements.txt above).

## Controls

- **Space** or **Up Arrow** - thruster jump (also triggers a boost orb if you're
  overlapping one, and dismisses tutorial popups)
- **Up / Down Arrow** - move between menu options
- **Enter** or **Space** - confirm a menu selection
- **Esc** - pause during a run / back out of a menu
- Typing letters/numbers - enter a profile name on the name screen

## First run

The game opens on a profile picker - pick **+ New Profile**, type a name, and
press Enter. First-time profiles are dropped straight into the tutorial (no
life cost); after that, "Start" from the main menu goes to the level list.

## How it's put together

- `settings.py` - every tunable number (physics, colors, screen size) in one place
- `surfer.py` - the player's physics, jump/boost with coyote-time and jump
  buffering, gravity flip, rotation, hit-shake, and drawing
- `obstacles.py` - `Asteroid` (deadly), `Debris` (solid on every side - land on
  top, or bonk if you jump into its underside), `BoostOrb` (extra-high jump),
  `WarpPortal` (flips gravity)
- `level.py` - runs one playthrough: scrolling camera, collisions, scoring,
  tutorial popups, particles
- `levels/*.py` - each level's layout, authored as `(beat, obstacle_type, options)`
  tuples. Beats convert to pixel positions using the level's BPM, so obstacles
  land close to the beat of that level's generated music track (an approximate,
  hand-authored sync - not sample-accurate rhythm-game tooling).
- `level_generator.py` - procedurally builds obstacle layouts for a given
  difficulty tier using the same safe-spacing physics rules the first three
  hand-built levels were tuned against, so generated levels are collision-fair
  by construction (still bot-verified before shipping, not just trusted)
- `audio_gen.py` - synthesizes every level's looping backing track from scratch
  (square-wave arpeggio + kick + hi-hat) using only the standard library, so
  there are no external/copyrighted audio files to source
- `profile.py` - named player profiles: cumulative score, per-level bests,
  seen-feature tracking (for the "New: X" popups), the 24h lives economy, the
  Stardust Shards currency, and owned/equipped cosmetics. Persists to
  `profiles.json`. Automatically migrates an old flat `scores.json` (from
  before profiles existed) into a "Player" profile the first time it finds one.
- `ui.py` / `main.py` - menus, HUD, shop, tutorial popups, and the game's state
  machine

Want to change how a level plays? Edit its file in `levels/` - add, remove, or
move `(beat, type, options)` entries, or change `BPM`/`LENGTH_BEATS`. Re-run
`python audio_gen.py` after changing a level's `BPM` so the music stays in
tempo. Want a new generated level? Add a spec tuple to `make_levels`-style
generation (see `level_generator.generate_level`) and bot-verify it the same
way the shipped ones were (see Quality checks below).

## Economy notes (test-environment defaults)

- Profiles start with **10,000 Stardust Shards** and **3 free retries**,
  refilling every 24h (`profile.py`: `STARTING_CURRENCY`, `FREE_LIVES`,
  `LIVES_REFILL`).
- Running out of retries costs **150 Shards** to refill 3 more
  (`LIFE_REFILL_COST`).
- The cosmetics shop's real-money entries (see `profile.COSMETICS`,
  `price_usd`) are an architectural stub: `buy_cosmetic(..., pay_with="usd")`
  simulates a successful purchase and does **not** talk to any payment
  processor. Wiring up real payments is a separate, later integration.

## Quality checks

There's no bundled test suite in the shipped game (kept out of the runtime
footprint), but every level was verified with a headless "bot" that plays
using the same physics/collision code as the real game, plus a geometric
overlap audit and a timing-tolerance sweep, before being considered done. If
you add or edit a level, re-verify it the same way: instantiate `Level(module)`
headlessly (`SDL_VIDEODRIVER=dummy`), drive it with a simple reactive bot that
jumps when a hazard is within ~140px, and confirm it reaches `state ==
"complete"`.

## Porting to iPhone (a later step, not part of this build)

Pygame has no official iOS build tool, so this isn't a one-command port - but
the game's loop is already written in the `async`/`await` style that
[pygbag](https://github.com/pygame-web/pygbag) requires, so no rewrite is
needed to take this first step:

1. `pip install pygbag`
2. `pygbag main.py` - compiles the game to WebAssembly and serves it locally
   as a browser game
3. Host the exported build (e.g. GitHub Pages or any static file host)
4. On an iPhone, open the hosted page in Safari and use **Share -> Add to
   Home Screen** - this gives AstroSurfer an app-like icon and full-screen
   launch, with no App Store or Mac/Xcode required

A true native App Store app would mean rewriting the front-end in Kivy or
Swift/SpriteKit instead - a much bigger undertaking, only worth it if the
browser/home-screen version isn't enough. Real in-app-purchase support for the
cosmetics shop would need to be built at the same time as that native port
(StoreKit on iOS), replacing the current `pay_with="usd"` stub.
