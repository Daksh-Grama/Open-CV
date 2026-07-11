"""Keyboard-driven menus and HUD overlays."""

import pygame

import settings as s

_FONT_CACHE = {}


def get_font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont("consolas,couriernew,monospace", size, bold=bold)
    return _FONT_CACHE[key]


def draw_text(screen, text, size, color, center, bold=False):
    if not text:
        return
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=center))


def draw_text_topleft(screen, text, size, color, pos, bold=False):
    if not text:
        return
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(topleft=pos))


def draw_text_topright(screen, text, size, color, pos, bold=False):
    if not text:
        return
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(topright=pos))


class Menu:
    """A simple keyboard-driven vertical list of options. Each option is
    either a plain label string, or an (label, detail) tuple where detail
    is a smaller line of extra info shown underneath."""

    def __init__(self, options):
        self.options = []
        self.selected = 0
        self.set_options(options)

    def set_options(self, options):
        self.options = list(options)
        self.selected = 0

    def navigate(self, delta):
        if not self.options:
            return
        self.selected = (self.selected + delta) % len(self.options)

    def selected_label(self):
        opt = self.options[self.selected]
        return opt[0] if isinstance(opt, tuple) else opt

    def draw(self, screen, title="", subtitle=None, y_start=220, spacing=52):
        if title:
            draw_text(screen, title, 44, s.UI_TEXT, (s.SCREEN_W // 2, 110), bold=True)
        if subtitle:
            draw_text(screen, subtitle, 18, s.UI_DIM, (s.SCREEN_W // 2, 150))

        # Long lists get a scrolling window so entries never run off the
        # bottom of the screen: only `max_visible` rows are drawn at once,
        # sliding to keep the current selection in view.
        bottom_margin = 32
        max_visible = max(1, (s.SCREEN_H - bottom_margin - y_start) // spacing)
        total = len(self.options)
        if total > max_visible:
            start = max(0, min(self.selected - max_visible // 2, total - max_visible))
        else:
            start = 0
        end = min(total, start + max_visible)

        if start > 0:
            draw_text(screen, "^ more above", 13, s.UI_DIM, (s.SCREEN_W // 2, y_start - 18))
        if end < total:
            draw_text(screen, "v more below", 13, s.UI_DIM, (s.SCREEN_W // 2, y_start + (end - start) * spacing + 2))

        for row, i in enumerate(range(start, end)):
            opt = self.options[i]
            label = opt[0] if isinstance(opt, tuple) else opt
            detail = opt[1] if isinstance(opt, tuple) else None
            color = s.UI_ACCENT if i == self.selected else s.UI_TEXT
            prefix = "> " if i == self.selected else "  "
            y = y_start + row * spacing
            draw_text(screen, f"{prefix}{label}", 28, color, (s.SCREEN_W // 2, y))
            if detail:
                draw_text(screen, detail, 15, s.UI_DIM, (s.SCREEN_W // 2, y + 22))


class TextInput:
    """Minimal single-line text entry box, used for naming a profile."""

    def __init__(self, max_len=16):
        self.buffer = ""
        self.max_len = max_len

    def handle_text(self, char):
        if len(self.buffer) < self.max_len and (char.isalnum() or char in " _-"):
            self.buffer += char

    def backspace(self):
        self.buffer = self.buffer[:-1]

    def draw(self, screen, title, subtitle=None):
        screen.fill((10, 10, 22))
        draw_text(screen, title, 36, s.UI_TEXT, (s.SCREEN_W // 2, 140), bold=True)
        if subtitle:
            draw_text(screen, subtitle, 16, s.UI_DIM, (s.SCREEN_W // 2, 175))

        box = pygame.Rect(0, 0, 420, 54)
        box.center = (s.SCREEN_W // 2, 260)
        pygame.draw.rect(screen, s.UI_PANEL, box, border_radius=8)
        pygame.draw.rect(screen, s.UI_ACCENT, box, width=2, border_radius=8)
        cursor = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        draw_text(screen, self.buffer + cursor, 26, s.UI_TEXT, box.center)
        draw_text(screen, "Enter to confirm, Esc to cancel", 15, s.UI_DIM, (s.SCREEN_W // 2, 320))


def draw_profile_select(screen, menu):
    screen.fill((10, 10, 22))
    menu.draw(screen, "WHO'S FLYING?", "Up/Down to choose, Enter to confirm, Delete to remove a profile")


def draw_confirm_delete(screen, menu, profile):
    screen.fill((10, 10, 22))
    if profile is None:
        menu.draw(screen, "DELETE PROFILE?")
        return
    completed = sum(1 for e in profile["levels"].values() if e.get("completed"))
    draw_text(screen, "DELETE PROFILE?", 36, s.UI_DANGER, (s.SCREEN_W // 2, 110), bold=True)
    draw_text(screen, f"\"{profile['name']}\"  -  score {profile['cumulative_score']}, {completed} level(s) completed",
              17, s.UI_TEXT, (s.SCREEN_W // 2, 150))
    draw_text(screen, "This permanently deletes the profile and cannot be undone.", 15, s.UI_DANGER, (s.SCREEN_W // 2, 175))
    menu.draw(screen, y_start=230)


def draw_main_menu(screen, menu, profile):
    screen.fill((10, 10, 22))
    menu.draw(screen, "ASTROSURFER", f"Profile: {profile['name']}   Cumulative score: {profile['cumulative_score']}")
    draw_text(screen, "Up/Down to choose, Enter to confirm", 15, s.UI_DIM, (s.SCREEN_W // 2, s.SCREEN_H - 30))


def draw_level_select(screen, menu):
    screen.fill((10, 10, 22))
    menu.draw(screen, "SELECT A RUN", "Up/Down to choose, Enter to fly, Esc to go back")


def draw_overlay_backdrop(screen):
    overlay = pygame.Surface((s.SCREEN_W, s.SCREEN_H), pygame.SRCALPHA)
    overlay.fill((5, 5, 10, 180))
    screen.blit(overlay, (0, 0))


def draw_pause(screen, menu):
    draw_overlay_backdrop(screen)
    menu.draw(screen, "PAUSED")


def draw_no_lives(screen, menu, profile, refill_cost):
    draw_overlay_backdrop(screen)
    draw_text(screen, "OUT OF RETRIES", 40, s.UI_DANGER, (s.SCREEN_W // 2, 110), bold=True)
    draw_text(screen, f"Free retries refill in the next 24h window.  Shards: {profile['currency']}", 17, s.UI_TEXT, (s.SCREEN_W // 2, 150))
    draw_text(screen, f"Refill 3 retries now for {refill_cost} Shards?", 17, s.UI_DIM, (s.SCREEN_W // 2, 175))
    menu.draw(screen, y_start=230)


def draw_game_over(screen, menu, progress_pct, is_new_best, lives, currency):
    draw_overlay_backdrop(screen)
    draw_text(screen, "DESTROYED", 44, s.UI_DANGER, (s.SCREEN_W // 2, 100), bold=True)
    detail = f"Reached {progress_pct:.0f}% of the run"
    if is_new_best:
        detail += "  -  NEW BEST!"
    draw_text(screen, detail, 20, s.UI_TEXT, (s.SCREEN_W // 2, 138))
    draw_text(screen, f"Retries left: {lives}   Shards: {currency}", 16, s.UI_DIM, (s.SCREEN_W // 2, 165))
    menu.draw(screen, y_start=220)


def draw_level_complete(screen, menu, is_new_best, score, lives, currency):
    draw_overlay_backdrop(screen)
    draw_text(screen, "RUN COMPLETE", 40, s.UI_ACCENT, (s.SCREEN_W // 2, 100), bold=True)
    detail = "NEW BEST!" if is_new_best else "Nice flying!"
    draw_text(screen, f"{detail}   Score: {score}", 20, s.UI_TEXT, (s.SCREEN_W // 2, 138))
    draw_text(screen, f"Retries left: {lives}   Shards: {currency}", 16, s.UI_DIM, (s.SCREEN_W // 2, 165))
    menu.draw(screen, y_start=220)


def draw_hud(screen, level, profile):
    pct = level.progress * 100
    draw_text(screen, f"{level.name}   {pct:4.0f}%", 18, s.UI_DIM, (s.SCREEN_W // 2, 22))
    bar_w = 320
    bar_rect = pygame.Rect(0, 0, bar_w, 8)
    bar_rect.midtop = (s.SCREEN_W // 2, 36)
    pygame.draw.rect(screen, s.UI_PANEL, bar_rect, border_radius=4)
    fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, max(1, int(bar_w * level.progress)), 8)
    pygame.draw.rect(screen, level.theme["accent"], fill_rect, border_radius=4)

    draw_text_topleft(screen, f"{profile['name']}", 14, s.UI_DIM, (12, 10))
    draw_text_topleft(screen, f"Total: {profile['cumulative_score']}", 20, s.UI_TEXT, (12, 26), bold=True)

    draw_text_topright(screen, f"Score: {level.score}", 20, s.UI_TEXT, (s.SCREEN_W - 12, 10), bold=True)
    lives_text = f"Retries: {profile['lives']}"
    draw_text_topright(screen, lives_text, 14, s.UI_DIM, (s.SCREEN_W - 12, 34))


# -- tutorial popups -----------------------------------------------------------
TUTORIAL_TEXT = {
    "welcome": ("WELCOME TO ASTROSURFER", "Your hoverboard auto-scrolls forward. Your only job is timing."),
    "jump": ("THRUSTER JUMP", "Press SPACE or UP to fire your thruster and jump over asteroids."),
    "ledge": ("RIDE-UP LEDGES", "Short debris ledges are safe to run straight over - no jump needed."),
    "elevated_ledge": ("ELEVATED PLATFORMS", "Taller platforms float above the path - jump to land on top of them."),
    "boost_orb": ("BOOST ORBS", "Glowing orbs give a huge extra boost - press jump while touching one."),
}


def draw_tutorial_popup(screen, popup_key):
    draw_overlay_backdrop(screen)
    title, body = TUTORIAL_TEXT.get(popup_key, ("", ""))
    panel = pygame.Rect(0, 0, 640, 180)
    panel.center = (s.SCREEN_W // 2, s.SCREEN_H // 2)
    pygame.draw.rect(screen, s.UI_PANEL, panel, border_radius=12)
    pygame.draw.rect(screen, s.UI_ACCENT, panel, width=2, border_radius=12)
    draw_text(screen, title, 26, s.UI_ACCENT, (panel.centerx, panel.top + 45), bold=True)
    draw_text(screen, body, 17, s.UI_TEXT, (panel.centerx, panel.top + 90))
    draw_text(screen, "Press SPACE / ENTER to continue", 14, s.UI_DIM, (panel.centerx, panel.bottom - 28))


# -- "new feature" banner (non-blocking) ----------------------------------------
FEATURE_BANNER_DURATION = 3.5


def draw_feature_banner(screen, text, timer):
    if timer <= 0:
        return
    alpha = int(255 * min(1.0, timer / 0.5)) if timer < 0.5 else 255
    surf = pygame.Surface((s.SCREEN_W, 44), pygame.SRCALPHA)
    surf.fill((*s.UI_PANEL, min(210, alpha)))
    label = get_font(20, bold=True).render(f"NEW: {text}", True, (*s.UI_ACCENT, alpha))
    surf.blit(label, label.get_rect(center=(s.SCREEN_W // 2, 22)))
    screen.blit(surf, (0, 64))


# -- shop -----------------------------------------------------------------------
def draw_shop(screen, menu, profile):
    screen.fill((10, 10, 22))
    menu.draw(
        screen, "COSMETICS SHOP",
        f"Shards: {profile['currency']}   Up/Down choose, Enter buy/equip, Esc back",
        y_start=190, spacing=44,
    )
