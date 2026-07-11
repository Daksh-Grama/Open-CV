"""Runs a single playthrough of one level: scrolls the camera, spawns and
collides obstacles, and owns the Surfer + particle system for that run."""

import random

import pygame

import settings as s
from surfer import Surfer
from stardust import ParticleSystem
from obstacles import Asteroid, Debris, BoostOrb, WarpPortal

OBSTACLE_CLASSES = {
    "asteroid": Asteroid,
    "debris": Debris,
    "boost_orb": BoostOrb,
    "warp_portal": WarpPortal,
}

FEATURE_LABELS = {
    "elevated_ledge": "Elevated Platforms",
    "ledge": "Platforms",
    "boost_orb": "Boost Orbs",
    "warp_portal": "Gravity Warp Portals",
}


def features_used(module):
    """Which non-basic mechanics this level's layout touches, keyed the
    same way profile.mark_feature_seen() expects."""
    found = set()
    for _beat, kind, kwargs in module.OBSTACLES:
        if kind == "boost_orb":
            found.add("boost_orb")
        elif kind == "warp_portal":
            found.add("warp_portal")
        elif kind == "debris":
            found.add("elevated_ledge" if kwargs.get("gap", 0) > 0 else "ledge")
    return found


COMPLETE_BONUS = 500
ORB_BONUS = 50


def _build_gradient(top_color, bottom_color):
    surf = pygame.Surface((1, s.SCREEN_H))
    for y in range(s.SCREEN_H):
        t = y / (s.SCREEN_H - 1)
        color = [int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3)]
        surf.set_at((0, y), color)
    return pygame.transform.scale(surf, (s.SCREEN_W, s.SCREEN_H))


class Level:
    def __init__(self, module, skin_color=None, death_fx_color=None):
        self.module = module
        self.name = module.NAME
        self.key = module.KEY
        self.bpm = module.BPM
        self.theme = module.THEME
        self.death_fx_color = death_fx_color or s.UI_DANGER

        seconds_per_beat = 60.0 / self.bpm
        self.px_per_beat = seconds_per_beat * s.BASE_SCROLL_SPEED
        self.length_world = module.LENGTH_BEATS * self.px_per_beat

        self.obstacles = [self._build_obstacle(spec) for spec in module.OBSTACLES]
        self.surfer = Surfer(skin_color=skin_color)
        self.particles = ParticleSystem()

        self.camera_x = 0.0
        self.scroll_speed = s.BASE_SCROLL_SPEED
        self.elapsed = 0.0
        self.progress = 0.0
        self.state = "playing"  # "playing" | "dead" | "complete"
        self.orbs_collected = 0

        self._popups = [(beat * self.px_per_beat, key) for beat, key in getattr(module, "TUTORIAL_POPUPS", [])]
        self.pending_popup = None
        self.paused_for_popup = False

        self._bg_surface = _build_gradient(self.theme["bg_top"], self.theme["bg_bottom"])
        self._stars = self._build_starfield()
        self._trail_timer = 0.0

    @property
    def score(self):
        bonus = COMPLETE_BONUS if self.state == "complete" else 0
        return int(self.camera_x) + self.orbs_collected * ORB_BONUS + bonus

    def dismiss_popup(self):
        self.pending_popup = None
        self.paused_for_popup = False

    def _build_obstacle(self, spec):
        beat, kind, kwargs = spec
        world_x = beat * self.px_per_beat
        cls = OBSTACLE_CLASSES[kind]
        return cls(world_x, **kwargs)

    def _build_starfield(self):
        rnd = random.Random(hash(self.key) & 0xFFFFFFFF)
        stars = []
        for _ in range(90):
            layer = rnd.choice((0.15, 0.35, 0.6))
            stars.append({
                "x": rnd.uniform(0, s.SCREEN_W * 2),
                "y": rnd.uniform(0, s.SCREEN_H),
                "layer": layer,
                "radius": 1 if layer < 0.4 else 2,
                "color": s.STAR_DIM if layer < 0.4 else s.STAR_BRIGHT,
            })
        return stars

    # -- input / simulation -----------------------------------------------
    def handle_jump_press(self):
        if self.state != "playing":
            return
        for obs in self.obstacles:
            if isinstance(obs, BoostOrb) and not obs.triggered:
                if obs.screen_rect(self.camera_x).colliderect(self.surfer.rect):
                    self.surfer.boost()
                    obs.triggered = True
                    self.orbs_collected += 1
                    return
        self.surfer.jump()

    def update(self, dt):
        if self.state != "playing":
            return
        if self.paused_for_popup:
            return

        if self._popups and self.camera_x >= self._popups[0][0]:
            _, key = self._popups.pop(0)
            self.pending_popup = key
            self.paused_for_popup = True
            return

        self.elapsed += dt
        self.scroll_speed = min(s.MAX_SCROLL_SPEED, s.BASE_SCROLL_SPEED + s.SCROLL_SPEED_RAMP * self.elapsed)
        self.camera_x += self.scroll_speed * dt
        self.progress = max(self.progress, min(1.0, self.camera_x / self.length_world))

        self.surfer.grounded = False  # tentative; re-confirmed below this frame
        self.surfer.update(dt)
        self.surfer.resolve_world_bounds()
        self._resolve_obstacles()
        self.surfer.finalize_frame(dt)
        self._spawn_trail(dt)
        self.particles.update(dt)

        if self.state == "playing" and self.camera_x >= self.length_world:
            self.state = "complete"

    def _resolve_obstacles(self):
        surfer = self.surfer
        for obs in self.obstacles:
            rect = obs.screen_rect(self.camera_x)
            if not rect.colliderect(surfer.rect):
                continue
            if isinstance(obs, Asteroid):
                self._kill()
                return
            elif isinstance(obs, Debris):
                self._resolve_debris(obs, rect)
            elif isinstance(obs, WarpPortal) and not obs.triggered:
                obs.triggered = True
                surfer.flip_gravity()

    def _resolve_debris(self, obs, rect):
        """Debris is solid on every side: falling/rising onto it with
        gravity lands you on it, but moving against gravity into it (e.g.
        jumping up into its underside) bonks you back instead of letting
        you clip straight through."""
        surfer = self.surfer
        with_gravity = (surfer.vel_y * surfer.gravity_dir) >= 0
        if surfer.gravity_dir == 1:
            if with_gravity:
                if surfer.rect.bottom >= rect.top:
                    surfer.land_on(rect.top, from_above=True)
            else:
                if surfer.rect.top <= rect.bottom:
                    surfer.bonk_from_below(rect.bottom)
        else:
            if with_gravity:
                if surfer.rect.top <= rect.bottom:
                    surfer.land_on(rect.bottom, from_above=False)
            else:
                if surfer.rect.bottom >= rect.top:
                    surfer.bonk_from_above(rect.top)

    def _kill(self):
        self.surfer.alive = False
        self.surfer.trigger_hit_shake()
        self.state = "dead"
        self.particles.spawn_burst(self.surfer.rect.centerx, self.surfer.rect.centery, self.death_fx_color)

    def _spawn_trail(self, dt):
        self._trail_timer -= dt
        if self._trail_timer > 0:
            return
        self._trail_timer = 0.03
        surfer = self.surfer
        trail_y = surfer.rect.top if surfer.gravity_dir == 1 else surfer.rect.bottom
        color = s.THRUSTER_FLAME if surfer.thrusting else s.DEBRIS_FILL
        self.particles.spawn_trail(surfer.rect.centerx, trail_y, color)

    # -- rendering -----------------------------------------------------------
    def draw(self, screen):
        screen.blit(self._bg_surface, (0, 0))
        self._draw_starfield(screen)

        accent = self.theme["accent"]
        pygame.draw.rect(screen, accent, (0, s.GROUND_Y, s.SCREEN_W, 3))
        pygame.draw.rect(screen, accent, (0, s.CEILING_Y - 3, s.SCREEN_W, 3))

        for obs in self.obstacles:
            obs.draw(screen, self.camera_x)

        self.particles.draw(screen)
        if self.surfer.alive or self.surfer.hit_shake_timer > 0:
            self.surfer.draw(screen)

    def _draw_starfield(self, screen):
        tile_w = s.SCREEN_W * 2
        for star in self._stars:
            x = (star["x"] - self.camera_x * star["layer"]) % tile_w
            if x > s.SCREEN_W:
                continue
            pygame.draw.circle(screen, star["color"], (int(x), int(star["y"])), star["radius"])
