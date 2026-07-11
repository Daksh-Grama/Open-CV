# AstroSurfer - Game Design Document

**Genre:** Auto-scrolling rhythm-platformer (Geometry Dash-style)
**Platform (current):** Desktop, via Python/Pygame
**Platform (planned):** Browser via WebAssembly (pygbag), then iPhone via
"Add to Home Screen"; a native App Store build is a possible later step (see
`README.md`'s porting section)

## 1. Pitch

An astronaut on a hoverboard auto-scrolls through space. The player's only
input is *when* to fire the thruster. Success is entirely about timing:
clearing asteroids, riding debris platforms, grabbing boost orbs, and
surviving gravity-flipping warp tunnels, all loosely synced to a generated
electronic backing track.

## 2. Core loop

1. Pick a level from the list (or the tutorial).
2. The hoverboard scrolls forward automatically at a speed that ramps up
   over the run.
3. Press **Space/Up** to jump. Miss a hazard and the run ends immediately.
4. Reaching the end of the level banks a score; dying banks a partial score
   for distance covered.
5. Progress (score, completion, currency, retries) persists to the active
   profile and the player either retries, moves to the next level, or backs
   out to the level list.

## 3. Mechanics

| Mechanic | Behavior |
|---|---|
| **Jump** | Fires the thruster upward (JUMP_SPEED). Only usable when grounded, with a short **coyote-time** grace window (0.10s) after leaving a surface, and **jump buffering** (0.12s) so a slightly-early press still fires the instant you land. This was a deliberate feel fix - the raw "must be exactly grounded" rule read as an unresponsive cooldown. |
| **Asteroid** | Instant death on contact. Ground- or ceiling-mounted depending on current gravity. |
| **Debris** | A solid platform, not a hazard. It behaves like a real solid on *every* side: fall or rise onto it *with* gravity and you land on it; jump *against* gravity into its underside and you bonk off it and get knocked back the way you came, instead of clipping through. (This symmetric with-gravity/against-gravity rule was a direct bug fix - the original version only ever checked the "landing from above" case.) |
| **Boost Orb** | Touch it and press jump for a much bigger vertical kick (BOOST_SPEED, roughly 2x a normal jump's height) - enough to sail clean over a short cluster of hazards without landing between them. |
| **Warp Portal** | Instantly flips gravity direction. The world doesn't change, but "up" and "down" (for jumping and falling) swap, so the player rides the ceiling until the next portal flips it back. |
| **Scoring** | `score = distance_traveled + 50 x orbs_collected + 500 completion bonus`. Distance dominates, so longer/faster levels are worth more, and a full clear is always worth meaningfully more than dying just short of the end. |

## 4. Level design

### Beat-sync approach
Every level has a BPM. Obstacle positions are authored in "beats from level
start" and converted to world pixels via `seconds_per_beat x base scroll
speed`. The level's generated backing track is built from the same BPM, so
hazards land close to the beat. This is an **approximate, hand-tuned sync**,
not sample-accurate rhythm-game tooling - scroll speed ramps slightly over a
run for difficulty, which gradually drifts the sync late in a level. That
tradeoff was made deliberately in favor of a simpler, still-readable ramp
rather than a fully rigid tempo lock.

### Safe-spacing rules (why the levels are fair, not just "tuned by feel")
Every obstacle placement is bound by physics constants derived from the
actual jump/boost arcs (see `level_generator.py` for the full derivation):
a normal jump clears a hazard for ~0.586s of flight (~429px at the game's
top speed); a boost clears one for ~0.93s (~577px). Every generated level's
spacing keeps a safety margin over those numbers, tightening as difficulty
increases but never crossing the hard physics minimum. This is why new
levels can be generated procedurally and still be trustworthy: the
generator can't produce an impossible placement by construction, and every
level (hand-built or generated) is additionally verified by a headless bot
that plays it with the real physics/collision code before shipping.

### Difficulty curve
- **Tutorial** (BPM 80): jump, ride-up ledges, elevated platforms, boost
  orbs, one at a time, each behind a pausing popup explaining it.
- **Orbit Drop -> Solar Flare** (BPM 100-150, hand-authored): the original
  three levels, introducing debris, boost-orb clusters, and gravity-warp
  portals.
- **Comet Chase -> Singularity** (BPM 155-210, procedurally generated,
  difficulty 5.0-10.0): density and combo complexity ramp up - more
  frequent portals, ceiling-mounted hazards and platforms, tighter (but
  still verified-safe) spacing.

### Feature discovery
The first time a profile's level list includes a mechanic it hasn't seen
before (elevated platforms, boost orbs, warp portals), a non-blocking "New:
X" banner shows for the first few seconds of that run. The tutorial covers
the same ground but as blocking, dismissable popups, since a brand-new
player shouldn't be learning a mechanic while also trying not to die from it.

## 5. Progression & profiles

Profiles are named, local, and hold:
- Cumulative score across all runs (shown top-left during play and on the
  main menu)
- Per-level best completion % and best score
- Which mechanics have been introduced (drives the popup/banner system)
- Currency balance, lives state, owned/equipped cosmetics

Everything autosaves immediately after every attempt (death or completion),
not on a timer or on quit, so progress can't be lost to a crash.

## 6. Economy

- **Lives ("retries"):** 3 free per profile, refilling fully 24 real-world
  hours after they're depleted (timestamp-based, survives restarts). A life
  is spent when *starting* a real level (not the tutorial, and not
  navigating menus). Running out routes to a dedicated screen offering a
  currency-paid refill instead of blocking the game outright.
- **Stardust Shards (premium currency):** the in-game currency. Test
  profiles start with 10,000 for unrestricted QA; a refill costs 150.
- **Design intent:** lives create a light session-pacing mechanic (a
  reason to come back later) without ever hard-walling a player who's
  willing to spend currency - there's no mechanic that's *only* reachable
  by paying.

## 7. Monetization (cosmetics shop)

The shop sells cosmetics in two categories today (skins, death-effect
recolors) plus a hook for a third (full game "themes", e.g. a hypothetical
future medieval reskin) that's architecturally ready but has no content
built yet, per the brief that themes are future work.

Every cosmetic can be bought with Shards. A subset can *also* be bought
with real money (`price_usd` in `profile.COSMETICS`). **That real-money path
is currently a stub**: `buy_cosmetic(..., pay_with="usd")` simulates an
instant successful purchase and does not talk to any payment processor.
This was a deliberate scope decision, not an oversight - real payment
integration needs a payment SDK, business/legal setup (Apple/Google
merchant agreements, tax handling, etc.) that doesn't belong hardcoded into
a hobby project. The stub exists so the *mechanic* (browse, see a real-money
price, purchase, own, equip) is fully built and testable now; swapping in a
real payment SDK later is a drop-in replacement for that one function, not
a redesign.

Cosmetics currently change: the player sprite's body color (skins) and the
death explosion's particle color (death effects). Nothing about collision,
physics, or level layout is cosmetic-dependent - swapping art assets in
later (see Section 8) doesn't require touching gameplay code.

## 8. Visual & audio direction (for a future artist / audio pass)

Everything rendered today is procedural (pygame primitives: rects, polygons,
circles, a per-level color gradient) specifically so the collision shapes
and game feel could be nailed down *before* real art exists, and so a
future artist has a fully playable, fully-timed reference to design against
rather than a spec on paper. Concretely, a real art pass would replace:

- `surfer.py`'s `draw()` - currently a rounded body rect + visor circle +
  board rect + flame polygon, all built on the fly. A sprite sheet (idle,
  airborne tumble frames, thruster VFX) would drop in here; the collision
  `rect` is intentionally decoupled from the drawn shape already, so a
  visually larger/smaller sprite doesn't require touching physics.
- `obstacles.py`'s `draw()` methods - asteroids/debris/orbs/portals are
  simple shapes; sprites or particle-based VFX would replace these directly.
- The per-level gradient background + dot starfield in `level.py` - would
  become real parallax art layers.
- `audio_gen.py`'s synthesized tracks - a real composer's tracks would
  replace these, keeping the same BPM per level so obstacle timing stays in
  sync.

Cosmetic recolors (Section 7) are implemented as a color override passed
into the same draw calls, so they'll continue to work once those draw calls
are backed by real sprites (recoloring a sprite instead of a flat rect).

## 9. Technical notes

- Game loop is `async`/`await`-shaped from the start specifically so a
  browser export via `pygbag` (the planned next porting step) doesn't
  require restructuring the core loop.
- All persistence is flat JSON (`profiles.json`) - no database, intentional
  for a project this size.
- See `README.md` for the full file-by-file architecture breakdown and setup
  instructions.
