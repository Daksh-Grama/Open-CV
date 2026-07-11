"""Obstacle types placed along a level's track. Each obstacle has a fixed
position in "world" pixels (world_x); the Level converts that to a screen
position each frame using the current camera/scroll offset."""

import math
import pygame

import settings as s


class Obstacle:
    kind = "obstacle"

    def __init__(self, world_x, on_ceiling=False):
        self.world_x = world_x
        self.on_ceiling = on_ceiling
        self.triggered = False  # used by orbs/portals to fire only once

    def screen_rect(self, camera_x):
        raise NotImplementedError

    def draw(self, screen, camera_x):
        raise NotImplementedError


class Asteroid(Obstacle):
    """A deadly rock jutting up from the ground (or down from the ceiling
    when placed inside a gravity-flipped stretch)."""

    kind = "asteroid"
    WIDTH = 40
    HEIGHT = 44

    def screen_rect(self, camera_x):
        x = s.SURFER_X + (self.world_x - camera_x)
        if self.on_ceiling:
            y = s.CEILING_Y
        else:
            y = s.GROUND_Y - self.HEIGHT
        return pygame.Rect(int(x), int(y), self.WIDTH, self.HEIGHT)

    def draw(self, screen, camera_x):
        rect = self.screen_rect(camera_x)
        if rect.right < -20 or rect.left > s.SCREEN_W + 20:
            return
        if self.on_ceiling:
            points = [(rect.left, rect.top), (rect.right, rect.top), (rect.centerx, rect.bottom)]
        else:
            points = [(rect.left, rect.bottom), (rect.right, rect.bottom), (rect.centerx, rect.top)]
        pygame.draw.polygon(screen, s.ASTEROID_FILL, points)
        pygame.draw.polygon(screen, s.ASTEROID_EDGE, points, width=3)


class Debris(Obstacle):
    """A solid chunk of space junk the surfer can ride on top of (or
    underneath, when riding the ceiling). `gap` raises the block off the
    ground/ceiling baseline so it becomes a platform that must actually be
    jumped onto rather than walked straight up (gap=0 is a low ride-up
    ledge; gap>=45 clears a grounded surfer's standing height, so reaching
    it requires a real jump)."""

    kind = "debris"
    WIDTH = 90

    def __init__(self, world_x, height=36, gap=0, on_ceiling=False):
        super().__init__(world_x, on_ceiling)
        self.height = height
        self.gap = gap

    def screen_rect(self, camera_x):
        x = s.SURFER_X + (self.world_x - camera_x)
        if self.on_ceiling:
            y = s.CEILING_Y + self.gap
        else:
            y = s.GROUND_Y - self.gap - self.height
        return pygame.Rect(int(x), int(y), self.WIDTH, self.height)

    def draw(self, screen, camera_x):
        rect = self.screen_rect(camera_x)
        if rect.right < -20 or rect.left > s.SCREEN_W + 20:
            return
        pygame.draw.rect(screen, s.DEBRIS_FILL, rect, border_radius=6)
        pygame.draw.rect(screen, s.DEBRIS_EDGE, rect, width=3, border_radius=6)


class BoostOrb(Obstacle):
    """A glowing star that grants an extra thruster boost when the jump key
    is pressed while the surfer is overlapping it."""

    kind = "boost_orb"
    RADIUS = 15

    def __init__(self, world_x, y_offset=90, on_ceiling=False):
        super().__init__(world_x, on_ceiling)
        self.y_offset = y_offset  # distance from the ground/ceiling baseline

    def screen_rect(self, camera_x):
        x = s.SURFER_X + (self.world_x - camera_x)
        y = (s.GROUND_Y - self.y_offset) if not self.on_ceiling else (s.CEILING_Y + self.y_offset)
        return pygame.Rect(int(x - self.RADIUS), int(y - self.RADIUS), self.RADIUS * 2, self.RADIUS * 2)

    def draw(self, screen, camera_x, pulse=0.0):
        rect = self.screen_rect(camera_x)
        if rect.right < -20 or rect.left > s.SCREEN_W + 20:
            return
        glow_r = self.RADIUS + 5 + int(3 * math.sin(pulse))
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*s.BOOST_ORB_COLOR, 70), (glow_r, glow_r), glow_r)
        screen.blit(glow, glow.get_rect(center=rect.center))
        pygame.draw.circle(screen, s.BOOST_ORB_COLOR, rect.center, self.RADIUS)


class WarpPortal(Obstacle):
    """A full-height gate that flips gravity the instant the surfer passes
    through it."""

    kind = "warp_portal"
    WIDTH = 26

    def screen_rect(self, camera_x):
        x = s.SURFER_X + (self.world_x - camera_x)
        return pygame.Rect(int(x), s.CEILING_Y, self.WIDTH, s.GROUND_Y - s.CEILING_Y)

    def draw(self, screen, camera_x):
        rect = self.screen_rect(camera_x)
        if rect.right < -20 or rect.left > s.SCREEN_W + 20:
            return
        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        glow.fill((*s.WARP_PORTAL_COLOR, 90))
        screen.blit(glow, rect)
        pygame.draw.rect(screen, s.WARP_PORTAL_COLOR, rect, width=3)
