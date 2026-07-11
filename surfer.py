"""The player character: an astronaut riding a hoverboard."""

import random

import pygame

import settings as s


class Surfer:
    COYOTE_TIME = 0.10        # grace window to still jump just after leaving a surface
    JUMP_BUFFER_TIME = 0.12   # a jump pressed just before landing fires the instant you land
    BONK_NUDGE = 150.0
    HIT_SHAKE_DURATION = 0.25

    def __init__(self, skin_color=None):
        self.rect = pygame.Rect(0, 0, s.SURFER_SIZE, s.SURFER_SIZE)
        self.rect.x = s.SURFER_X
        self.rect.bottom = s.GROUND_Y
        self.skin_color = skin_color or s.SURFER_BODY

        self.vel_y = 0.0
        self.gravity_dir = 1       # +1 = normal (falls down), -1 = flipped (falls up)
        self.grounded = True
        self.alive = True
        self.angle = 0.0           # visual tumble angle while airborne
        self.thrusting = False     # true for a few frames after a jump/boost, for the flame vfx

        self._thrust_timer = 0.0
        self._coyote_timer = 0.0
        self._jump_buffer_timer = 0.0
        self.hit_shake_timer = 0.0

    # -- input -----------------------------------------------------------
    def jump(self):
        if self.grounded or self._coyote_timer > 0:
            self._do_jump(s.JUMP_SPEED)
        else:
            self._jump_buffer_timer = self.JUMP_BUFFER_TIME

    def boost(self):
        """Extra kick from a BoostOrb, works even while airborne."""
        self._do_jump(s.BOOST_SPEED)

    def _do_jump(self, speed):
        self.vel_y = -speed * self.gravity_dir
        self.grounded = False
        self._coyote_timer = 0.0
        self._jump_buffer_timer = 0.0
        self._thrust_timer = 0.12

    def flip_gravity(self):
        self.gravity_dir *= -1
        self.grounded = False
        self._coyote_timer = 0.0

    def trigger_hit_shake(self):
        self.hit_shake_timer = self.HIT_SHAKE_DURATION

    def tick_shake(self, dt):
        if self.hit_shake_timer > 0:
            self.hit_shake_timer = max(0.0, self.hit_shake_timer - dt)

    # -- physics -----------------------------------------------------------
    def update(self, dt):
        """Physics integration only. `grounded` is left for Level to
        re-resolve this frame via resolve_world_bounds()/obstacle checks -
        see finalize_frame() for the coyote/buffer/animation follow-up."""
        self.vel_y += s.GRAVITY * self.gravity_dir * dt
        self.vel_y = max(-s.TERMINAL_FALL_SPEED, min(s.TERMINAL_FALL_SPEED, self.vel_y))
        self.rect.y += round(self.vel_y * dt)

        if self._thrust_timer > 0:
            self._thrust_timer -= dt
        self.thrusting = self._thrust_timer > 0

    def finalize_frame(self, dt):
        """Called once Level has resolved ground/obstacle collisions for
        this frame: updates coyote time, fires any buffered jump the
        instant we land, and drives the airborne tumble animation from the
        now-confirmed grounded state."""
        if self.grounded:
            self._coyote_timer = self.COYOTE_TIME
            self.angle = 0.0
        else:
            if self._coyote_timer > 0:
                self._coyote_timer -= dt
            self.angle = (self.angle + 540 * dt) % 360

        if self._jump_buffer_timer > 0:
            self._jump_buffer_timer -= dt
            if self.grounded:
                self._do_jump(s.JUMP_SPEED)

    def resolve_world_bounds(self):
        """Land on the level's baseline floor/ceiling (used when no debris
        platform is underfoot)."""
        if self.gravity_dir == 1:
            floor = s.GROUND_Y - self.rect.height
            if self.rect.top >= floor:
                self.rect.top = floor
                self.vel_y = 0.0
                self.grounded = True
        else:
            if self.rect.top <= s.CEILING_Y:
                self.rect.top = s.CEILING_Y
                self.vel_y = 0.0
                self.grounded = True

    def land_on(self, surface_y, from_above):
        """Snap onto a debris platform edge."""
        if from_above:
            self.rect.bottom = surface_y
        else:
            self.rect.top = surface_y
        self.vel_y = 0.0
        self.grounded = True

    def bonk_from_below(self, block_bottom_y):
        """Hit the underside of a block while rising into it - get knocked
        back down instead of clipping through."""
        self.rect.top = block_bottom_y
        self.vel_y = self.BONK_NUDGE
        self.grounded = False

    def bonk_from_above(self, block_top_y):
        """Hit the topside of a block while moving away from the ceiling
        into it (flipped-gravity equivalent of bonk_from_below)."""
        self.rect.bottom = block_top_y
        self.vel_y = -self.BONK_NUDGE
        self.grounded = False

    # -- rendering -----------------------------------------------------------
    def draw(self, screen):
        size = self.rect.width
        pad = size  # extra room for the board + flame
        icon = pygame.Surface((size + pad, size + pad), pygame.SRCALPHA)
        cx, cy = icon.get_width() // 2, icon.get_height() // 2

        if self.thrusting:
            flame_len = 16 + int(6 * abs(self.vel_y) / s.JUMP_SPEED)
            flame_dir = 1 if self.gravity_dir == 1 else -1
            flame_points = [
                (cx - size // 2 + 4, cy + flame_dir * size // 2),
                (cx + size // 2 - 4, cy + flame_dir * size // 2),
                (cx, cy + flame_dir * (size // 2 + flame_len)),
            ]
            pygame.draw.polygon(icon, s.THRUSTER_FLAME, flame_points)

        board_rect = pygame.Rect(0, 0, size + 6, 8)
        board_rect.center = (cx, cy + size // 2)
        pygame.draw.rect(icon, s.SURFER_BOARD, board_rect, border_radius=4)

        body_rect = pygame.Rect(0, 0, size, size)
        body_rect.center = (cx, cy)
        pygame.draw.rect(icon, self.skin_color, body_rect, border_radius=8)

        visor_radius = size // 4
        pygame.draw.circle(icon, s.SURFER_VISOR, (cx + size // 6, cy - size // 8), visor_radius)

        rotated = pygame.transform.rotate(icon, self.angle)
        dest = rotated.get_rect(center=self.rect.center)

        if self.hit_shake_timer > 0:
            strength = 6 * (self.hit_shake_timer / self.HIT_SHAKE_DURATION)
            dest.x += random.uniform(-strength, strength)
            dest.y += random.uniform(-strength, strength)

        screen.blit(rotated, dest)
