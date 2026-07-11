"""A small particle system: a stardust trail behind the hoverboard, and an
explosion burst when the surfer is destroyed."""

import math
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "radius", "color")

    def __init__(self, x, y, vx, vy, life, radius, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.radius = radius
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, screen):
        fade = max(0.0, self.life / self.max_life)
        radius = max(1, int(self.radius * fade))
        alpha = int(255 * fade)
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (radius, radius), radius)
        screen.blit(surf, (self.x - radius, self.y - radius))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_trail(self, x, y, color):
        self.particles.append(
            Particle(
                x + random.uniform(-4, 4),
                y + random.uniform(-4, 4),
                vx=random.uniform(-40, -10),
                vy=random.uniform(-20, 20),
                life=random.uniform(0.25, 0.45),
                radius=random.uniform(2, 4),
                color=color,
            )
        )

    def spawn_burst(self, x, y, color, count=28):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 260)
            self.particles.append(
                Particle(
                    x, y,
                    vx=speed * pygame.math.Vector2(1, 0).rotate_rad(angle).x,
                    vy=speed * pygame.math.Vector2(1, 0).rotate_rad(angle).y,
                    life=random.uniform(0.35, 0.7),
                    radius=random.uniform(2, 5),
                    color=color,
                )
            )

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)

    def clear(self):
        self.particles.clear()
